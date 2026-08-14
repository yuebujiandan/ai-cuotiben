"""AI 对话路由：会话管理 + 硅基流动流式回答（SSE）。

安全与限额（PRD §5.8 GAP-7）：
- 内容安全：输入/输出双端敏感词过滤，命中返回固定提示不生成内容
- 每日限额：免费用户 50 次/天，超限返回 403 提示
"""
import logging
from datetime import date

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from database import get_db
from models import Conversation, DailyUsage, Message
from schemas import ChatRequest, ConversationOut, ExplainOut, ExplainRequest, MessageOut
from services import llm_service, safety, vector_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/chat", tags=["chat"])

DAILY_CHAT_LIMIT = 50


def _quota_row(db: Session, day: str, kind: str = "chat") -> DailyUsage:
    row = db.query(DailyUsage).filter_by(day=day, kind=kind).first()
    if row is None:
        row = DailyUsage(day=day, kind=kind, count=0)
        db.add(row)
        db.flush()
    return row


def _check_quota(db: Session) -> None:
    """超额抛 403；未超额不做计数（计数在流成功结束时 +1）。"""
    row = _quota_row(db, date.today().isoformat())
    if row.count >= DAILY_CHAT_LIMIT:
        raise HTTPException(403, "今日提问次数已用完，明日再来")


def _inc_quota(db: Session) -> None:
    row = _quota_row(db, date.today().isoformat())
    row.count += 1
    db.commit()


@router.get("/conversations", response_model=list[ConversationOut])
def list_conversations(db: Session = Depends(get_db)):
    return db.query(Conversation).order_by(Conversation.created_at.desc()).all()


@router.get("/conversations/{cid}/messages", response_model=list[MessageOut])
def history(cid: int, db: Session = Depends(get_db)):
    conv = db.get(Conversation, cid)
    if not conv:
        raise HTTPException(404, "会话不存在")
    return db.query(Message).filter(Message.conversation_id == cid).order_by(Message.id).all()


@router.post("/stream")
async def chat_stream(req: ChatRequest, db: Session = Depends(get_db)):
    """硅基流动流式回复，SSE 文本流。附带向量检索同类题作上下文。

    会话隔离：传入 conversation_id 则复用该会话，否则新建会话。
    会话 ID 通过响应头 X-Conversation-Id 回传，便于前端定位新会话。
    """
    # 0) 安全与限额：输入敏感词拦截 / 每日 50 次限额
    if safety.check(req.question):
        raise HTTPException(403, safety.filtered_message())
    _check_quota(db)

    # 1) 确定会话：指定则复用，未指定则新建
    if req.conversation_id is not None:
        conv = db.get(Conversation, req.conversation_id)
        if not conv:
            raise HTTPException(404, "会话不存在")
    else:
        conv = Conversation(title=req.question[:18] or "新对话")
        db.add(conv)
        db.flush()
    conv_id = conv.id

    # 2) 取本会话已有的最近 10 条消息作为历史
    rows = (
        db.query(Message)
        .filter(Message.conversation_id == conv_id)
        .order_by(Message.id.desc())
        .limit(10)
        .all()
    )
    chat_history = [(m.role, m.content) for m in reversed(rows)]

    # 3) 先持久化用户消息
    db.add(Message(conversation_id=conv_id, role="user", content=req.question))
    db.commit()

    # 4) 向量检索同类题，增强 RAG 上下文
    similar = vector_service.search(req.question, k=2)
    similar_text = "；".join(s["content"] for s in similar) if similar else ""
    rag_context = (
        f"相关错题参考：{similar_text}\n" if similar_text else ""
    ) + req.context

    def gen():
        content = []
        for delta in llm_service.chat_stream(req.question, rag_context, chat_history):
            content.append(delta)
            # 输出端安全：累积文本命中敏感词 → 中断并替换为固定提示
            if safety.check("".join(content)):
                yield safety.filtered_message()
                return
            yield delta
        # 流结束后落库助手回复
        try:
            _persist_assistant(db, conv_id, "".join(content))
            _inc_quota(db)
            print(f"[chat] 对话完成并计次：conv={conv_id} 字数={len(content)}", flush=True)
        except Exception as e:
            print(f"[chat] 流后处理失败 conv={conv_id}: {e}", flush=True)

    return StreamingResponse(
        gen(),
        media_type="text/plain; charset=utf-8",
        headers={"X-Conversation-Id": str(conv_id)},
    )


@router.post("/explain", response_model=ExplainOut)
def explain(req: ExplainRequest, db: Session = Depends(get_db)):
    """3 级讲解：提示(hint) / 思路(approach) / 详解(solution)，各级内容 ≥50 字。"""
    if safety.check(req.question):
        raise HTTPException(403, safety.filtered_message())
    content = llm_service.explain(req.question, req.level)
    return ExplainOut(level=req.level, content=content)


def _persist_assistant(db: Session, conv_id: int, ai_text: str):
    """将助手回复落库到指定会话。"""
    db.add(Message(conversation_id=conv_id, role="assistant", content=ai_text))
    db.commit()
