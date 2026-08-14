"""数据看板路由：统计指标 + 近十天趋势 + PDF 导出。

统计口径（PRD §5.6 指标口径）：
- 今日复习数 / 连续打卡 / 每日正确数：全部来自 review_records 真实作答记录
- 掌握率 = 已掌握错题数 ÷ 有效错题总数 × 100%
"""
from datetime import date, timedelta

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from sqlalchemy import func
from sqlalchemy.orm import Session

from database import get_db
from models import Question, ReviewRecord
from schemas import DailyStat, DashboardStats
from services import pdf_service

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


def _count_reviews(db: Session, start, end, result: str | None = None) -> int:
    q = db.query(func.count(ReviewRecord.id)).filter(
        ReviewRecord.created_at >= start, ReviewRecord.created_at < end
    )
    if result:
        q = q.filter(ReviewRecord.result == result)
    return q.scalar() or 0


def _streak_days(db: Session) -> int:
    """连续打卡天数：从今天往前，连续每天都有复习记录。"""
    streak = 0
    day = date.today()
    while True:
        start = datetime_combine(day)
        end = start + timedelta(days=1)
        if _count_reviews(db, start, end) > 0:
            streak += 1
            day -= timedelta(days=1)
        else:
            break
    return streak


@router.get("/stats", response_model=DashboardStats)
def stats(db: Session = Depends(get_db)):
    total = db.query(func.count(Question.id)).scalar() or 0
    mastered = (
        db.query(func.count(Question.id)).filter(Question.status == "green").scalar() or 0
    )
    reviewing = (
        db.query(func.count(Question.id)).filter(Question.status == "amber").scalar() or 0
    )
    pending = (
        db.query(func.count(Question.id)).filter(Question.status == "red").scalar() or 0
    )
    mastery_rate = round(mastered / total * 100) if total else 0
    today_start = datetime_combine(date.today())
    review_today = _count_reviews(db, today_start, today_start + timedelta(days=1))
    return DashboardStats(
        total=total,
        mastered=mastered,
        reviewing=reviewing,
        pending=pending,
        mastery_rate=mastery_rate,
        review_today=review_today,
        streak_days=_streak_days(db),
    )


@router.get("/daily", response_model=list[DailyStat])
def daily(db: Session = Depends(get_db)):
    """近十天：新增错题数 / 复习次数 / 复习正确数（真实口径）。"""
    rows: list[DailyStat] = []
    today = date.today()
    for i in range(9, -1, -1):
        day = today - timedelta(days=i)
        start = datetime_combine(day)
        end = start + timedelta(days=1)
        total = (
            db.query(func.count(Question.id))
            .filter(Question.created_at >= start, Question.created_at < end)
            .scalar()
            or 0
        )
        review = _count_reviews(db, start, end)
        correct = _count_reviews(db, start, end, result="correct")
        rows.append(DailyStat(date=day.isoformat(), total=total, correct=correct, review=review))
    return rows


@router.get("/export")
def export_pdf(
    subject: str | None = None,
    status: str | None = None,
    keyword: str | None = None,
    notebook_id: int | None = None,
    db: Session = Depends(get_db),
):
    """导出错题本 PDF（ReportLab 生成）。支持按当前筛选条件导出。"""
    query = db.query(Question)
    if subject:
        query = query.filter(Question.subject == subject)
    if status:
        query = query.filter(Question.status == status)
    if keyword:
        like = f"%{keyword}%"
        query = query.filter(
            (Question.content.like(like))
            | (Question.knowledge_point.like(like))
            | (Question.subject.like(like))
        )
    if notebook_id is not None:
        query = query.filter(Question.notebook_id == notebook_id)
    questions = query.order_by(Question.created_at.desc()).all()
    if not questions:
        raise HTTPException(404, "暂无错题可导出")
    data = pdf_service.export_pdf(questions)
    filename = f"recall-{date.today().isoformat()}.pdf"
    return Response(
        content=data,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


def datetime_combine(day: date):
    from datetime import datetime

    return datetime.combine(day, datetime.min.time())
