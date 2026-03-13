"""
仪表盘 API 路由 - 概览统计数据
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from datetime import datetime, timedelta

from app.database import get_db
from app.schemas.schemas import DashboardData

router = APIRouter(prefix="/api/dashboard", tags=["仪表盘"])


@router.get("", response_model=DashboardData)
def get_dashboard(db: Session = Depends(get_db)):
    """获取仪表盘概览数据"""
    from app.models.models import (
        WatchStock, MonitoredUser, Keyword,
        NewsArticle, PushHistory, SentimentReport
    )

    # 统计基础数据
    total_stocks = db.query(WatchStock).count()
    total_users = db.query(MonitoredUser).count()
    total_keywords = db.query(Keyword).count()
    total_news = db.query(NewsArticle).count()

    # 最近7天推送成功数
    week_ago = datetime.utcnow() - timedelta(days=7)
    recent_push_count = db.query(PushHistory).filter(
        PushHistory.pushed_at >= week_ago,
        PushHistory.status == "success"
    ).count()

    # 推送成功率
    total_push = db.query(PushHistory).filter(PushHistory.pushed_at >= week_ago).count()
    push_success_rate = (recent_push_count / total_push * 100) if total_push > 0 else 0.0

    # 最新情感报告
    latest_sentiment_obj = (
        db.query(SentimentReport)
        .order_by(SentimentReport.created_at.desc())
        .first()
    )
    latest_sentiment = None
    if latest_sentiment_obj:
        latest_sentiment = {
            "conclusion": latest_sentiment_obj.conclusion,
            "overall_score": latest_sentiment_obj.overall_score,
            "positive_count": latest_sentiment_obj.positive_count,
            "negative_count": latest_sentiment_obj.negative_count,
            "neutral_count": latest_sentiment_obj.neutral_count,
            "created_at": latest_sentiment_obj.created_at.isoformat(),
        }

    # 最近5条新闻
    recent_news_objs = (
        db.query(NewsArticle)
        .order_by(NewsArticle.created_at.desc())
        .limit(5)
        .all()
    )
    recent_news = [
        {
            "id": n.id,
            "title": n.title,
            "source": n.source,
            "url": n.url,
            "sentiment_label": n.sentiment_label,
            "published_at": n.published_at.isoformat() if n.published_at else None,
        }
        for n in recent_news_objs
    ]

    return DashboardData(
        total_stocks=total_stocks,
        total_users=total_users,
        total_keywords=total_keywords,
        total_news=total_news,
        recent_push_count=recent_push_count,
        latest_sentiment=latest_sentiment,
        recent_news=recent_news,
        push_success_rate=round(push_success_rate, 1),
    )
