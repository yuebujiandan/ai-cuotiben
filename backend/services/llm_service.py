"""硅基流动（SiliconFlow）大模型服务：错因诊断、知识点归类、AI 对话讲解。

模型：deepseek-ai/DeepSeek-V4-Flash（经硅基流动 OpenAI 兼容端点调用）。

适配要点：
- 保留提示词引导 + 容错 JSON 提取（对任意模型都稳健）
- 流式响应兼容 reasoning_content（若模型带思考过程则过滤，只输出正文）
- AI 服务不可用时按错误类型降级：未配置 / 认证失败 / 限流 / 超时 / 网络错误，分别提示
"""
import json
import logging
import re

from openai import OpenAI
from openai import APITimeoutError, AuthenticationError, RateLimitError, APIConnectionError

from config import settings

logger = logging.getLogger(__name__)

_client: OpenAI | None = None

# 单次 AI 调用超时（秒）。免费额度高负载下可能 2 分钟+，但为给用户及时反馈，
# 60s 超时即视为失败，_run_ai_analysis 会把占位文本改为"AI 解析失败"提示。
LLM_TIMEOUT = 60
LLM_MAX_TOKENS = 800


def _get_client() -> OpenAI:
    global _client
    if _client is None:
        _client = OpenAI(
            api_key=settings.siliconflow_api_key,
            base_url=settings.siliconflow_base_url,
            timeout=LLM_TIMEOUT,
            max_retries=1,
        )
    return _client


def _is_dummy_key() -> bool:
    """检测未配置的占位 key，避免无效网络调用。"""
    return not settings.siliconflow_api_key or settings.siliconflow_api_key.startswith("sk-xxxx")


def _degrade_message(e: Exception) -> str:
    """按错误类型返回面向用户的降级提示。"""
    if isinstance(e, AuthenticationError):
        return "（AI 服务认证失败：API Key 无效或已过期，请在 backend/.env 中检查 RECALL_SILICONFLOW_API_KEY）"
    if isinstance(e, RateLimitError):
        return "（AI 服务限流：请求过于频繁，请稍后再试）"
    if isinstance(e, APITimeoutError):
        return "（AI 服务响应超时：当前网络较慢或模型繁忙，请稍后再试）"
    if isinstance(e, APIConnectionError):
        return "（AI 服务网络连接失败：请检查网络或稍后再试）"
    return "（AI 服务暂时不可用，请稍后再试，或检查 API Key 配置。）"


SYSTEM_PROMPT = (
    "你是一名亲切耐心的AI学伴，面向中学生讲解错题。"
    "回答使用简体中文，结构清晰、步骤明确，最后给出一个可操作的小建议。"
)


def _extract_json(raw: str) -> dict:
    """从模型输出中健壮地提取 JSON 对象。
    推理模型可能输出多余说明文字，这里定位第一个 { 到最后一个 } 截取。
    """
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        m = re.search(r"\{.*\}", raw, re.S)
        if m:
            try:
                return json.loads(m.group(0))
            except json.JSONDecodeError:
                pass
        return {}


def analyze_question(content: str, my_answer: str | None = None) -> dict:
    """AI 解析错题：返回 {subject, knowledge_point, analysis, correct_answer}。
    AI 不可用时返回空字典（调用方按默认值入库）。
    """
    if _is_dummy_key():
        return {}
    user = (
        f"题目：{content}\n"
        + (f"我的答案：{my_answer}\n" if my_answer else "")
        + '请只输出一个 JSON 对象，不要输出其他文字，格式为：'
        + '{"subject": "学科", "knowledge_point": "知识点", '
        + '"analysis": "错因诊断与解题步骤", "correct_answer": "正确答案"}'
    )
    try:
        resp = _get_client().chat.completions.create(
            model=settings.siliconflow_model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user},
            ],
            temperature=0.4,
            max_tokens=LLM_MAX_TOKENS,  # 限制输出，防止推理模型无限思考拖慢接口
        )
        raw = resp.choices[0].message.content or ""
        return _extract_json(raw)
    except Exception as e:
        logger.warning("硅基流动解析失败，降级处理：%s", e)
        return {}


EXPLAIN_PROMPTS = {
    "hint": "针对下面的题目，只给出一条解题提示（不直接给答案、不列步骤），控制在 50-120 字，用简体中文。",
    "approach": "针对下面的题目，给出解题思路和关键步骤，控制在 80-160 字，用简体中文。",
    "solution": "针对下面的题目，给出完整详细的解答过程（含最终答案），控制在 150-350 字，用简体中文。",
}


def explain(question: str, level: str) -> str:
    """3 级讲解：按等级生成 提示/思路/详解。失败返回降级提示。"""
    if _is_dummy_key():
        return "（AI 服务未配置）请在 backend/.env 中设置 RECALL_SILICONFLOW_API_KEY 后重启后端。"
    user = f"题目：{question}\n\n{EXPLAIN_PROMPTS.get(level, EXPLAIN_PROMPTS['hint'])}"
    try:
        resp = _get_client().chat.completions.create(
            model=settings.siliconflow_model,
            messages=[
                {"role": "system", "content": "你是一名亲切耐心的AI学伴，面向中学生讲解错题，使用简体中文。"},
                {"role": "user", "content": user},
            ],
            temperature=0.4,
            max_tokens=600,
        )
        text = (resp.choices[0].message.content or "").strip()
        return text or "（AI 未返回内容，请稍后再试）"
    except Exception as e:
        logger.warning("3 级讲解生成失败：%s", e)
        return _degrade_message(e)


def chat_stream(question: str, context: str = "", history: list | None = None):
    """流式对话（生成器，逐段 yield 正文文本）。
    过滤 reasoning_content 思考过程，仅输出最终回答。
    history: 本会话历史，元素为 (role, content) 元组，用于多轮连贯对话。
    """
    if _is_dummy_key():
        yield "（AI 服务未配置）请在 backend/.env 中设置 RECALL_SILICONFLOW_API_KEY 后重启后端，即可获得真实的 AI 讲解。"
        return
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    for role, content in (history or []):
        if role in ("user", "assistant"):
            messages.append({"role": role, "content": content})
    if context:
        messages.append({"role": "system", "content": f"当前上下文：{context}"})
    messages.append({"role": "user", "content": question})

    try:
        stream = _get_client().chat.completions.create(
            model=settings.siliconflow_model,
            messages=messages,
            stream=True,
            temperature=0.6,
            max_tokens=LLM_MAX_TOKENS,
        )
        for chunk in stream:
            if not chunk.choices:
                continue
            delta = chunk.choices[0].delta
            # 推理模型流式返回含 reasoning_content，只取 content 正文
            text = getattr(delta, "content", None)
            if text:
                yield text
    except Exception as e:
        logger.warning("硅基流动流式对话失败：%s", e)
        yield _degrade_message(e)
