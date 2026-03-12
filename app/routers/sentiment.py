"""
情感分析 API 路由
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.models import SentimentReport, NewsArticle
from app.schemas.schemas import SentimentReportResponse

router = APIRouter(prefix="/api/sentiment", tags=["情感分析"])


@router.get("", response_model=List[SentimentReportResponse])
def list_sentiment_reports(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    target_type: Optional[str] = Query(None, description="过滤类型: news/user_post/keyword/daily_news"),
    db: Session = Depends(get_db)
):
    """获取情感分析报告列表"""
    query = db.query(SentimentReport)
    if target_type:
        query = query.filter(SentimentReport.target_type == target_type)

    return (
        query
        .order_by(SentimentReport.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )


@router.get("/analyze", response_model=dict)
def analyze_recent_news(
    hours: int = Query(24, ge=1, le=168, description="分析最近N小时的新闻"),
    use_ai: bool = Query(False, description="是否使用AI分析"),
    db: Session = Depends(get_db)
):
    """对最近新闻进行情感分析并生成报告"""
    from datetime import datetime, timedelta
    from app.services.sentiment_analyzer import generate_sentiment_report

    since = datetime.utcnow() - timedelta(hours=hours)
    articles = db.query(NewsArticle).filter(
        NewsArticle.created_at >= since
    ).all()

    items = [
        {"title": a.title, "content": a.content}
        for a in articles
    ]

    report = generate_sentiment_report(
        items=items,
        target_type="news",
        target_name=f"最近{hours}小时新闻",
        use_ai=use_ai
    )

    # 保存报告
    sentiment_report = SentimentReport(
        target_type="news",
        target_name=f"最近{hours}小时新闻",
        analysis=report.get("analysis"),
        conclusion=report.get("conclusion"),
        positive_count=report.get("positive_count", 0),
        negative_count=report.get("negative_count", 0),
        neutral_count=report.get("neutral_count", 0),
        overall_score=report.get("overall_score"),
    )
    db.add(sentiment_report)
    db.commit()

    return report


@router.get("/latest", response_model=Optional[SentimentReportResponse])
def get_latest_sentiment(db: Session = Depends(get_db)):
    """获取最新的情感分析报告"""
    return db.query(SentimentReport).order_by(SentimentReport.created_at.desc()).first()
