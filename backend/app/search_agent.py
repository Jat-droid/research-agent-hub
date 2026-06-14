import os
import json
from typing import List, Dict, Any
from tavily import TavilyClient

# 1. Remove langchain_groq and import ChatOpenAI
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from app.state import AgentState

# Initialize Tavily and Cerebras Clients
tavily_client = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))

# 2. Replace ChatGroq with ChatOpenAI targeting Cerebras
search_evaluator_llm = ChatOpenAI(
    api_key=os.getenv("CEREBRAS_API_KEY"),
    base_url="https://api.cerebras.ai/v1",
    model="gpt-oss-120b",
    temperature=0.0,  # Zero temperature for deterministic evaluation
    model_kwargs={"response_format": {"type": "json_object"}}
)

EVALUATOR_SYSTEM_PROMPT = """You are a precision credibility evaluator for scientific and technical research papers.
Evaluate the given web search results for relevance to the research sub-question.

You must score each source on 3 criteria (each from 1 to 5):
1. Domain Authority (1-5): Academic papers, official documentation (.gov, .edu, standards bodies), and premier publications (Reuters, Bloomberg, Nature) score 5. General tech blogs score 2-3.
2. Recency (1-5): Published within the last year scores 5. Up to 3 years scores 3. Older than 3 years scores 1.
3. Relevance (1-5): Directly answers or provides hard evidence for the specific sub-question.

CRITICAL RULES:
- Automatically reject (set total score to 0) any source from: Reddit, Quora, personal blogs (Medium/Substack unless authoritative), or content verified older than 3 years.
- Calculate the total score as: domain_authority + recency + relevance.

You MUST respond with a valid JSON object matching this exact format:
{{
    "sources": [
        {{
            "url": "URL of the source",
            "title": "Title of the source",
            "snippet": "Original snippet",
            "scores": {{
                "domain_authority": 5,
                "recency": 4,
                "relevance": 5
            }},
            "total_score": 14,
            "reason": "Brief single-sentence explanation for the score"
        }}
    ]
}}"""

def search_agent_node(state: AgentState) -> Dict[str, Any]:
    """Retrieves the active sub-question, runs optimized web searches, 
    scores credibility, and saves the filtered high-credibility results."""
    
    plan = state["plan"]
    idx = state["current_sub_question_index"]
    
    # Safely get current sub-question
    if idx >= len(plan.get("sub_questions", [])):
        print("[Search Agent] No more sub-questions to process.")
        return {}
        
    sub_question = plan["sub_questions"][idx]
    print(f"\n[Search Agent] Processing sub-question {idx + 1}/{len(plan['sub_questions'])}: '{sub_question}'")
    
    # 1. Execute Tavily search optimized for technical depth
    try:
        search_response = tavily_client.search(
            query=sub_question,
            search_depth="advanced",
            max_results=6  # Fetch slightly more to filter down
        )
        raw_results = search_response.get("results", [])
    except Exception as e:
        print(f"[Error] Tavily API call failed: {e}")
        raw_results = []

    if not raw_results:
        return {"scraped_raw_data": []}

    # 2. Format findings for Groq Evaluation Node
    formatted_sources_input = []
    for res in raw_results:
        formatted_sources_input.append({
            "title": res.get("title"),
            "url": res.get("url"),
            "snippet": res.get("content") or res.get("snippet") # Fallback to snippet if content is missing
        })

    # 3. Call Groq to compute credibility scores
    prompt = ChatPromptTemplate.from_messages([
        ("system", EVALUATOR_SYSTEM_PROMPT),
        ("user", "Evaluate these search results for the sub-question: '{query}'\n\nResults:\n{results_json}")
    ])
    
    formatted_prompt = prompt.format_messages(
        query=sub_question,
        results_json=json.dumps(formatted_sources_input, indent=2)
    )
    
    response = search_evaluator_llm.invoke(formatted_prompt)
    
    try:
        evaluated_data = json.loads(response.content)
        all_sources = evaluated_data.get("sources", [])
        
        # 4. Filter out sources scoring below 8/15
        credible_sources = [s for s in all_sources if s.get("total_score", 0) >= 8]
        
        # Sort descending by total score and take top 3
        credible_sources = sorted(credible_sources, key=lambda x: x.get("total_score", 0), reverse=True)[:3]
        
        print(f"[Search Agent] Found {len(credible_sources)} highly credible sources (Score >= 8/15)")
        for src in credible_sources:
            print(f"  - [{src.get('total_score', 'N/A')}/15] {src.get('url', 'Unknown URL')}")
            
        return {"scraped_raw_data": credible_sources}
        
    except Exception as e:
        print(f"[Error] Failed parsing evaluation response: {e}")
        return {"scraped_raw_data": formatted_sources_input[:3]} # Fallback to first 3 if parsing hits an issue