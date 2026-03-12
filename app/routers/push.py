"""
推送 API 路由 - 手动触发推送、查看推送历史
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, Query, BackgroundTasks
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.models import PushHistory
from app.schemas.schemas import PushHistoryResponse, ManualPushRequest, MessageResponse

router = APIRouter(prefix="/api/push", tags=["推送管理"])


@router.get("/history", response_model=List[PushHistoryResponse])
def list_push_history(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: Optional[str] = Query(None, description="按状态过滤: success/failed/pending"),
    db: Session = Depends(get_db)
):
    """获取推送历史记录"""
    query = db.query(PushHistory)
    if status:
        query = query.filter(PushHistory.status == status)

    return (
        query
        .order_by(PushHistory.pushed_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )


@router.post("/trigger", response_model=MessageResponse)
def trigger_push(
    request: ManualPushRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """手动触发推送任务"""
    from app.services.scheduler import run_daily_pipeline
    from app.services.lark_notifier import send_text_message
    from app.models.models import PushHistory

    if request.custom_message:
        # 发送自定义消息
        def send_custom():
            from app.config import settings
            urls = settings.get_lark_webhook_list()
            responses = []
            for url in urls:
                resp = send_text_message(request.custom_message, webhook_url=url)
                responses.append(resp)

            status = "success" if any(
                r.get("code") == 0 or r.get("StatusCode") == 0
                for r in responses
            ) else "failed"

            history = PushHistory(
                push_type="manual",
                title="手动推送",
                content=request.custom_message[:200],
                status=status,
                lark_response=responses[0] if responses else None,
            )
            db.add(history)
            db.commit()
            db.close()

        background_tasks.add_task(send_custom)
        return {"message": "自定义消息推送任务已启动", "success": True}
    else:
        # 执行完整每日报告推送
        background_tasks.add_task(run_daily_pipeline)
        return {"message": "每日报告推送任务已启动（后台执行）", "success": True}


@router.get("/status", response_model=dict)
def get_scheduler_status():
    """获取定时调度器状态"""
    from app.services.scheduler import get_scheduler_status
    return get_scheduler_status()
