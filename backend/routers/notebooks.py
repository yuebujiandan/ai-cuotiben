"""错题本（容器）路由：增删查。"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from database import get_db
from models import Notebook, Question
from schemas import NotebookCreate, NotebookOut

router = APIRouter(prefix="/notebooks", tags=["notebooks"])


@router.get("", response_model=list[NotebookOut])
def list_notebooks(db: Session = Depends(get_db)):
    notebooks = db.query(Notebook).order_by(Notebook.created_at.desc()).all()
    result = []
    for nb in notebooks:
        count = (
            db.query(func.count(Question.id))
            .filter(Question.notebook_id == nb.id)
            .scalar()
            or 0
        )
        result.append(
            NotebookOut(id=nb.id, name=nb.name, created_at=nb.created_at, count=count)
        )
    return result


@router.post("", response_model=NotebookOut, status_code=201)
def create_notebook(data: NotebookCreate, db: Session = Depends(get_db)):
    name = (data.name or "").strip()
    if not name:
        raise HTTPException(400, "错题本名称不能为空")
    # 同名不重复创建，直接返回已有本
    existing = db.query(Notebook).filter(Notebook.name == name).first()
    if existing:
        count = (
            db.query(func.count(Question.id))
            .filter(Question.notebook_id == existing.id)
            .scalar()
            or 0
        )
        return NotebookOut(
            id=existing.id, name=existing.name, created_at=existing.created_at, count=count
        )
    nb = Notebook(name=name)
    db.add(nb)
    db.commit()
    db.refresh(nb)
    return NotebookOut(id=nb.id, name=nb.name, created_at=nb.created_at, count=0)


@router.delete("/{nid}")
def delete_notebook(nid: int, db: Session = Depends(get_db)):
    nb = db.get(Notebook, nid)
    if not nb:
        raise HTTPException(404, "错题本不存在")
    # 解除题目归属（不删除题目本身）
    db.query(Question).filter(Question.notebook_id == nid).update(
        {Question.notebook_id: None}
    )
    db.delete(nb)
    db.commit()
    return {"ok": True}
