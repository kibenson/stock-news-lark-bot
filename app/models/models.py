"""
SQLAlchemy 数据模型定义
"""
from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Text, Float, Boolean,
    DateTime, ForeignKey, JSON
)
from sqlalchemy.orm import relationship

from app.database import Base


class WatchStock(Base):
    """关注的股票"""
    __tablename__ = "watch_stocks"

    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String(20), unique=True, nullable=False, index=True, comment="股票代码，如 AAPL, 600519")
    name = Column(String(100), nullable=False, comment="股票名称")
    market = Column(String(50), default="US", comment="市场，如 US, CN, HK")
    notes = Column(Text, nullable=True, comment="备注")
    is_active = Column(Boolean, default=True, comment="是否激活监控")
    created_at = Column(DateTime, default=datetime.utcnow, comment="创建时间")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class MonitoredUser(Base):
    """监控的社交媒体用户"""
    __tablename__ = "monitored_users"

    id = Column(Integer, primary_key=True, index=True)
    platform = Column(String(50), nullable=False, comment="平台，如 twitter, xueqiu")
    username = Column(String(100), nullable=False, comment="用户名/账号")
    display_name = Column(String(200), nullable=True, comment="显示名称")
    notes = Column(Text, nullable=True, comment="备注")
    is_active = Column(Boolean, default=True, comment="是否激活监控")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关联的用户发言
    posts = relationship("UserPost", back_populates="monitored_user", cascade="all, delete-orphan")


class Keyword(Base):
    """关键词配置"""
    __tablename__ = "keywords"

    id = Column(Integer, primary_key=True, index=True)
    keyword = Column(String(200), unique=True, nullable=False, index=True, comment="关键词")
    category = Column(String(100), nullable=True, comment="分类，如 股票, 宏观, 行业")
    is_active = Column(Boolean, default=True, comment="是否激活爬取")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class NewsArticle(Base):
    """新闻文章"""
    __tablename__ = "news_articles"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(500), nullable=False, comment="新闻标题")
    content = Column(Text, nullable=True, comment="新闻内容摘要")
    source = Column(String(200), nullable=True, comment="来源，如 NewsAPI, Finnhub")
    url = Column(String(1000), nullable=True, unique=True, comment="原文链接")
    published_at = Column(DateTime, nullable=True, comment="发布时间")
    related_symbols = Column(String(500), nullable=True, comment="相关股票代码，逗号分隔")
    sentiment_score = Column(Float, nullable=True, comment="情感分数 -1.0 到 1.0")
    sentiment_label = Column(String(20), nullable=True, comment="情感标签: positive/negative/neutral")
    created_at = Column(DateTime, default=datetime.utcnow)


class UserPost(Base):
    """用户发言记录"""
    __tablename__ = "user_posts"

    id = Column(Integer, primary_key=True, index=True)
    monitored_user_id = Column(Integer, ForeignKey("monitored_users.id"), nullable=False)
    content = Column(Text, nullable=False, comment="发言内容")
    platform = Column(String(50), nullable=False, comment="平台")
    post_url = Column(String(1000), nullable=True, comment="原帖链接")
    posted_at = Column(DateTime, nullable=True, comment="发帖时间")
    sentiment_score = Column(Float, nullable=True, comment="情感分数")
    sentiment_label = Column(String(20), nullable=True, comment="情感标签")
    created_at = Column(DateTime, default=datetime.utcnow)

    # 关联的监控用户
    monitored_user = relationship("MonitoredUser", back_populates="posts")


class PushHistory(Base):
    """推送历史记录"""
    __tablename__ = "push_histories"

    id = Column(Integer, primary_key=True, index=True)
    push_type = Column(String(50), nullable=False, comment="推送类型: daily_report, manual, alert")
    title = Column(String(500), nullable=True, comment="推送标题")
    content = Column(Text, nullable=True, comment="推送内容摘要")
    status = Column(String(20), nullable=False, default="pending", comment="状态: pending/success/failed")
    webhook_url = Column(String(1000), nullable=True, comment="目标Webhook URL")
    lark_response = Column(JSON, nullable=True, comment="Lark API响应")
    error_message = Column(Text, nullable=True, comment="错误信息")
    pushed_at = Column(DateTime, default=datetime.utcnow, comment="推送时间")


class SentimentReport(Base):
    """情感分析报告"""
    __tablename__ = "sentiment_reports"

    id = Column(Integer, primary_key=True, index=True)
    target_type = Column(String(50), nullable=False, comment="分析目标类型: news/user_post/keyword")
    target_id = Column(Integer, nullable=True, comment="分析目标ID")
    target_name = Column(String(200), nullable=True, comment="分析目标名称")
    analysis = Column(JSON, nullable=True, comment="详细分析结果")
    conclusion = Column(Text, nullable=True, comment="分析结论摘要")
    positive_count = Column(Integer, default=0, comment="正面数量")
    negative_count = Column(Integer, default=0, comment="负面数量")
    neutral_count = Column(Integer, default=0, comment="中性数量")
    overall_score = Column(Float, nullable=True, comment="整体情感分数")
    created_at = Column(DateTime, default=datetime.utcnow)
