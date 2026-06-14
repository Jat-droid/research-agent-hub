import os
from typing import Dict, Any
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from app.state import AgentState

writer_llm = ChatOpenAI(
    api_key=os.getenv("CEREBRAS_API_KEY"),
    base_url="https://api.cerebras.ai/v1",
    model="gpt-oss-120b",
    temperature=0.2, 
)

WRITER_SYSTEM_PROMPT = """You are an expert research analyst and writer. 
Given the retrieved context chunks and a specific sub-question:
1. Synthesise information from multiple sources into clear, analytical prose.
2. Write 200-300 words for this section in an objective, professional tone.
3. Support every factual claim with an inline citation using the exact URL provided in the context [Source: URL].
4. Highlight conflicting information between sources explicitly.
5. Flag knowledge gaps with [GAP: description] where evidence is thin.

Do not pad. Be precise. Never fabricate facts not found in the provided context."""

# NEW: Instructions for when the Writer is forced to rewrite
REVISION_PROMPT = """
You previously wrote a draft for this section, but it was rejected by the Quality Assurance Critic.
Please rewrite the section, incorporating the following mandatory feedback:

CRITIC ISSUES: {issues}
CRITIC SUGGESTIONS: {suggestions}
"""

def writer_node(state: AgentState) -> Dict[str, Any]:
    print("\n[Writer Agent] Drafting section based on retrieved context...")
    
    plan = state.get("plan", {})
    idx = state.get("current_sub_question_index", 0)
    sub_question = plan["sub_questions"][idx]
    context_chunks = state.get("current_context", [])
    
    # NEW: Check if this is a rewrite iteration
    feedback = state.get("critic_feedback", {})
    is_revision = state.get("revision_count", 0) > 0
    
    formatted_context = ""
    if not context_chunks:
        formatted_context = "No relevant information found."
    else:
        for i, chunk in enumerate(context_chunks):
            formatted_context += f"--- Chunk {i+1} ---\n{chunk}\n\n"
            
    # NEW: Adjust prompt if this is a revision
    user_message = "Sub-question: {question}\n\nRetrieved Context:\n{context}"
    if is_revision and not feedback.get("approved", True):
        print(f"[Writer Agent] Applying Critic Feedback. Revision #{state['revision_count']}")
        revision_addon = REVISION_PROMPT.format(
            issues=feedback.get("issues", []), 
            suggestions=feedback.get("suggestions", [])
        )
        user_message += revision_addon
            
    prompt = ChatPromptTemplate.from_messages([
        ("system", WRITER_SYSTEM_PROMPT),
        ("user", user_message)
    ])
    
    formatted_prompt = prompt.format_messages(question=sub_question, context=formatted_context)
    response = writer_llm.invoke(formatted_prompt)
    drafted_content = response.content
    
    current_drafts = state.get("drafted_sections", {})
    current_drafts[sub_question] = drafted_content
    
    print(f"[Writer Agent] Successfully drafted {len(drafted_content.split())} words.")
    
    return {"drafted_sections": current_drafts}