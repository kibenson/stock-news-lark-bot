"""
新闻抓取服务测试
"""
import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime


def test_parse_rss_date_valid():
    """测试解析有效的RSS日期"""
    from app.services.news_fetcher import _parse_rss_date
    result = _parse_rss_date("Thu, 01 Jan 2024 08:00:00 +0000")
    assert isinstance(result, datetime)
    assert result.year == 2024


def test_parse_rss_date_none():
    """测试解析None日期"""
    from app.services.news_fetcher import _parse_rss_date
    result = _parse_rss_date(None)
    assert result is None


def test_parse_rss_date_invalid():
    """测试解析无效日期"""
    from app.services.news_fetcher import _parse_rss_date
    result = _parse_rss_date("invalid-date-string")
    assert result is None


def test_fetch_newsapi_without_key():
    """测试没有 NewsAPI Key 时跳过"""
    from app.services.news_fetcher import fetch_newsapi
    with patch('app.services.news_fetcher.settings') as mock_settings:
        mock_settings.news_api_key = None
        result = fetch_newsapi()
    assert result == []


def test_fetch_newsapi_with_placeholder_key():
    """测试有占位符 Key 时跳过"""
    from app.services.news_fetcher import fetch_newsapi
    with patch('app.services.news_fetcher.settings') as mock_settings:
        mock_settings.news_api_key = "your-newsapi-key"
        result = fetch_newsapi()
    assert result == []


def test_fetch_finnhub_without_key():
    """测试没有 Finnhub Key 时跳过"""
    from app.services.news_fetcher import fetch_finnhub_news
    with patch('app.services.news_fetcher.settings') as mock_settings:
        mock_settings.finnhub_api_key = None
        result = fetch_finnhub_news()
    assert result == []


def test_fetch_newsapi_success():
    """测试 NewsAPI 成功抓取"""
    from app.services.news_fetcher import fetch_newsapi
    mock_data = {
        "articles": [
            {
                "title": "Test Stock News",
                "description": "Test description",
                "url": "https://example.com/news/1",
                "publishedAt": "2024-01-01T08:00:00Z",
                "source": {"name": "Test Source"},
                "content": None,
            }
        ]
    }
    mock_response = MagicMock()
    mock_response.json.return_value = mock_data
    mock_response.raise_for_status = MagicMock()

    with patch('app.services.news_fetcher.settings') as mock_settings, \
         patch('app.services.news_fetcher.requests.get', return_value=mock_response):
        mock_settings.news_api_key = "real-api-key"
        result = fetch_newsapi(query="stock market", max_articles=5)

    assert len(result) == 1
    assert result[0]["title"] == "Test Stock News"
    assert result[0]["url"] == "https://example.com/news/1"


def test_fetch_all_news_deduplication():
    """测试新闻去重"""
    from app.services.news_fetcher import fetch_all_news

    same_url = "https://example.com/same-article"
    article1 = {"title": "Article 1", "content": "Content 1", "source": "Source A", "url": same_url, "published_at": None, "related_symbols": None}
    article2 = {"title": "Article 1 Copy", "content": "Content 1", "source": "Source B", "url": same_url, "published_at": None, "related_symbols": None}

    with patch('app.services.news_fetcher.fetch_rss_news', return_value=[article1]), \
         patch('app.services.news_fetcher.fetch_newsapi', return_value=[article2]), \
         patch('app.services.news_fetcher.fetch_finnhub_news', return_value=[]):
        results = fetch_all_news()

    # 相同 URL 应该只保留一条
    urls = [r["url"] for r in results]
    assert len(set(urls)) == len(urls), "存在重复的URL"
