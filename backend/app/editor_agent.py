import os
from typing import Dict, Any

# 1. Remove langchain_groq and import ChatOpenAI
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from app.state import AgentState

# 2. Replace ChatGroq with ChatOpenAI targeting Cerebras
editor_llm = ChatOpenAI(
    api_key=os.getenv("CEREBRAS_API_KEY"),
    base_url="https://api.cerebras.ai/v1",
    model="gpt-oss-120b",
    temperature=0.3, # Slightly higher temperature for better narrative flow
)

EDITOR_SYSTEM_PROMPT = """You are an elite Editor-in-Chief. 
Your job is to take a research topic, a planned structure, and a collection of drafted sections, and compile them into a cohesive, professional Markdown report.

CRITICAL INSTRUCTIONS:
1. Format the report using proper Markdown (H1 for the main title, H2/H3 for sections).
2. Ensure smooth, logical transitions between the drafted sections.
3. Preserve ALL inline citations (e.g., [Source: URL]) exactly as they appear in the drafts.
4. Add a brief, engaging Executive Summary at the beginning and a solid Conclusion at the end.
5. Do NOT hallucinate new factual data. Rely strictly on the provided drafts.

Respond ONLY with the final Markdown text. Do not include conversational filler."""

def editor_node(state: AgentState) -> Dict[str, Any]:
    """Compiles all drafted sections into a final markdown report."""
    print("\n[Editor Agent] Stitching drafts into the final Markdown report...")
    
    topic = state.get("topic", "Unknown Topic")
    plan = state.get("plan", {})
    drafts = state.get("drafted_sections", {})
    
    # Format the drafts into a readable string for the LLM
    drafts_text = ""
    for question, content in drafts.items():
        drafts_text += f"### Sub-Question: {question}\n{content}\n\n"
        
    prompt = ChatPromptTemplate.from_messages([
        ("system", EDITOR_SYSTEM_PROMPT),
        ("user", "Topic: {topic}\n\nExpected Structure: {plan}\n\nDrafted Content:\n{drafts}")
    ])
    
    formatted_prompt = prompt.format_messages(
        topic=topic,
        plan=plan.get("expected_sections", []),
        drafts=drafts_text
    )
    
    response = editor_llm.invoke(formatted_prompt)
    final_markdown = response.content
    
    print("[Editor Agent] Final report generated successfully!")
    
    return {
        "final_report": final_markdown
    }