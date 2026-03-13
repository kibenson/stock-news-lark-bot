"""
新闻 API 路由
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, Query, BackgroundTasks
from sqlalchemy.orm import Session
from datetime import datetime, timedelta

from app.database import get_db
from app.models.models import NewsArticle
from app.schemas.schemas import NewsArticleResponse, MessageResponse

router = APIRouter(prefix="/api/news", tags=["新闻"])


@router.get("", response_model=List[NewsArticleResponse])
def list_news(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    sentiment: Optional[str] = Query(None, description="按情感过滤: positive/negative/neutral"),
    symbol: Optional[str] = Query(None, description="按股票代码过滤"),
    source: Optional[str] = Query(None, description="按来源过滤"),
    hours: int = Query(24, ge=1, le=168, description="最近N小时"),
    db: Session = Depends(get_db)
):
    """获取新闻列表"""
    since = datetime.utcnow() - timedelta(hours=hours)
    query = db.query(NewsArticle).filter(NewsArticle.created_at >= since)

    if sentiment:
        query = query.filter(NewsArticle.sentiment_label == sentiment)
    if symbol:
        query = query.filter(NewsArticle.related_symbols.contains(symbol.upper()))
    if source:
        query = query.filter(NewsArticle.source.contains(source))

    total = query.count()
    articles = (
        query
        .order_by(NewsArticle.published_at.desc().nullslast(), NewsArticle.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    return articles


@router.get("/fetch", response_model=MessageResponse)
def trigger_news_fetch(
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """手动触发新闻抓取"""
    def do_fetch():
        from app.models.models import WatchStock, Keyword
        from app.services.news_fetcher import fetch_all_news, save_articles_to_db

        active_stocks = db.query(WatchStock).filter(WatchStock.is_active == True).all()
        active_keywords = db.query(Keyword).filter(Keyword.is_active == True).all()
        symbols = [s.symbol for s in active_stocks]
        keywords = [k.keyword for k in active_keywords]

        articles = fetch_all_news(symbols=symbols, keywords=keywords)
        count = save_articles_to_db(articles, db)
        db.close()

    background_tasks.add_task(do_fetch)
    return {"message": "新闻抓取任务已启动（后台执行）", "success": True}


@router.get("/{news_id}", response_model=NewsArticleResponse)
def get_news(news_id: int, db: Session = Depends(get_db)):
    """获取单条新闻详情"""
    from fastapi import HTTPException
    article = db.query(NewsArticle).filter(NewsArticle.id == news_id).first()
    if not article:
        raise HTTPException(status_code=404, detail="新闻不存在")
    return article
