"""Pydantic 请求/响应模型。"""
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator


class QuestionCreate(BaseModel):
    content: str = Field(min_length=1, description="题目内容，不能为空")
    my_answer: str | None = None
    subject: str | None = None
    knowledge_point: str | None = None
    notebook_id: int | None = None
    source: str | None = None

    @field_validator("content")
    @classmethod
    def _content_not_blank(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("题目内容不能为空")
        return v


class OcrPreviewOut(BaseModel):
    text: str
    source: str
    questions: list[str] = Field(default_factory=list, description="按「第N题」拆分的片段（如仅 1 题则等于 [text]）")


class QuestionUpdate(BaseModel):
    subject: str | None = None
    knowledge_point: str | None = None
    source: str | None = None
    content: str | None = None
    my_answer: str | None = None
    correct_answer: str | None = None
    ai_analysis: str | None = None
    status: str | None = None
    is_favorite: bool | None = None
    notebook_id: int | None = None


class QuestionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    subject: str
    knowledge_point: str
    source: str
    content: str
    my_answer: str | None
    correct_answer: str | None
    ai_analysis: str | None
    status: str
    review_count: int
    is_favorite: bool
    notebook_id: int | None = None
    created_at: datetime


class ChatRequest(BaseModel):
    question: str
    context: str = ""
    conversation_id: int | None = None


class ExplainRequest(BaseModel):
    question: str = Field(min_length=1)
    level: str = Field(pattern="^(hint|approach|solution)$")  # 提示/思路/详解


class ExplainOut(BaseModel):
    level: str
    content: str


class MessageOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    role: str
    content: str


class ConversationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    created_at: datetime


class NotebookCreate(BaseModel):
    name: str


class NotebookOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    created_at: datetime
    count: int = 0


class CategoryOut(BaseModel):
    name: str
    count: int


class DashboardStats(BaseModel):
    total: int
    mastered: int
    reviewing: int
    pending: int
    mastery_rate: int
    review_today: int
    streak_days: int = 0


class DailyStat(BaseModel):
    date: str
    total: int
    correct: int
    review: int = 0
