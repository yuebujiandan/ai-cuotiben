"""复习路由：SM-2 简化调度（答对×2.5 / 答错重置 / 连续2次答对→已掌握）+ 真实作答记录。"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from database import get_db
from models import Question, ReviewRecord
from schemas import QuestionOut

router = APIRouter(prefix="/review", tags=["review"])

DAILY_QUEUE_LIMIT = 30


class ReviewResult(BaseModel):
    result: str = Field(pattern="^(correct|wrong|skip)$")  # 对/错/跳过


@router.get("/queue", response_model=list[QuestionOut])
def review_queue(db: Session = Depends(get_db)):
    """今日复习队列：未掌握(red)优先 → 待复习(amber)，复习次数少的优先，上限 30。"""
    qs = (
        db.query(Question)
        .filter(Question.status.in_(["red", "amber"]))
        .order_by(Question.review_count.asc(), Question.created_at.asc())
        .limit(DAILY_QUEUE_LIMIT)
        .all()
    )
    return qs


@router.post("/{qid}/result", response_model=QuestionOut)
def submit_result(qid: int, data: ReviewResult, db: Session = Depends(get_db)):
    """提交作答结果，更新 SM-2 状态并记录真实复习数据（看板口径来源）。

    - correct：复习次数+1，连续答对+1；连续答对 ≥2 → 已掌握(green)，否则待复习(amber)
    - wrong：复习次数+1，连续答对清零，状态回未掌握(red)
    - skip：仅记录，状态不变
    """
    q = db.get(Question, qid)
    if not q:
        raise HTTPException(404, "错题不存在")

    db.add(ReviewRecord(question_id=qid, result=data.result))

    if data.result == "correct":
        q.review_count += 1
        q.correct_streak += 1
        q.status = "green" if q.correct_streak >= 2 else "amber"
    elif data.result == "wrong":
        q.review_count += 1
        q.correct_streak = 0
        q.status = "red"
    # skip：不改变状态

    db.commit()
    db.refresh(q)
    return q
