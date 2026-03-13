"""
关键词管理 API 路由
"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.models import Keyword
from app.schemas.schemas import (
    KeywordCreate, KeywordUpdate, KeywordResponse, MessageResponse
)

router = APIRouter(prefix="/api/keywords", tags=["关键词管理"])


@router.get("", response_model=List[KeywordResponse])
def list_keywords(
    category: str = Query(None, description="按分类过滤"),
    active_only: bool = Query(False, description="只返回激活的关键词"),
    db: Session = Depends(get_db)
):
    """获取关键词列表"""
    query = db.query(Keyword)
    if category:
        query = query.filter(Keyword.category == category)
    if active_only:
        query = query.filter(Keyword.is_active == True)
    return query.order_by(Keyword.created_at.desc()).all()


@router.post("", response_model=KeywordResponse, status_code=201)
def create_keyword(keyword: KeywordCreate, db: Session = Depends(get_db)):
    """添加关键词"""
    existing = db.query(Keyword).filter(Keyword.keyword == keyword.keyword).first()
    if existing:
        raise HTTPException(status_code=400, detail=f"关键词 '{keyword.keyword}' 已存在")

    db_keyword = Keyword(**keyword.model_dump())
    db.add(db_keyword)
    db.commit()
    db.refresh(db_keyword)
    return db_keyword


@router.get("/{keyword_id}", response_model=KeywordResponse)
def get_keyword(keyword_id: int, db: Session = Depends(get_db)):
    """获取单个关键词"""
    kw = db.query(Keyword).filter(Keyword.id == keyword_id).first()
    if not kw:
        raise HTTPException(status_code=404, detail="关键词不存在")
    return kw


@router.put("/{keyword_id}", response_model=KeywordResponse)
def update_keyword(
    keyword_id: int,
    kw_update: KeywordUpdate,
    db: Session = Depends(get_db)
):
    """更新关键词"""
    kw = db.query(Keyword).filter(Keyword.id == keyword_id).first()
    if not kw:
        raise HTTPException(status_code=404, detail="关键词不存在")

    update_data = kw_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(kw, field, value)

    db.commit()
    db.refresh(kw)
    return kw


@router.delete("/{keyword_id}", response_model=MessageResponse)
def delete_keyword(keyword_id: int, db: Session = Depends(get_db)):
    """删除关键词"""
    kw = db.query(Keyword).filter(Keyword.id == keyword_id).first()
    if not kw:
        raise HTTPException(status_code=404, detail="关键词不存在")

    db.delete(kw)
    db.commit()
    return {"message": f"关键词 '{kw.keyword}' 已删除", "success": True}
