"""
新闻抓取服务 - 支持多个新闻源（NewsAPI, Finnhub, RSS等）
"""
import logging
import hashlib
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional

import feedparser
import requests

from app.config import settings

logger = logging.getLogger(__name__)

# ---- 预设的金融相关 RSS 源（无需API Key） ----
RSS_FEEDS = {
    "Reuters Business": "https://feeds.reuters.com/reuters/businessNews",
    "Yahoo Finance": "https://finance.yahoo.com/news/rssindex",
    "MarketWatch": "https://feeds.marketwatch.com/marketwatch/topstories/",
    "Seeking Alpha": "https://seekingalpha.com/market_currents.xml",
    "Bloomberg Markets": "https://feeds.bloomberg.com/markets/news.rss",
    "CNBC": "https://www.cnbc.com/id/100003114/device/rss/rss.html",
    "Financial Times": "https://www.ft.com/rss/home/us",
}


def _generate_url_hash(url: str) -> str:
    """生成URL的MD5哈希用于去重"""
    return hashlib.md5(url.encode()).hexdigest()


def _parse_rss_date(date_str: Optional[str]) -> Optional[datetime]:
    """解析RSS日期格式"""
    if not date_str:
        return None
    try:
        import email.utils
        return datetime(*email.utils.parsedate(date_str)[:6])
    except Exception:
        return None


def fetch_rss_news(
    symbols: Optional[List[str]] = None,
    keywords: Optional[List[str]] = None,
    max_articles: int = 50
) -> List[Dict[str, Any]]:
    """
    从 RSS 源抓取新闻（无需API Key）
    
    Args:
        symbols: 股票代码过滤列表
        keywords: 关键词过滤列表
        max_articles: 最大文章数
    
    Returns:
        新闻文章列表
    """
    articles = []
    seen_urls = set()

    for source_name, feed_url in RSS_FEEDS.items():
        try:
            feed = feedparser.parse(feed_url)
            for entry in feed.entries[:20]:  # 每个源最多取20条
                url = getattr(entry, 'link', '') or ''
                if not url or url in seen_urls:
                    continue

                title = getattr(entry, 'title', '') or ''
                content = (
                    getattr(entry, 'summary', '') or
                    getattr(entry, 'description', '') or ''
                )

                # 关键词/股票代码过滤
                if symbols or keywords:
                    text_to_check = (title + " " + content).upper()
                    match = False
                    if symbols:
                        for sym in symbols:
                            if sym.upper() in text_to_check:
                                match = True
                                break
                    if not match and keywords:
                        for kw in keywords:
                            if kw.upper() in text_to_check:
                                match = True
                                break
                    if not match:
                        continue

                published_at = _parse_rss_date(
                    getattr(entry, 'published', None)
                )

                articles.append({
                    "title": title[:500],
                    "content": content[:1000],
                    "source": source_name,
                    "url": url[:1000],
                    "published_at": published_at,
                    "related_symbols": ",".join(symbols) if symbols else None,
                })
                seen_urls.add(url)

                if len(articles) >= max_articles:
                    break

        except Exception as e:
            logger.warning(f"RSS源 {source_name} 抓取失败: {e}")
            continue

    logger.info(f"RSS抓取完成，共获取 {len(articles)} 条新闻")
    return articles


def fetch_newsapi(
    query: str = "stock market",
    from_date: Optional[datetime] = None,
    max_articles: int = 20
) -> List[Dict[str, Any]]:
    """
    从 NewsAPI 抓取新闻（需要 NEWS_API_KEY）
    
    Args:
        query: 搜索关键词
        from_date: 起始日期
        max_articles: 最大文章数
    
    Returns:
        新闻文章列表
    """
    if not settings.news_api_key or settings.news_api_key == "your-newsapi-key":
        logger.info("NewsAPI Key 未配置，跳过 NewsAPI 抓取")
        return []

    if from_date is None:
        from_date = datetime.utcnow() - timedelta(days=1)

    url = "https://newsapi.org/v2/everything"
    params = {
        "q": query,
        "from": from_date.strftime("%Y-%m-%dT%H:%M:%S"),
        "language": "en",
        "sortBy": "relevancy",
        "pageSize": min(max_articles, 100),
        "apiKey": settings.news_api_key,
    }

    try:
        response = requests.get(url, params=params, timeout=15)
        response.raise_for_status()
        data = response.json()

        articles = []
        for article in data.get("articles", []):
            if article.get("url") == "[Removed]":
                continue
            articles.append({
                "title": (article.get("title") or "")[:500],
                "content": (article.get("description") or article.get("content") or "")[:1000],
                "source": f"NewsAPI/{article.get('source', {}).get('name', 'Unknown')}",
                "url": (article.get("url") or "")[:1000],
                "published_at": (
                    datetime.fromisoformat(article["publishedAt"].replace("Z", "+00:00"))
                    if article.get("publishedAt") else None
                ),
                "related_symbols": None,
            })
        logger.info(f"NewsAPI 获取 {len(articles)} 条新闻")
        return articles

    except Exception as e:
        logger.error(f"NewsAPI 请求失败: {e}")
        return []


def fetch_finnhub_news(
    symbol: Optional[str] = None,
    from_date: Optional[datetime] = None
) -> List[Dict[str, Any]]:
    """
    从 Finnhub 抓取新闻（需要 FINNHUB_API_KEY）
    
    Args:
        symbol: 股票代码（如 AAPL），为空则获取市场新闻
        from_date: 起始日期
    
    Returns:
        新闻文章列表
    """
    if not settings.finnhub_api_key or settings.finnhub_api_key == "your-finnhub-key":
        logger.info("Finnhub API Key 未配置，跳过 Finnhub 抓取")
        return []

    if from_date is None:
        from_date = datetime.utcnow() - timedelta(days=1)
    to_date = datetime.utcnow()

    if symbol:
        url = f"https://finnhub.io/api/v1/company-news"
        params = {
            "symbol": symbol,
            "from": from_date.strftime("%Y-%m-%d"),
            "to": to_date.strftime("%Y-%m-%d"),
            "token": settings.finnhub_api_key,
        }
    else:
        url = "https://finnhub.io/api/v1/news"
        params = {
            "category": "general",
            "token": settings.finnhub_api_key,
        }

    try:
        response = requests.get(url, params=params, timeout=15)
        response.raise_for_status()
        data = response.json()

        articles = []
        for item in (data if isinstance(data, list) else []):
            articles.append({
                "title": (item.get("headline") or "")[:500],
                "content": (item.get("summary") or "")[:1000],
                "source": f"Finnhub/{item.get('source', 'Unknown')}",
                "url": (item.get("url") or "")[:1000],
                "published_at": (
                    datetime.fromtimestamp(item["datetime"])
                    if item.get("datetime") else None
                ),
                "related_symbols": symbol,
            })
        logger.info(f"Finnhub 获取 {len(articles)} 条新闻 (symbol={symbol})")
        return articles

    except Exception as e:
        logger.error(f"Finnhub 请求失败: {e}")
        return []


def fetch_all_news(
    symbols: Optional[List[str]] = None,
    keywords: Optional[List[str]] = None,
    max_articles: int = 100
) -> List[Dict[str, Any]]:
    """
    从所有配置的新闻源抓取新闻，去重合并
    
    Args:
        symbols: 关注的股票代码列表
        keywords: 关键词列表
        max_articles: 最大文章总数
    
    Returns:
        去重后的新闻列表，按发布时间降序排列
    """
    all_articles = []
    seen_urls = set()

    # 1. RSS 源（免费）
    rss_articles = fetch_rss_news(symbols=symbols, keywords=keywords)
    for a in rss_articles:
        if a["url"] and a["url"] not in seen_urls:
            all_articles.append(a)
            seen_urls.add(a["url"])

    # 2. NewsAPI（需要Key）
    query = " OR ".join(symbols) if symbols else "stock market finance"
    newsapi_articles = fetch_newsapi(query=query)
    for a in newsapi_articles:
        if a["url"] and a["url"] not in seen_urls:
            all_articles.append(a)
            seen_urls.add(a["url"])

    # 3. Finnhub（需要Key，按股票代码抓取）
    if symbols:
        for symbol in symbols[:5]:  # 限制最多5个
            finnhub_articles = fetch_finnhub_news(symbol=symbol)
            for a in finnhub_articles:
                if a["url"] and a["url"] not in seen_urls:
                    all_articles.append(a)
                    seen_urls.add(a["url"])
    else:
        finnhub_articles = fetch_finnhub_news()
        for a in finnhub_articles:
            if a["url"] and a["url"] not in seen_urls:
                all_articles.append(a)
                seen_urls.add(a["url"])

    # 按发布时间降序排列
    all_articles.sort(
        key=lambda x: x.get("published_at") or datetime.min,
        reverse=True
    )

    logger.info(f"共抓取 {len(all_articles)} 条新闻（去重后）")
    return all_articles[:max_articles]


def save_articles_to_db(articles: List[Dict[str, Any]], db) -> int:
    """
    将抓取的新闻保存到数据库（自动去重）
    
    Args:
        articles: 新闻列表
        db: 数据库会话
    
    Returns:
        新增的文章数量
    """
    from app.models.models import NewsArticle
    from app.services.sentiment_analyzer import analyze_text

    new_count = 0
    for article in articles:
        # 按URL去重
        if article.get("url"):
            exists = db.query(NewsArticle).filter(
                NewsArticle.url == article["url"]
            ).first()
            if exists:
                continue

        # 进行情感分析
        text = article.get("title", "") + " " + (article.get("content") or "")
        sentiment = analyze_text(text)

        db_article = NewsArticle(
            title=article.get("title", "")[:500],
            content=article.get("content", "")[:2000] if article.get("content") else None,
            source=article.get("source", ""),
            url=article.get("url", "")[:1000] if article.get("url") else None,
            published_at=article.get("published_at"),
            related_symbols=article.get("related_symbols"),
            sentiment_score=sentiment.get("score"),
            sentiment_label=sentiment.get("label"),
        )
        db.add(db_article)
        new_count += 1

    db.commit()
    logger.info(f"保存 {new_count} 条新新闻到数据库")
    return new_count
