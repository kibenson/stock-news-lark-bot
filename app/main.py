"""
FastAPI 应用主入口
"""
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi import Request
import os

from app.config import settings
from app.database import init_db

# 配置日志
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper(), logging.INFO),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时初始化
    logger.info("正在初始化应用...")
    init_db()

    # 启动定时调度器
    from app.services.scheduler import start_scheduler
    start_scheduler()
    logger.info("应用启动完成 ✅")

    yield

    # 关闭时清理
    from app.services.scheduler import stop_scheduler
    stop_scheduler()
    logger.info("应用已关闭")


# 创建 FastAPI 应用
app = FastAPI(
    title="股票新闻 Lark 推送 Bot",
    description="全球股票新闻智能推送到Lark群 + 交互式管理网页 + 情感分析",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
)

# ---- 中间件配置 ----
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---- 注册 API 路由 ----
from app.routers import stocks, users, keywords, news, sentiment, push, dashboard, ai

app.include_router(stocks.router)
app.include_router(users.router)
app.include_router(keywords.router)
app.include_router(news.router)
app.include_router(sentiment.router)
app.include_router(push.router)
app.include_router(dashboard.router)
app.include_router(ai.router)

# ---- 模板配置 ----
templates_dir = os.path.join(os.path.dirname(__file__), "templates")
templates = Jinja2Templates(directory=templates_dir)


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """返回前端交互页面"""
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/health")
async def health_check():
    """健康检查接口"""
    return {
        "status": "ok",
        "version": "1.0.0",
        "app": "stock-news-lark-bot"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.app_host,
        port=settings.app_port,
        reload=settings.debug,
        log_level=settings.log_level.lower(),
    )
