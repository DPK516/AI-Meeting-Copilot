from pydantic import BaseModel, Field
from typing import Optional


class MeetingAnalysisRequest(BaseModel):
    source: str = Field(..., description="YouTube URL or local file path")
    language: str = Field(default="english", description="Primary spoken language")

class ChatRequest(BaseModel):
    question: str = Field(..., description="User's question for the RAG engine")


class MeetingAnalysisResponse(BaseModel):
    title: str
    summary: str
    action_items: str
    key_decisions: str
    open_questions: str

class ChatResponse(BaseModel):
    answer: str
