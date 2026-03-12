"""
监控用户 API 路由
"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.models import MonitoredUser
from app.schemas.schemas import (
    MonitoredUserCreate, MonitoredUserUpdate, MonitoredUserResponse, MessageResponse
)

router = APIRouter(prefix="/api/users", tags=["用户监控"])


@router.get("", response_model=List[MonitoredUserResponse])
def list_users(
    platform: str = Query(None, description="按平台过滤"),
    active_only: bool = Query(False, description="只返回激活的用户"),
    db: Session = Depends(get_db)
):
    """获取监控用户列表"""
    query = db.query(MonitoredUser)
    if platform:
        query = query.filter(MonitoredUser.platform == platform)
    if active_only:
        query = query.filter(MonitoredUser.is_active == True)
    return query.order_by(MonitoredUser.created_at.desc()).all()


@router.post("", response_model=MonitoredUserResponse, status_code=201)
def create_user(user: MonitoredUserCreate, db: Session = Depends(get_db)):
    """添加监控用户"""
    # 检查是否已存在相同平台+用户名
    existing = db.query(MonitoredUser).filter(
        MonitoredUser.platform == user.platform,
        MonitoredUser.username == user.username
    ).first()
    if existing:
        raise HTTPException(
            status_code=400,
            detail=f"用户 {user.platform}/{user.username} 已在监控列表中"
        )

    db_user = MonitoredUser(**user.model_dump())
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


@router.get("/{user_id}", response_model=MonitoredUserResponse)
def get_user(user_id: int, db: Session = Depends(get_db)):
    """获取单个监控用户详情"""
    user = db.query(MonitoredUser).filter(MonitoredUser.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    return user


@router.put("/{user_id}", response_model=MonitoredUserResponse)
def update_user(
    user_id: int,
    user_update: MonitoredUserUpdate,
    db: Session = Depends(get_db)
):
    """更新监控用户信息"""
    user = db.query(MonitoredUser).filter(MonitoredUser.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    update_data = user_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(user, field, value)

    db.commit()
    db.refresh(user)
    return user


@router.delete("/{user_id}", response_model=MessageResponse)
def delete_user(user_id: int, db: Session = Depends(get_db)):
    """删除监控用户"""
    user = db.query(MonitoredUser).filter(MonitoredUser.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    db.delete(user)
    db.commit()
    return {"message": f"用户 {user.platform}/{user.username} 已从监控列表删除", "success": True}
