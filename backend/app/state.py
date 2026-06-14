from typing import List, Dict, Any, TypedDict
from pydantic import BaseModel, Field

class ResearchPlan(BaseModel):
    topic: str = Field(description="The primary umbrella topic of research.")
    sub_questions: List[str] = Field(description="List of 3-5 specific sub-questions to investigate sequentially or in parallel.")
    expected_sections: List[str] = Field(description="The structural chapters or sections of the final report.")

class AgentState(TypedDict):
    topic: str
    plan: Dict[str, Any]  # Stores the parsed ResearchPlan
    current_sub_question_index: int
    search_queries: List[str]
    scraped_raw_data: List[Dict[str, Any]]
    vector_store_status: str
    drafted_sections: Dict[str, str]  # Format: {"Section Title": "Markdown Content"}
    critic_feedback: Dict[str, Any]  # Format: {"approved": bool, "score": int, "feedback": str}
    revision_count: int
    final_report: str