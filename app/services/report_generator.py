"""
报告生成服务 - 整合新闻、情感分析、AI摘要生成完整报告
"""
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)


def generate_daily_report(db, use_ai: bool = True) -> Dict[str, Any]:
    """
    生成每日报告
    
    Args:
        db: 数据库会话
        use_ai: 是否使用AI生成摘要
    
    Returns:
        报告数据字典
    """
    from app.models.models import NewsArticle, WatchStock, SentimentReport
    from app.services.sentiment_analyzer import generate_sentiment_report

    # 获取过去24小时的新闻
    since = datetime.utcnow() - timedelta(hours=24)
    articles = db.query(NewsArticle).filter(
        NewsArticle.created_at >= since
    ).order_by(NewsArticle.published_at.desc()).limit(50).all()

    # 转换为字典
    articles_data = [
        {
            "id": a.id,
            "title": a.title,
            "content": a.content,
            "source": a.source,
            "url": a.url,
            "published_at": a.published_at.isoformat() if a.published_at else None,
            "sentiment_score": a.sentiment_score,
            "sentiment_label": a.sentiment_label,
        }
        for a in articles
    ]

    # 生成情感分析报告
    sentiment_report = generate_sentiment_report(
        items=articles_data,
        target_type="news",
        target_name="今日新闻",
        use_ai=False  # 批量分析时用本地方式节省API
    )

    # AI摘要（可选）
    ai_summary = None
    if use_ai and articles_data:
        try:
            from app.services.ai_provider import ai_provider
            if ai_provider.is_available():
                ai_summary = ai_provider.summarize_news(articles_data)
        except Exception as e:
            logger.warning(f"AI摘要生成失败: {e}")

    # 获取关注的股票列表
    watch_stocks = db.query(WatchStock).filter(WatchStock.is_active == True).all()
    stocks_data = [
        {"symbol": s.symbol, "name": s.name, "market": s.market}
        for s in watch_stocks
    ]

    # 保存情感报告到数据库
    try:
        from app.models.models import SentimentReport
        report = SentimentReport(
            target_type="daily_news",
            target_name=datetime.now().strftime("%Y-%m-%d"),
            analysis=sentiment_report.get("analysis"),
            conclusion=sentiment_report.get("conclusion"),
            positive_count=sentiment_report.get("positive_count", 0),
            negative_count=sentiment_report.get("negative_count", 0),
            neutral_count=sentiment_report.get("neutral_count", 0),
            overall_score=sentiment_report.get("overall_score"),
        )
        db.add(report)
        db.commit()
    except Exception as e:
        logger.warning(f"保存情感报告失败: {e}")

    return {
        "date": datetime.now().strftime("%Y-%m-%d"),
        "total_news": len(articles_data),
        "articles": articles_data[:10],  # 返回前10条
        "sentiment_summary": sentiment_report,
        "ai_summary": ai_summary,
        "watch_stocks": stocks_data,
        "generated_at": datetime.now().isoformat(),
    }


def format_report_for_lark(report: Dict[str, Any]) -> str:
    """
    将报告格式化为适合 Lark 展示的文本
    
    Args:
        report: 报告数据
    
    Returns:
        格式化的 Markdown 文本
    """
    lines = []
    date = report.get("date", datetime.now().strftime("%Y-%m-%d"))
    lines.append(f"# 📊 {date} 全球股票新闻日报\n")

    # AI摘要
    ai_summary = report.get("ai_summary")
    if ai_summary:
        lines.append("## 🤖 AI智能摘要")
        lines.append(ai_summary)
        lines.append("")

    # 情感概览
    sentiment = report.get("sentiment_summary", {})
    if sentiment:
        pos = sentiment.get("positive_count", 0)
        neg = sentiment.get("negative_count", 0)
        neu = sentiment.get("neutral_count", 0)
        score = sentiment.get("overall_score", 0)

        sentiment_arrow = "📈" if score > 0.1 else ("📉" if score < -0.1 else "➡️")
        lines.append("## 💬 市场情绪")
        lines.append(f"{sentiment_arrow} 今日情感指数: **{score:+.2f}**")
        lines.append(f"正面 🟢 {pos} | 负面 🔴 {neg} | 中性 ⚪ {neu}")
        lines.append(f"\n> {sentiment.get('conclusion', '')}")
        lines.append("")

    # 重点新闻
    articles = report.get("articles", [])
    if articles:
        lines.append(f"## 📰 重点新闻（共{report.get('total_news', 0)}条）")
        for i, article in enumerate(articles[:8], 1):
            title = (article.get("title") or "")[:80]
            source = article.get("source", "")
            url = article.get("url", "")
            sentiment_label = article.get("sentiment_label", "")
            icon = {"positive": "🟢", "negative": "🔴", "neutral": "⚪"}.get(sentiment_label, "⚪")

            if url:
                lines.append(f"{i}. {icon} [{title}]({url})")
            else:
                lines.append(f"{i}. {icon} {title}")
            if source:
                lines.append(f"   *{source}*")
        lines.append("")

    lines.append(f"*生成时间: {report.get('generated_at', '')}*")
    return "\n".join(lines)
