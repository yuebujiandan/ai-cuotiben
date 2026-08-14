# Recall AI 智能错题本 · 全栈工程

面向学生的 AI 智能错题管理平台：拍照/截图 OCR 录入 → AI 归类诊断 → 错题管理 → AI 答疑 → 数据看板 → PDF 导出。

## 技术栈

| 层 | 技术 |
|---|---|
| 前端 | Vue 3 + TypeScript + Vite + Tailwind CSS（组件化） |
| 后端 | FastAPI + Uvicorn |
| 数据库 | SQLite（SQLAlchemy ORM） |
| 向量数据库 | ChromaDB（同类题语义检索） |
| 大模型 | 硅基流动 SiliconFlow · THUDM/GLM-Z1-9B-0414（归类 / 错因诊断 / 流式答疑） |
| OCR | 硅基流动 DeepSeek-OCR（拍照/截图录入，视觉模型，免费） |
| PDF | ReportLab（错题本导出） |

## 目录结构

```
recall-app/
├── frontend/               # Vue 3 前端
│   ├── src/
│   │   ├── api/            # axios 接口封装（questions/chat/dashboard）
│   │   ├── components/     # 组件化 UI（AppHeader/QuestionCard/ChatWindow/UploadModal…）
│   │   ├── router/         # Vue Router 路由
│   │   ├── types/          # TypeScript 类型定义
│   │   └── views/          # 页面（BankView/AiTutorView/DashboardView/HelpView）
│   └── package.json
└── backend/                # FastAPI 后端
    ├── main.py             # 应用入口
    ├── models.py           # SQLAlchemy 模型（questions/conversations/messages）
    ├── schemas.py          # Pydantic 模型
    ├── routers/            # 路由（questions/chat/dashboard）
    └── services/           # 服务（llm/ocr/vector/pdf）
```

## 快速启动

### 1. 后端

```bash
cd backend
python -m venv venv
# Windows: venv\Scripts\activate   |  macOS/Linux: source venv/bin/activate
pip install -r requirements.txt

# 配置硅基流动 API Key（可选，配置后 AI 功能可用）
# 方式一：环境变量
export RECALL_SILICONFLOW_API_KEY=sk-xxxx
# 方式二：backend/.env 文件
# RECALL_SILICONFLOW_API_KEY=sk-xxxx
# （可选）覆盖默认模型与端点：
# RECALL_SILICONFLOW_MODEL=THUDM/GLM-Z1-9B-0414
# RECALL_SILICONFLOW_BASE_URL=https://api.siliconflow.cn/v1

uvicorn main:app --reload --port 8000
```

> 注：OCR 使用硅基流动 DeepSeek-OCR 视觉模型（免费），与 LLM 共用同一个 API Key，无需本地安装任何 OCR 依赖。

### 2. 前端

```bash
cd frontend
npm install
npm run dev
```

浏览器打开 http://localhost:5173，Vite 已配置 `/api` 代理到 8000 端口。

## 核心流程

```
拍照/截图 ──DeepSeek-OCR──> 题目文本 ──GLM-Z1-9B──> {学科, 知识点, 错因分析, 正确答案}
                                                            │
错题入库 ──> SQLite(关系数据) ──> ChromaDB(向量索引)
                                                            │
AI 答疑 ──向量检索同类题──> GLM-Z1-9B 流式回答 ──SSE──> 前端打字机
导出复习卷 ──ReportLab──> PDF
```

## 可选优化

- 做题记录独立建表（当前看板"每日做题量"用新增错题数近似）
- 用户体系 + JWT（当前单用户）
- ChromaDB embedding 换专用模型（如 BGE）
- 前端接入 Pinia 状态管理（当前组件内 state 已够用）
