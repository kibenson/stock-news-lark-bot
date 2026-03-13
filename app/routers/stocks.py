"""
股票关注列表 API 路由
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.models import WatchStock
from app.schemas.schemas import (
    WatchStockCreate, WatchStockUpdate, WatchStockResponse, MessageResponse
)

router = APIRouter(prefix="/api/stocks", tags=["股票关注列表"])


@router.get("", response_model=List[WatchStockResponse])
def list_stocks(
    active_only: bool = Query(False, description="只返回激活的股票"),
    db: Session = Depends(get_db)
):
    """获取关注的股票列表"""
    query = db.query(WatchStock)
    if active_only:
        query = query.filter(WatchStock.is_active == True)
    return query.order_by(WatchStock.created_at.desc()).all()


@router.post("", response_model=WatchStockResponse, status_code=201)
def create_stock(stock: WatchStockCreate, db: Session = Depends(get_db)):
    """添加关注的股票"""
    # 检查是否已存在
    existing = db.query(WatchStock).filter(
        WatchStock.symbol == stock.symbol.upper()
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail=f"股票代码 {stock.symbol} 已在关注列表中")

    db_stock = WatchStock(
        symbol=stock.symbol.upper(),
        name=stock.name,
        market=stock.market,
        notes=stock.notes,
        is_active=stock.is_active,
    )
    db.add(db_stock)
    db.commit()
    db.refresh(db_stock)
    return db_stock


@router.get("/{stock_id}", response_model=WatchStockResponse)
def get_stock(stock_id: int, db: Session = Depends(get_db)):
    """获取单个股票详情"""
    stock = db.query(WatchStock).filter(WatchStock.id == stock_id).first()
    if not stock:
        raise HTTPException(status_code=404, detail="股票不存在")
    return stock


@router.put("/{stock_id}", response_model=WatchStockResponse)
def update_stock(
    stock_id: int,
    stock_update: WatchStockUpdate,
    db: Session = Depends(get_db)
):
    """更新股票信息"""
    stock = db.query(WatchStock).filter(WatchStock.id == stock_id).first()
    if not stock:
        raise HTTPException(status_code=404, detail="股票不存在")

    update_data = stock_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(stock, field, value)

    db.commit()
    db.refresh(stock)
    return stock


@router.delete("/{stock_id}", response_model=MessageResponse)
def delete_stock(stock_id: int, db: Session = Depends(get_db)):
    """删除关注的股票"""
    stock = db.query(WatchStock).filter(WatchStock.id == stock_id).first()
    if not stock:
        raise HTTPException(status_code=404, detail="股票不存在")

    db.delete(stock)
    db.commit()
    return {"message": f"股票 {stock.symbol} 已从关注列表删除", "success": True}
