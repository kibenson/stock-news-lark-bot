"""
情感分析服务测试
"""
import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime


def test_local_sentiment_analysis_positive():
    """测试本地情感分析 - 正面"""
    from app.services.sentiment_analyzer import local_sentiment_analysis
    result = local_sentiment_analysis("股市大涨，盈利超预期，牛市来临")
    assert result["label"] == "positive"
    assert result["score"] > 0
    assert result["method"] == "local"


def test_local_sentiment_analysis_negative():
    """测试本地情感分析 - 负面"""
    from app.services.sentiment_analyzer import local_sentiment_analysis
    result = local_sentiment_analysis("股市暴跌，亏损严重，破产风险")
    assert result["label"] == "negative"
    assert result["score"] < 0
    assert result["method"] == "local"


def test_local_sentiment_analysis_neutral():
    """测试本地情感分析 - 中性"""
    from app.services.sentiment_analyzer import local_sentiment_analysis
    result = local_sentiment_analysis("今天是星期三，天气不错")
    assert result["label"] == "neutral"
    assert result["method"] == "local"


def test_local_sentiment_analysis_empty():
    """测试空文本情感分析"""
    from app.services.sentiment_analyzer import local_sentiment_analysis
    result = local_sentiment_analysis("")
    assert result["label"] == "neutral"
    assert result["score"] == 0.0


def test_analyze_text_without_ai():
    """测试 analyze_text 函数（不使用AI）"""
    from app.services.sentiment_analyzer import analyze_text
    result = analyze_text("股市上涨，好消息", use_ai=False)
    assert "label" in result
    assert "score" in result
    assert result["method"] == "local"


def test_generate_sentiment_report_empty():
    """测试空数据生成情感报告"""
    from app.services.sentiment_analyzer import generate_sentiment_report
    report = generate_sentiment_report([], "news", "测试")
    assert report["positive_count"] == 0
    assert report["negative_count"] == 0
    assert report["neutral_count"] == 0
    assert "暂无数据" in report["conclusion"]


def test_generate_sentiment_report_with_data():
    """测试有数据的情感报告生成"""
    from app.services.sentiment_analyzer import generate_sentiment_report
    items = [
        {"title": "股市大涨，创历史新高", "content": "盈利超预期"},
        {"title": "市场暴跌，损失惨重", "content": "亏损严重"},
        {"title": "今日市场平稳", "content": "无明显波动"},
    ]
    report = generate_sentiment_report(items, "news", "今日新闻")
    assert report["positive_count"] >= 0
    assert report["negative_count"] >= 0
    assert report["neutral_count"] >= 0
    total = report["positive_count"] + report["negative_count"] + report["neutral_count"]
    assert total == 3
    assert "conclusion" in report
    assert "analysis" in report


def test_batch_analyze():
    """测试批量分析"""
    from app.services.sentiment_analyzer import analyze_batch
    texts = ["股市上涨", "股市暴跌", "今天天气不错"]
    results = analyze_batch(texts, use_ai=False)
    assert len(results) == 3
    for r in results:
        assert "label" in r
        assert r["label"] in ["positive", "negative", "neutral"]
