# 📊 股票新闻 Lark Bot

> 全球股票新闻智能推送到Lark群 + 交互式管理网页 + 情感分析 + AI能力集成

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110-green.svg)](https://fastapi.tiangolo.com)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

## 🌟 功能特色

| 功能 | 说明 |
|------|------|
| 📰 **全球股票新闻聚合** | 多源抓取（RSS/NewsAPI/Finnhub），自动去重排序 |
| 🔔 **Lark群智能推送** | 支持文本/富文本/交互卡片消息，多群推送 |
| 🌐 **交互式管理页面** | 现代化单页应用，管理股票/用户/关键词 |
| 👤 **用户发言监控** | 监控Twitter/雪球等平台用户发言 |
| 🔍 **关键词资讯爬取** | 按关键词自动爬取相关资讯 |
| 💬 **情感文本分析** | 本地规则分析 + AI深度分析双模式 |
| 🤖 **AI能力集成** | 千问(Qwen) API，支持摘要/情感/建议 |
| ⏰ **定时自动推送** | APScheduler，每天定时执行完整任务流 |
| 🐳 **Docker一键部署** | Dockerfile + docker-compose |

## 🏗️ 项目架构

```
stock-news-lark-bot/
├── app/
│   ├── main.py                    # FastAPI 入口
│   ├── config.py                  # 配置加载 (pydantic-settings)
│   ├── database.py                # SQLAlchemy 数据库连接
│   ├── models/
│   │   └── models.py              # 数据模型 (7个表)
│   ├── schemas/
│   │   └── schemas.py             # Pydantic 请求/响应模型
│   ├── routers/                   # API 路由 (8个模块)
│   │   ├── stocks.py              # 股票 CRUD
│   │   ├── users.py               # 用户监控 CRUD
│   │   ├── keywords.py            # 关键词 CRUD
│   │   ├── news.py                # 新闻列表/抓取
│   │   ├── sentiment.py           # 情感分析
│   │   ├── push.py                # 推送管理
│   │   ├── dashboard.py           # 仪表盘数据
│   │   └── ai.py                  # AI分析接口
│   ├── services/                  # 业务逻辑
│   │   ├── news_fetcher.py        # 新闻抓取 (RSS/NewsAPI/Finnhub)
│   │   ├── lark_notifier.py       # Lark推送 (文本/富文本/卡片)
│   │   ├── user_monitor.py        # 用户监控 (Twitter/雪球预留)
│   │   ├── keyword_crawler.py     # 关键词爬取 (Google/Bing News)
│   │   ├── sentiment_analyzer.py  # 情感分析 (本地+AI)
│   │   ├── ai_provider.py         # AI Provider (千问/扩展接口)
│   │   ├── scheduler.py           # 定时任务调度
│   │   └── report_generator.py    # 日报生成
│   └── templates/
│       └── index.html             # 前端单页应用 (TailwindCSS)
├── tests/                         # 单元测试
├── .env.example                   # 环境变量模板
├── requirements.txt               # Python 依赖
├── Dockerfile                     # Docker 镜像
└── docker-compose.yml             # Docker Compose 配置
```

## 🚀 快速开始

### 方式一：本地运行

**1. 克隆项目并安装依赖**
```bash
git clone https://github.com/kibenson/stock-news-lark-bot.git
cd stock-news-lark-bot
pip install -r requirements.txt
```

**2. 配置环境变量**
```bash
cp .env.example .env
# 编辑 .env，填写你的配置
```

**3. 启动应用**
```bash
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

**4. 访问管理页面**

打开浏览器访问: http://localhost:8000

### 方式二：Docker 部署（推荐）

**1. 配置环境变量**
```bash
cp .env.example .env
# 编辑 .env，填写关键配置
```

**2. 启动服务**
```bash
docker-compose up -d
```

**3. 查看日志**
```bash
docker-compose logs -f
```

## ⚙️ 配置说明

编辑 `.env` 文件，以下是关键配置项：

```env
# ===== 必填 =====

# Lark Webhook（从飞书机器人设置中获取）
LARK_WEBHOOK_URL=https://open.feishu.cn/open-apis/bot/v2/hook/你的Token

# ===== 推荐配置 =====

# 千问AI API Key（DashScope）
DASHSCOPE_API_KEY=你的DashScope API Key

# 新闻API（选填，不填则仅使用RSS源）
NEWS_API_KEY=你的NewsAPI Key
FINNHUB_API_KEY=你的Finnhub Key

# ===== 可选配置 =====

# 推送时间（每天8:00 上海时区）
PUSH_SCHEDULE_HOUR=8
PUSH_SCHEDULE_MINUTE=0
PUSH_TIMEZONE=Asia/Shanghai

# 数据库（默认SQLite，生产环境可用PostgreSQL）
DATABASE_URL=sqlite:///./stock_news.db
```

### 如何获取 Lark Webhook URL

1. 在飞书群聊中，点击右上角 **设置** → **群机器人** → **添加机器人**
2. 选择 **自定义机器人**，创建机器人
3. 复制生成的 **Webhook地址**，填入 `.env` 的 `LARK_WEBHOOK_URL`

### 如何获取 千问 API Key

1. 访问 [DashScope控制台](https://dashscope.console.aliyun.com/apiKey)
2. 创建 API Key
3. 填入 `.env` 的 `DASHSCOPE_API_KEY`

## 📡 API 文档

启动应用后访问:
- **交互式文档 (Swagger)**: http://localhost:8000/api/docs
- **ReDoc 文档**: http://localhost:8000/api/redoc

### 主要接口列表

| 接口 | 方法 | 说明 |
|------|------|------|
| `/api/stocks` | GET/POST/DELETE | 股票关注列表管理 |
| `/api/users` | GET/POST/DELETE | 用户监控管理 |
| `/api/keywords` | GET/POST/DELETE | 关键词管理 |
| `/api/news` | GET | 获取新闻列表 |
| `/api/news/fetch` | GET | 触发新闻抓取 |
| `/api/sentiment/analyze` | GET | 触发情感分析 |
| `/api/push/trigger` | POST | 手动触发推送 |
| `/api/push/history` | GET | 推送历史记录 |
| `/api/dashboard` | GET | 仪表盘统计数据 |
| `/api/ai/analyze` | POST | AI内容分析 |
| `/api/ai/status` | GET | AI服务状态 |

## 🖥️ 管理界面功能

| Tab | 功能 |
|-----|------|
| 📊 仪表盘 | 统计概览、最新情感、近期新闻、推送成功率 |
| 📈 股票关注 | 添加/删除/查看关注的股票，支持US/CN/HK市场 |
| 👤 用户监控 | 管理需要监控的社交媒体用户 |
| 🔑 关键词管理 | 配置爬取关键词，按分类管理 |
| 📰 新闻中心 | 浏览新闻，按情感/时间过滤，手动触发抓取 |
| 💬 情感分析 | 查看情感报告，触发本地/AI分析 |
| 📤 推送历史 | 查看所有推送记录及状态，手动触发推送 |
| 🤖 AI分析 | 输入文本，选择分析类型，获取AI分析结果 |

## 🤖 AI 功能说明

AI 模块采用 **Provider 模式**设计，目前默认集成 **千问(Qwen)** API：

```python
# AI 分析类型
- sentiment  # 情感分析（正面/负面/中性 + 置信度 + 原因）
- summary    # 新闻摘要（生成简洁的市场日报）
- advice     # 投资建议（含免责声明）
- custom     # 自定义Prompt分析
```

**扩展其他AI服务**（如OpenAI、Claude）：
```python
from app.services.ai_provider import ai_provider, BaseAIProvider

class OpenAIProvider(BaseAIProvider):
    def chat_completion(self, messages, **kwargs):
        # 实现 OpenAI 调用
        pass
    def is_available(self):
        return bool(your_openai_key)

# 注册并设为默认
ai_provider.register_provider("openai", OpenAIProvider(...))
ai_provider._default_provider = "openai"
```

## 📊 数据模型

| 模型 | 说明 |
|------|------|
| `WatchStock` | 关注的股票（代码/名称/市场/备注） |
| `MonitoredUser` | 监控的用户（平台/用户名/显示名） |
| `Keyword` | 关键词（词/分类/状态） |
| `NewsArticle` | 新闻文章（标题/内容/来源/情感分析） |
| `UserPost` | 用户发言（内容/平台/情感分析） |
| `PushHistory` | 推送历史（类型/状态/响应） |
| `SentimentReport` | 情感分析报告（统计/结论） |

## 🛠️ 开发指南

### 运行测试
```bash
pytest tests/ -v
```

### 本地开发（热重载）
```bash
python -m uvicorn app.main:app --reload --log-level debug
```

### 添加新的新闻源

在 `app/services/news_fetcher.py` 中：
```python
def fetch_my_source(symbol=None):
    # 实现你的新闻源抓取逻辑
    return articles_list

# 在 fetch_all_news() 中添加调用
```

### 添加新的社交平台监控

在 `app/services/user_monitor.py` 中：
```python
class WeiboMonitor(BasePlatformMonitor):
    platform_name = "weibo"
    
    def fetch_user_posts(self, username, limit=20, since=None):
        # 实现微博爬取逻辑
        return posts_list

# 注册到服务
user_monitor_service.register_monitor("weibo", WeiboMonitor())
```

## 📝 任务执行流程

每日定时任务（默认每天早上8点）执行流程：

```
1. 获取关注股票列表 & 关键词列表
      ↓
2. 抓取全球股票新闻（RSS/NewsAPI/Finnhub）
      ↓
3. 爬取关键词相关资讯
      ↓
4. 抓取监控用户最新发言
      ↓
5. 情感分析（本地分析 or AI分析）
      ↓
6. AI生成新闻摘要（如已配置千问API）
      ↓
7. 生成每日报告
      ↓
8. 推送到 Lark 群（所有配置的Webhook）
      ↓
9. 记录推送历史
```

## ⚠️ 免责声明

本项目提供的 AI 投资建议功能仅供参考，**不构成任何投资建议**。投资有风险，入市需谨慎。请自行判断投资决策。

## 📄 License

MIT License
