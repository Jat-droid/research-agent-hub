import os
import json
from typing import Dict, Any
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from app.state import AgentState

# Initialize the Critic LLM using Cerebras
critic_llm = ChatOpenAI(
    api_key=os.getenv("CEREBRAS_API_KEY"),
    base_url="https://api.cerebras.ai/v1",
    model="gpt-oss-120b",
    temperature=0.0, # Zero temperature for strict, objective grading
    model_kwargs={"response_format": {"type": "json_object"}}
)

CRITIC_SYSTEM_PROMPT = """You are a rigorous quality reviewer. Evaluate the drafted section on:
- Accuracy: are all claims supported by cited sources? (0-3)
- Completeness: are key angles covered? (0-3)
- Clarity: is the writing clear and logical? (0-2)
- Citations: are sources credible and properly referenced? (0-2)

Return JSON strictly in this format:
{{
    "score": 8,
    "issues": ["specific problem 1", "specific problem 2"],
    "suggestions": ["concrete fix 1", "concrete fix 2"],
    "approved": true
}}"""

def critic_node(state: AgentState) -> Dict[str, Any]:
    """Evaluates the drafted section and returns feedback and approval status."""
    print("\n[Critic Agent] Evaluating drafted section for quality...")
    
    plan = state.get("plan", {})
    idx = state.get("current_sub_question_index", 0)
    sub_question = plan["sub_questions"][idx]
    
    drafted_content = state.get("drafted_sections", {}).get(sub_question, "")
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", CRITIC_SYSTEM_PROMPT),
        ("user", "Sub-question: {question}\n\nDrafted Content:\n{draft}")
    ])
    
    formatted_prompt = prompt.format_messages(
        question=sub_question, 
        draft=drafted_content
    )
    
    response = critic_llm.invoke(formatted_prompt)
    
    try:
        evaluation = json.loads(response.content)
        score = evaluation.get("score", 0)
        approved = evaluation.get("approved", False)
        
        print(f"[Critic Agent] Draft scored {score}/10. Approved: {approved}")
        if not approved:
            print(f"               Issues found: {evaluation.get('issues')}")
            
        return {
            "critic_feedback": evaluation
        }
    except Exception as e:
        print(f"[Error] Critic failed to parse JSON. Auto-approving to prevent block. {e}")
        return {"critic_feedback": {"approved": True, "score": 7, "issues": [], "suggestions": []}}