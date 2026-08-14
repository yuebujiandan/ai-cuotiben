"""错题 CRUD / 上传识别 / AI 归类路由。"""
import logging
import uuid

from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy import func
from sqlalchemy.orm import Session

import services.vector_service as vector
from database import get_db
from models import Notebook, Question, ReviewRecord
from schemas import CategoryOut, OcrPreviewOut, QuestionCreate, QuestionOut, QuestionUpdate
from services import llm_service, ocr_service
from services.ocr_service import OcrError

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/questions", tags=["questions"])

_UPLOAD_DIR = "./uploads"
_ALLOWED_EXT = {".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp", ".heic"}


def _check_notebook(db: Session, notebook_id: int | None):
    """校验错题本存在，避免悬空外键。"""
    if notebook_id is not None:
        nb = db.get(Notebook, notebook_id)
        if not nb:
            raise HTTPException(400, "错题本不存在")


def _save_upload(file: UploadFile) -> str:
    """校验扩展名并落盘，返回文件路径。非图片直接 400。"""
    import os

    ext = "." + (file.filename.split(".")[-1].lower() if "." in file.filename else "")
    if ext not in _ALLOWED_EXT:
        raise HTTPException(400, f"不支持的文件类型 {ext or '(无扩展名)'}，仅支持图片")
    os.makedirs(_UPLOAD_DIR, exist_ok=True)
    path = os.path.join(_UPLOAD_DIR, f"{uuid.uuid4().hex}{ext}")
    with open(path, "wb") as f:
        f.write(file.file.read())
    return path


@router.get("", response_model=list[QuestionOut])
def list_questions(
    category: str | None = None,
    status: str | None = None,
    keyword: str | None = None,
    notebook_id: int | None = None,
    db: Session = Depends(get_db),
):
    query = db.query(Question)
    if notebook_id is not None:
        query = query.filter(Question.notebook_id == notebook_id)
    if category and category not in ("all", "收藏夹", "复习计划"):
        query = query.filter(Question.subject == category)
    if category == "收藏夹":
        query = query.filter(Question.is_favorite.is_(True))
    if category == "复习计划":
        query = query.filter(Question.review_count > 0)
    if status:
        query = query.filter(Question.status == status)
    if keyword:
        like = f"%{keyword}%"
        query = query.filter(
            (Question.content.like(like))
            | (Question.knowledge_point.like(like))
            | (Question.subject.like(like))
            | (Question.source.like(like))
        )
    return query.order_by(Question.created_at.desc()).all()


@router.get("/categories", response_model=list[CategoryOut])
def categories(db: Session = Depends(get_db)):
    rows = (
        db.query(Question.subject, func.count(Question.id))
        .group_by(Question.subject)
        .all()
    )
    total = db.query(func.count(Question.id)).scalar() or 0
    fav = db.query(func.count(Question.id)).filter(Question.is_favorite.is_(True)).scalar() or 0
    plan = db.query(func.count(Question.id)).filter(Question.review_count > 0).scalar() or 0
    result = [CategoryOut(name="all", count=total)]
    result += [CategoryOut(name=s, count=c) for s, c in rows]
    result.append(CategoryOut(name="收藏夹", count=fav))
    result.append(CategoryOut(name="复习计划", count=plan))
    return result


@router.get("/{qid}", response_model=QuestionOut)
def get_question(qid: int, db: Session = Depends(get_db)):
    q = db.get(Question, qid)
    if not q:
        raise HTTPException(404, "错题不存在")
    return q


# 共享占位文本与失败提示常量，便于轮询判断与失败回写
AI_PENDING_PLACEHOLDER = "AI 解析中…（约 1-2 分钟，请稍后刷新查看）"
AI_FAILED_PLACEHOLDER = "AI 解析失败（超时或服务不可用），请点击「重新 AI 分析」重试"


def _run_ai_analysis(qid: int, content: str, my_answer: str | None):
    """后台线程执行 AI 解析，完成后更新数据库（同步向量索引）。
    任何异常都会被捕获并把占位文本改为失败提示，避免前端轮询永远卡住。
    """
    from database import SessionLocal

    try:
        analysis = llm_service.analyze_question(content, my_answer) or {}
    except Exception as e:
        logger.warning("后台 AI 解析失败（网络/服务）：#%s %s", qid, e)
        analysis = {}  # 不抛异常，进入下方"回写失败占位"路径

    db = SessionLocal()
    try:
        q = db.get(Question, qid)
        if not q:
            return
        if analysis.get("subject"):
            q.subject = analysis["subject"]
        if analysis.get("knowledge_point"):
            q.knowledge_point = analysis["knowledge_point"]
        if analysis.get("correct_answer"):
            q.correct_answer = analysis["correct_answer"]
        if analysis.get("analysis"):
            q.ai_analysis = analysis["analysis"]
        else:
            # 无有效结果 → 把占位文本改为失败提示，让前端停止轮询
            q.ai_analysis = AI_FAILED_PLACEHOLDER
        db.commit()
        if analysis.get("analysis"):  # 真正成功才做向量索引
            try:
                vector.upsert(qid, q.content, q.subject, q.knowledge_point)
            except Exception as e:
                logger.warning("向量索引更新失败（不影响保存）：#%s %s", qid, e)
    except Exception as e:
        logger.error("后台 AI 解析写库失败：#%s %s", qid, e)
        try:
            # 即便异常也要把占位文本改成失败提示，避免前端永远轮询
            db.rollback()
            q2 = db.get(Question, qid)
            if q2 and (q2.ai_analysis or "").strip() == AI_PENDING_PLACEHOLDER:
                q2.ai_analysis = AI_FAILED_PLACEHOLDER
                db.commit()
        except Exception:
            pass
    finally:
        db.close()


@router.post("", response_model=QuestionOut)
def create_question(
    data: QuestionCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """创建错题：立即入库并返回（秒级），AI 解析在后台线程异步完成。
    前端列表刷新后可见 AI 归类结果；未完成时显示「AI 解析中…」。
    """
    _check_notebook(db, data.notebook_id)
    q = Question(
        content=data.content,
        my_answer=data.my_answer,
        subject=data.subject or "数学",
        knowledge_point="",
        ai_analysis=AI_PENDING_PLACEHOLDER,
        source=data.source or "",
        status="red",
        notebook_id=data.notebook_id,
    )
    db.add(q)
    db.commit()
    db.refresh(q)
    # 后台异步执行 AI 解析，不阻塞接口返回
    background_tasks.add_task(_run_ai_analysis, q.id, q.content, q.my_answer)
    return q


@router.post("/upload", response_model=QuestionOut)
async def upload_image(
    file: UploadFile = File(...),
    notebook_id: int | None = Form(None),
    background_tasks: BackgroundTasks = BackgroundTasks(),
    db: Session = Depends(get_db),
):
    """上传错题图片 → DeepSeek-OCR 识别 → 入库（一步完成，AI 解析后台异步）。
    OCR 失败返回 502 且不入库（不产生污染数据）。
    """
    _check_notebook(db, notebook_id)
    path = _save_upload(file)
    try:
        text = ocr_service.ocr_image(path)
    except OcrError as e:
        raise HTTPException(502, str(e))
    if not text.strip():
        raise HTTPException(502, "OCR 未识别到有效文字，请换更清晰的图片或改用手动输入")
    q = Question(
        content=text,
        subject="数学",
        knowledge_point="",
        ai_analysis=AI_PENDING_PLACEHOLDER,
        source=file.filename,
        status="red",
        notebook_id=notebook_id,
    )
    db.add(q)
    db.commit()
    db.refresh(q)
    background_tasks.add_task(_run_ai_analysis, q.id, q.content, q.my_answer)
    return q


@router.post("/upload/ocr", response_model=OcrPreviewOut)
async def upload_ocr(file: UploadFile = File(...)):
    """仅做 OCR 识别，不入库。返回识别文本供前端预览/编辑后再确认入库。
    自动按「第N题」标题拆分多题，前端可逐题入库。
    """
    path = _save_upload(file)
    try:
        text = ocr_service.ocr_image(path)
    except OcrError as e:
        raise HTTPException(502, str(e))
    if not text.strip():
        raise HTTPException(502, "OCR 未识别到有效文字，请换更清晰的图片或改用手动输入")
    questions = _split_questions(text)
    return OcrPreviewOut(text=text, source=file.filename, questions=questions)


def _split_questions(text: str) -> list[str]:
    """按「第N题/第N小题」标题切分多题。无匹配返回整段单题列表。"""
    import re
    # 匹配「第1题」「第 2 题」「(第3题)」「第10小题」等，标题作为分隔点
    pattern = re.compile(r"(?:^|\n)\s*(?:\(|（)?\s*第\s*(\d+)\s*题(?:[题小题]|目)?\s*(?:\)|）)?", re.M)
    matches = list(pattern.finditer(text))
    if len(matches) < 2:
        return [text.strip()] if text.strip() else []
    parts: list[str] = []
    for i, m in enumerate(matches):
        start = m.start()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        chunk = text[start:end].strip()
        if chunk:
            parts.append(chunk)
    # 第一个题号之前若有内容（如标题、页眉），附加到第一题
    if matches[0].start() > 0:
        head = text[: matches[0].start()].strip()
        if head and parts:
            parts[0] = head + "\n\n" + parts[0]
        elif head:
            parts.insert(0, head)
    return parts


@router.post("/{qid}/analyze", response_model=QuestionOut)
def analyze(qid: int, db: Session = Depends(get_db)):
    """对已入库错题重新执行 AI 解析（任何异常都把占位文本改为失败提示）。"""
    q = db.get(Question, qid)
    if not q:
        raise HTTPException(404, "错题不存在")
    try:
        analysis = llm_service.analyze_question(q.content, q.my_answer) or {}
    except Exception as e:
        logger.warning("重新 AI 解析失败：#%s %s", qid, e)
        analysis = {}
    if analysis.get("analysis"):
        q.ai_analysis = analysis["analysis"]
    else:
        q.ai_analysis = AI_FAILED_PLACEHOLDER
    if analysis.get("correct_answer"):
        q.correct_answer = analysis["correct_answer"]
    db.commit()
    db.refresh(q)
    return q


@router.put("/{qid}", response_model=QuestionOut)
def update_question(qid: int, data: QuestionUpdate, db: Session = Depends(get_db)):
    q = db.get(Question, qid)
    if not q:
        raise HTTPException(404, "错题不存在")
    if data.notebook_id is not None:
        _check_notebook(db, data.notebook_id)
    if data.status is not None and data.status not in ("red", "amber", "green"):
        raise HTTPException(400, f"非法的状态值：{data.status}（仅支持 red/amber/green）")
    if data.content is not None and not data.content.strip():
        raise HTTPException(400, "题目内容不能为空")
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(q, field, value)
    db.commit()
    db.refresh(q)
    if data.content or data.subject or data.knowledge_point:
        try:
            vector.upsert(q.id, q.content, q.subject, q.knowledge_point)
        except Exception as e:
            logger.warning("向量索引更新失败（不影响保存）：#%s %s", qid, e)
    return q


@router.delete("/{qid}")
def delete_question(qid: int, db: Session = Depends(get_db)):
    q = db.get(Question, qid)
    if not q:
        raise HTTPException(404, "错题不存在")
    # 先删关联复习记录（外键约束），再删题目
    db.query(ReviewRecord).filter(ReviewRecord.question_id == qid).delete()
    db.delete(q)
    db.commit()
    vector.delete(qid)
    return {"ok": True}
