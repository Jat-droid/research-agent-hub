import os
import json
from typing import Dict, Any
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from app.state import AgentState, ResearchPlan

# Initialize the structural reasoning model
planner_llm = ChatOpenAI(
    api_key=os.getenv("CEREBRAS_API_KEY"),
    base_url="https://api.cerebras.ai/v1",
    model="gpt-oss-120b",
    temperature=0.1,
    model_kwargs={"response_format": {"type": "json_object"}}
)

PLANNER_SYSTEM_PROMPT = """You are an expert Research Director. Your job is to take a core topic and produce a comprehensive execution plan.
You must break down the main topic into actionable sub-questions that need targeted web investigation and define the final chapters of the report.

You MUST respond strictly in a valid JSON format matching this schema:
{{
    "topic": "The exact original topic",
    "sub_questions": ["sub-question 1", "sub-question 2", "sub-question 3"],
    "expected_sections": ["Executive Summary", "Section 1 Title", "Section 2 Title", "Conclusion", "Bibliography"]
}}
Ensure your JSON is completely valid and free of conversational prose."""

def planner_node(state: AgentState) -> Dict[str, Any]:
    """Takes user input topic from state, runs it through the planner LLM, and populates the research plan."""
    print(f"\n[Planner Agent] Planning research lifecycle for topic: '{state['topic']}'")
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", PLANNER_SYSTEM_PROMPT),
        ("user", "Generate an in-depth research execution plan for the following topic: {topic}")
    ])
    
    # Format and invoke the chain
    formatted_prompt = prompt.format_messages(topic=state["topic"])
    response = planner_llm.invoke(formatted_prompt)
    
    try:
        # Parse the guaranteed JSON payload
        plan_json = json.loads(response.content)
        
        return {
            "plan": plan_json,
            "current_sub_question_index": 0,
            "drafted_sections": {},
            "revision_count": 0
        }
    except Exception as e:
        print(f"[Error] Planner failed to generate valid JSON: {str(e)}")
        # Fallback basic structure if parsing fails unexpectedly
        return {
            "plan": {
                "topic": state["topic"],
                "sub_questions": [f"Overview of {state['topic']}"],
                "expected_sections": ["Introduction", "Analysis", "Conclusion"]
            },
            "current_sub_question_index": 0,
            "drafted_sections": {},
            "revision_count": 0
        }