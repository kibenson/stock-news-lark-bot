"""
关键词资讯爬取服务 - 支持多个资讯源，预留反爬策略接口
"""
import logging
import time
import random
from typing import List, Dict, Any, Optional
from datetime import datetime

import requests
from bs4 import BeautifulSoup

from app.config import settings

logger = logging.getLogger(__name__)

# 随机 User-Agent 列表（反爬）
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
]


def _get_random_headers() -> Dict[str, str]:
    """获取随机请求头（反爬策略）"""
    return {
        "User-Agent": random.choice(USER_AGENTS),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
        "Accept-Encoding": "gzip, deflate",
        "Connection": "keep-alive",
    }


def _random_delay(min_sec: float = 1.0, max_sec: float = 3.0):
    """随机延迟（防止被封）"""
    delay = random.uniform(min_sec, max_sec)
    time.sleep(delay)


def crawl_google_news(keyword: str, max_results: int = 10) -> List[Dict[str, Any]]:
    """
    通过 Google News RSS 抓取关键词相关新闻（无需API Key）
    
    Args:
        keyword: 搜索关键词
        max_results: 最大结果数
    
    Returns:
        新闻列表
    """
    import feedparser

    encoded_keyword = requests.utils.quote(keyword)
    url = f"https://news.google.com/rss/search?q={encoded_keyword}&hl=zh-CN&gl=CN&ceid=CN:zh-Hans"

    try:
        feed = feedparser.parse(url)
        results = []
        for entry in feed.entries[:max_results]:
            results.append({
                "title": getattr(entry, 'title', ''),
                "content": getattr(entry, 'summary', '') or getattr(entry, 'description', ''),
                "url": getattr(entry, 'link', ''),
                "source": f"Google News/{keyword}",
                "published_at": _parse_published(getattr(entry, 'published', None)),
                "keyword": keyword,
            })
        logger.info(f"Google News 关键词 '{keyword}' 抓取 {len(results)} 条")
        return results
    except Exception as e:
        logger.error(f"Google News 抓取失败 (keyword={keyword}): {e}")
        return []


def crawl_bing_news(keyword: str, max_results: int = 10) -> List[Dict[str, Any]]:
    """
    通过 Bing News 抓取关键词相关新闻
    
    Args:
        keyword: 搜索关键词
        max_results: 最大结果数
    
    Returns:
        新闻列表
    """
    url = f"https://www.bing.com/news/search?q={requests.utils.quote(keyword)}&format=rss"

    try:
        import feedparser
        feed = feedparser.parse(url)
        results = []
        for entry in feed.entries[:max_results]:
            results.append({
                "title": getattr(entry, 'title', ''),
                "content": getattr(entry, 'summary', '') or '',
                "url": getattr(entry, 'link', ''),
                "source": f"Bing News/{keyword}",
                "published_at": _parse_published(getattr(entry, 'published', None)),
                "keyword": keyword,
            })
        logger.info(f"Bing News 关键词 '{keyword}' 抓取 {len(results)} 条")
        return results
    except Exception as e:
        logger.error(f"Bing News 抓取失败 (keyword={keyword}): {e}")
        return []


def crawl_newsapi_keyword(keyword: str, max_results: int = 10) -> List[Dict[str, Any]]:
    """
    通过 NewsAPI 搜索关键词相关新闻（需要 API Key）
    """
    if not settings.news_api_key or settings.news_api_key == "your-newsapi-key":
        return []

    try:
        response = requests.get(
            "https://newsapi.org/v2/everything",
            params={
                "q": keyword,
                "pageSize": max_results,
                "sortBy": "relevancy",
                "apiKey": settings.news_api_key,
            },
            timeout=10
        )
        response.raise_for_status()
        data = response.json()

        results = []
        for article in data.get("articles", []):
            if article.get("url") == "[Removed]":
                continue
            results.append({
                "title": article.get("title", "")[:500],
                "content": article.get("description") or article.get("content") or "",
                "url": article.get("url", "")[:1000],
                "source": f"NewsAPI/{article.get('source', {}).get('name', 'Unknown')}",
                "published_at": (
                    datetime.fromisoformat(article["publishedAt"].replace("Z", "+00:00"))
                    if article.get("publishedAt") else None
                ),
                "keyword": keyword,
            })
        return results
    except Exception as e:
        logger.error(f"NewsAPI 关键词抓取失败 (keyword={keyword}): {e}")
        return []


def _parse_published(date_str: Optional[str]) -> Optional[datetime]:
    """解析发布时间"""
    if not date_str:
        return None
    try:
        import email.utils
        return datetime(*email.utils.parsedate(date_str)[:6])
    except Exception:
        try:
            return datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        except Exception:
            return None


def crawl_all_keywords(
    keywords: List[str],
    max_per_keyword: int = 10
) -> List[Dict[str, Any]]:
    """
    对所有关键词进行抓取，合并去重
    
    Args:
        keywords: 关键词列表
        max_per_keyword: 每个关键词最大抓取数
    
    Returns:
        去重后的新闻列表
    """
    all_results = []
    seen_urls = set()

    for keyword in keywords:
        # Google News（免费，主要来源）
        google_results = crawl_google_news(keyword, max_per_keyword)
        for item in google_results:
            url = item.get("url", "")
            if url and url not in seen_urls:
                all_results.append(item)
                seen_urls.add(url)

        # Bing News（备用来源）
        bing_results = crawl_bing_news(keyword, max_per_keyword // 2)
        for item in bing_results:
            url = item.get("url", "")
            if url and url not in seen_urls:
                all_results.append(item)
                seen_urls.add(url)

        # NewsAPI（需要Key）
        newsapi_results = crawl_newsapi_keyword(keyword, max_per_keyword // 2)
        for item in newsapi_results:
            url = item.get("url", "")
            if url and url not in seen_urls:
                all_results.append(item)
                seen_urls.add(url)

        # 随机延迟防止被封
        _random_delay(0.5, 1.5)

    logger.info(f"关键词爬取完成，共 {len(all_results)} 条（去重后）")
    return all_results


def save_keyword_news_to_db(articles: List[Dict[str, Any]], db) -> int:
    """
    将关键词爬取的新闻保存到数据库
    
    Args:
        articles: 文章列表
        db: 数据库会话
    
    Returns:
        新增数量
    """
    from app.models.models import NewsArticle
    from app.services.sentiment_analyzer import analyze_text

    new_count = 0
    for article in articles:
        # URL去重
        if article.get("url"):
            exists = db.query(NewsArticle).filter(
                NewsArticle.url == article["url"]
            ).first()
            if exists:
                continue

        # 情感分析
        text = article.get("title", "") + " " + (article.get("content") or "")
        sentiment = analyze_text(text)

        db_article = NewsArticle(
            title=article.get("title", "")[:500],
            content=article.get("content", "")[:2000] if article.get("content") else None,
            source=article.get("source", ""),
            url=article.get("url", "")[:1000] if article.get("url") else None,
            published_at=article.get("published_at"),
            related_symbols=article.get("keyword"),
            sentiment_score=sentiment.get("score"),
            sentiment_label=sentiment.get("label"),
        )
        db.add(db_article)
        new_count += 1

    db.commit()
    logger.info(f"关键词新闻保存 {new_count} 条到数据库")
    return new_count
