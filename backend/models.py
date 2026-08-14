"""SQLAlchemy ORM 数据模型（错题 / 对话）。"""
from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import Base


def now() -> datetime:
    return datetime.now(timezone.utc)


class Question(Base):
    """错题表"""

    __tablename__ = "questions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    subject: Mapped[str] = mapped_column(String(32), default="数学")       # 学科
    knowledge_point: Mapped[str] = mapped_column(String(64), default="")   # 知识点
    source: Mapped[str] = mapped_column(String(64), default="")            # 来源（试卷/练习册）
    content: Mapped[str] = mapped_column(Text)                             # 题目内容
    my_answer: Mapped[str | None] = mapped_column(Text, nullable=True)     # 我的答案
    correct_answer: Mapped[str | None] = mapped_column(Text, nullable=True)  # 正确答案
    ai_analysis: Mapped[str | None] = mapped_column(Text, nullable=True)   # AI 解析/错因诊断
    status: Mapped[str] = mapped_column(String(16), default="red")         # red/amber/green
    review_count: Mapped[int] = mapped_column(Integer, default=0)          # 复习次数
    correct_streak: Mapped[int] = mapped_column(Integer, default=0)        # 连续答对次数（≥2 → mastered）
    is_favorite: Mapped[bool] = mapped_column(default=False)               # 收藏
    notebook_id: Mapped[int | None] = mapped_column(ForeignKey("notebooks.id"), nullable=True)  # 所属错题本
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now)


class Notebook(Base):
    """错题本（容器）：一道错题归属某一个错题本。"""

    __tablename__ = "notebooks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(64))                          # 错题本名称
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now)

    questions: Mapped[list["Question"]] = relationship(
        "Question",
        backref="notebook",
        foreign_keys="Question.notebook_id",
        cascade="save-update, merge",
    )



class Conversation(Base):
    """AI 对话会话表"""

    __tablename__ = "conversations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(64), default="新对话")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now)

    messages: Mapped[list["Message"]] = relationship(
        back_populates="conversation", cascade="all, delete-orphan"
    )


class DailyUsage(Base):
    """AI 调用每日限额统计（按 天+类型 唯一计数）"""

    __tablename__ = "daily_usage"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    day: Mapped[str] = mapped_column(String(10))          # YYYY-MM-DD
    kind: Mapped[str] = mapped_column(String(16))          # chat / analyze
    count: Mapped[int] = mapped_column(Integer, default=0)

    __table_args__ = (__import__("sqlalchemy").UniqueConstraint("day", "kind", name="uq_daily_usage"),)


class ReviewRecord(Base):
    """复习作答记录（真实统计口径来源：今日复习数 / 连续打卡 / 每日正确率）"""

    __tablename__ = "review_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    question_id: Mapped[int] = mapped_column(ForeignKey("questions.id"))
    result: Mapped[str] = mapped_column(String(8))         # correct / wrong / skip
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now)


class Message(Base):
    """对话消息表"""

    __tablename__ = "messages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    conversation_id: Mapped[int] = mapped_column(ForeignKey("conversations.id"))
    role: Mapped[str] = mapped_column(String(16))      # user / assistant
    content: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now)

    conversation: Mapped[Conversation] = relationship(back_populates="messages")
