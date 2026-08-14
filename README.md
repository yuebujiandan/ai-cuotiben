# Recall AI 智能错题本 · 全栈工程

面向学生的 AI 智能错题管理平台：拍照/截图 OCR 录入 → AI 归类诊断 → 错题管理 → 一键复习 → AI 答疑 → 数据看板 → PDF 导出。

## ✨ 功能特性

- **多通道录入**：拍照/截图 OCR 自动识别（支持 LaTeX 公式）；手动输入秒级入库（0.4s 返回，AI 后台异步解析）
- **多题拆分**：整张试卷自动按「第 N 题」拆分，勾选后逐题批量入库
- **AI 归类诊断**：自动识别 学科 / 知识点 / 正确答案，并给出错因诊断与解题步骤
- **3 级讲解**：对话中按需生成 提示(💡) / 思路(🧭) / 详解(📖)，可一键「引用到错题本」
- **一键复习**：SM-2 简化调度（答对×2.5、连续 2 次答对→已掌握、答错回未掌握），对/错/跳过三键作答
- **AI 流式答疑**：SSE 打字机效果，向量检索同类题增强上下文（RAG）
- **数据看板**：掌握率、状态三色占比、近十天新增/复习趋势、今日复习数、连续打卡
- **数据管理**：错题本（持久化容器）、收藏、搜索、状态筛选、PDF/Markdown 导出（范围/内容可选）
- **安全与限额**：输入/输出敏感词过滤、每日 AI 对话 50 次限额、空内容/悬空外键数据校验

## 技术栈

| 层 | 技术 |
|---|---|
| 前端 | Vue 3 + TypeScript + Vite + Tailwind CSS |
| 后端 | FastAPI + Uvicorn |
| 数据库 | SQLite（SQLAlchemy ORM，已开启外键约束） |
| 向量数据库 | ChromaDB（同类题语义检索） |
| 大模型 | 硅基流动 SiliconFlow · THUDM/GLM-Z1-9B-0414（归类 / 错因诊断 / 3级讲解 / 流式答疑） |
| OCR | 硅基流动 DeepSeek-OCR（拍照/截图录入，视觉模型，免费） |
| PDF | ReportLab（错题本导出） |

## 目录结构

```
recall-app/
├── frontend/                       # Vue 3 前端
│   ├── src/
│   │   ├── api/                    # axios 接口封装（questions/chat/dashboard/review）
│   │   ├── components/             # 组件（QuestionCard/ChatWindow/UploadModal/DetailModal/ExportModal…）
│   │   ├── router/                 # Vue Router（/home /bank /review /ai /dashboard /help）
│   │   ├── types/                  # TypeScript 类型定义
│   │   └── views/                  # 页面（Home/Bank/Review/AiTutor/Dashboard/Help）
│   ├── package.json
│   └── vite.config.ts              # 已配置 /api 代理 → localhost:8000
└── backend/                        # FastAPI 后端
    ├── main.py                     # 应用入口
    ├── config.py                   # 配置读取（环境变量/.env）
    ├── models.py                   # SQLAlchemy 模型（questions/notebooks/conversations/messages/review_records/daily_usage）
    ├── schemas.py                  # Pydantic 请求/响应模型
    ├── database.py                 # SQLite 连接 + 自动建表/增量迁移
    ├── requirements.txt
    ├── routers/                    # 路由（questions/chat/dashboard/notebooks/review）
    └── services/                   # 服务（llm/ocr/vector/pdf/safety）
```

## 快速开始

### 1. 后端

```bash
cd backend
python -m venv venv
# Windows: venv\Scripts\activate   |   macOS/Linux: source venv/bin/activate
pip install -r requirements.txt

# 配置硅基流动 API Key（AI 功能必需）
cp .env.example .env   # 然后编辑 .env 填入 Key

uvicorn main:app --reload --port 8000
```

### 2. 前端

```bash
cd frontend
npm install
npm run dev
```

浏览器打开 **http://localhost:5173**（Vite 已将 `/api` 代理到 8000 端口）。

### 3. 环境变量（backend/.env）

```ini
# 必填：硅基流动 API Key（与 OCR 共用，DeepSeek-OCR 视觉模型免费）
RECALL_SILICONFLOW_API_KEY=sk-xxxx

# 可选：覆盖默认模型与端点
RECALL_SILICONFLOW_MODEL=THUDM/GLM-Z1-9B-0414
RECALL_SILICONFLOW_BASE_URL=https://api.siliconflow.cn/v1

# 可选：CORS 允许来源（逗号分隔），默认允许本地开发端口
# CORS_ORIGINS=http://localhost:5173
```

> 未配置 Key 时应用仍可启动：OCR/AI 解析返回降级提示，其余功能（录入/管理/复习/导出）正常可用。

## API 概览（前缀 `/api`）

| 方法 | 路径 | 说明 |
|---|---|---|
| GET | `/questions` | 错题列表（category/status/keyword/notebook_id 筛选） |
| POST | `/questions` | 创建错题（秒级返回，AI 解析后台异步） |
| GET/PUT/DELETE | `/questions/{id}` | 详情 / 更新（状态枚举校验）/ 删除（级联清理复习记录） |
| POST | `/questions/{id}/analyze` | 重新 AI 解析 |
| POST | `/questions/upload` | 图片 OCR + 入库（一步完成） |
| POST | `/questions/upload/ocr` | 仅 OCR 识别（返回 text + 按「第N题」拆分片段，供前端预览/勾选） |
| GET | `/questions/categories` | 学科/收藏/复习计划计数 |
| GET/POST/DELETE | `/notebooks` | 错题本 CRUD |
| GET | `/review/queue` | 今日复习队列（未掌握优先，上限 30） |
| POST | `/review/{id}/result` | 提交作答结果（correct/wrong/skip） |
| GET/POST | `/chat/conversations` `/chat/stream` | 会话列表 / 流式对话（SSE，限额 50 次/天） |
| POST | `/chat/explain` | 3 级讲解（hint/approach/solution） |
| GET | `/dashboard/stats` `/daily` | 看板统计 / 近十天趋势（基于真实复习记录） |
| GET | `/dashboard/export` | 导出 PDF（支持 subject/status/keyword/notebook_id 筛选） |
| GET | `/health` | 健康检查 |

## 核心流程

```
拍照/截图 ──DeepSeek-OCR──> 题目文本（自动拆分多题）
  └─> 手动输入 ──> 秒级入库
错题入库 ──> SQLite(关系数据) ──> ChromaDB(向量索引) ──> AI 后台归类 {学科, 知识点, 错因, 答案}

一键复习 ──> 复习队列(SM-2 简化) ──> 对/错/跳过 ──> 连续2次答对→已掌握

AI 答疑 ──向量检索同类题──> GLM-Z1-9B 流式回答 ──SSE──> 打字机
3级讲解 ──> 提示/思路/详解 ──> 可引用到错题本

数据看板 ──> 真实复习记录(review_records) ──> 今日复习/连续打卡/三色占比
导出 ──> PDF / Markdown（可选范围与内容）
```

## 复习调度（SM-2 简化）

| 作答 | 效果 |
|---|---|
| 答对 (correct) | 复习次数+1，连续答对+1；连续 2 次 → **已掌握(green)**，否则待复习(amber) |
| 答错 (wrong) | 复习次数+1，连续答对清零，回到**未掌握(red)** |
| 跳过 (skip) | 仅记录，状态不变 |

所有作答写入 `review_records` 表，作为看板「今日复习数 / 连续打卡 / 每日复习趋势」的真实数据源。

## 已知限制与注意事项

- **AI 响应时间波动**：免费额度下 OCR/AI 解析响应 0~90s 波动，分段函数等复杂题型易超时；已做 60s 超时 + 失败提示 +「重新 AI 分析」兜底
- **AI 对话限额**：每日 50 次（`routers/chat.py` 中 `DAILY_CHAT_LIMIT` 可调），超限返回 403
- **内容安全**：内置教育场景敏感词表（`services/safety.py`），命中返回固定提示不生成内容
- **单用户**：无账号体系，数据存储在服务端 SQLite（`backend/recall.db`）
- **搜索引擎**：全文检索基于 LIKE 模糊匹配，题目量大时建议换 FTS5 或全文索引

## 可选优化（Roadmap）

- [ ] 知识图谱（ECharts 学科→知识点聚合）
- [ ] AI 薄弱点推荐（看板 TOP3 建议）
- [ ] 数据备份/恢复（JSON 导出导入）
- [ ] AI 变体题生成（复习/答疑中同知识点变式）
- [ ] 用户体系 + JWT + 多设备同步
- [ ] ChromaDB embedding 换专用模型（如 BGE）
- [ ] 前端接入 Pinia 状态管理
