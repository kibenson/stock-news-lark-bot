"""
Pydantic Schema 定义 - 请求/响应数据验证
"""
from datetime import datetime
from typing import Optional, List, Any, Dict
from pydantic import BaseModel, Field, HttpUrl


# ==================== WatchStock Schemas ====================

class WatchStockBase(BaseModel):
    symbol: str = Field(..., min_length=1, max_length=20, description="股票代码")
    name: str = Field(..., min_length=1, max_length=100, description="股票名称")
    market: str = Field(default="US", max_length=50, description="市场")
    notes: Optional[str] = Field(None, description="备注")
    is_active: bool = Field(default=True, description="是否激活")


class WatchStockCreate(WatchStockBase):
    pass


class WatchStockUpdate(BaseModel):
    name: Optional[str] = None
    market: Optional[str] = None
    notes: Optional[str] = None
    is_active: Optional[bool] = None


class WatchStockResponse(WatchStockBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ==================== MonitoredUser Schemas ====================

class MonitoredUserBase(BaseModel):
    platform: str = Field(..., max_length=50, description="平台")
    username: str = Field(..., max_length=100, description="用户名")
    display_name: Optional[str] = Field(None, max_length=200, description="显示名称")
    notes: Optional[str] = Field(None, description="备注")
    is_active: bool = Field(default=True)


class MonitoredUserCreate(MonitoredUserBase):
    pass


class MonitoredUserUpdate(BaseModel):
    display_name: Optional[str] = None
    notes: Optional[str] = None
    is_active: Optional[bool] = None


class MonitoredUserResponse(MonitoredUserBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ==================== Keyword Schemas ====================

class KeywordBase(BaseModel):
    keyword: str = Field(..., min_length=1, max_length=200, description="关键词")
    category: Optional[str] = Field(None, max_length=100, description="分类")
    is_active: bool = Field(default=True)


class KeywordCreate(KeywordBase):
    pass


class KeywordUpdate(BaseModel):
    category: Optional[str] = None
    is_active: Optional[bool] = None


class KeywordResponse(KeywordBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ==================== NewsArticle Schemas ====================

class NewsArticleResponse(BaseModel):
    id: int
    title: str
    content: Optional[str] = None
    source: Optional[str] = None
    url: Optional[str] = None
    published_at: Optional[datetime] = None
    related_symbols: Optional[str] = None
    sentiment_score: Optional[float] = None
    sentiment_label: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


# ==================== UserPost Schemas ====================

class UserPostResponse(BaseModel):
    id: int
    monitored_user_id: int
    content: str
    platform: str
    post_url: Optional[str] = None
    posted_at: Optional[datetime] = None
    sentiment_score: Optional[float] = None
    sentiment_label: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


# ==================== PushHistory Schemas ====================

class PushHistoryResponse(BaseModel):
    id: int
    push_type: str
    title: Optional[str] = None
    content: Optional[str] = None
    status: str
    webhook_url: Optional[str] = None
    lark_response: Optional[Any] = None
    error_message: Optional[str] = None
    pushed_at: datetime

    class Config:
        from_attributes = True


# ==================== SentimentReport Schemas ====================

class SentimentReportResponse(BaseModel):
    id: int
    target_type: str
    target_id: Optional[int] = None
    target_name: Optional[str] = None
    analysis: Optional[Any] = None
    conclusion: Optional[str] = None
    positive_count: int
    negative_count: int
    neutral_count: int
    overall_score: Optional[float] = None
    created_at: datetime

    class Config:
        from_attributes = True


# ==================== 通用响应 Schemas ====================

class PaginatedResponse(BaseModel):
    total: int
    items: List[Any]
    page: int = 1
    page_size: int = 20


class MessageResponse(BaseModel):
    message: str
    success: bool = True


class DashboardData(BaseModel):
    total_stocks: int
    total_users: int
    total_keywords: int
    total_news: int
    recent_push_count: int
    latest_sentiment: Optional[Dict[str, Any]] = None
    recent_news: List[Dict[str, Any]] = []
    push_success_rate: float = 0.0


class ManualPushRequest(BaseModel):
    push_type: str = Field(default="manual", description="推送类型")
    include_sentiment: bool = Field(default=True, description="是否包含情感分析")
    custom_message: Optional[str] = Field(None, description="自定义消息内容")


class AIAnalyzeRequest(BaseModel):
    content: str = Field(..., min_length=1, description="要分析的内容")
    analysis_type: str = Field(default="sentiment", description="分析类型: sentiment/summary/advice")
    custom_prompt: Optional[str] = Field(None, description="自定义提示词")
