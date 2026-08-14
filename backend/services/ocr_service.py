"""OCR 文字识别服务（硅基流动，首选 + 竞速兜底）。

策略：
- 首选 PaddlePaddle/PaddleOCR-VL-1.5（专业 OCR，实测最快最准，~1.2s）
- 首选失败（超时 / 限流 / 报错）时，并发竞速其余视觉模型取最先成功者：
  - deepseek-ai/DeepSeek-OCR（文档/公式识别强，实测 ~1.3s）

说明：Qwen/Qwen3.5-4B 实测 180s+ 且输出错乱，已从竞速列表移除。
免费额度下并发会触发节流，因此"先单发最快模型、失败再竞速兜底"比"三模型同时并发"更稳定更快。
"""
import base64
import logging
import os
from concurrent.futures import ThreadPoolExecutor, as_completed

from openai import OpenAI

from config import settings

logger = logging.getLogger(__name__)

_client: OpenAI | None = None

# 首选模型：单发，追求稳定低延迟
OCR_PRIMARY = "PaddlePaddle/PaddleOCR-VL-1.5"
# 兜底竞速模型：首选失败时才并发调用
OCR_FALLBACKS = [
    "deepseek-ai/DeepSeek-OCR",
]

OCR_MAX_TOKENS = 4096
OCR_TIMEOUT = 90
# 单张图片大小上限（10MB），超过则提示压缩
MAX_IMAGE_BYTES = 10 * 1024 * 1024


def _get_client() -> OpenAI:
    global _client
    if _client is None:
        _client = OpenAI(
            api_key=settings.siliconflow_api_key,
            base_url=settings.siliconflow_base_url,
            timeout=OCR_TIMEOUT,
        )
    return _client


def _is_dummy_key() -> bool:
    """检测未配置的占位 key，避免无效网络调用。"""
    return not settings.siliconflow_api_key or settings.siliconflow_api_key.startswith("sk-xxxx")


def _image_to_data_url(image_path: str) -> str:
    """读取图片为 base64 data URL。"""
    with open(image_path, "rb") as f:
        b64 = base64.b64encode(f.read()).decode("utf-8")
    ext = os.path.splitext(image_path)[1].lstrip(".").lower() or "png"
    if ext == "jpg":
        ext = "jpeg"
    return f"data:image/{ext};base64,{b64}"


def _ocr_single(model: str, data_url: str) -> str:
    """调用单个模型识别，成功返回文本，失败抛异常。"""
    resp = _get_client().chat.completions.create(
        model=model,
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "image_url", "image_url": {"url": data_url}},
                    {
                        "type": "text",
                        "text": "OCR this image. Output only the recognized text in original order, keep line breaks.",
                    },
                ],
            }
        ],
        temperature=0.0,
        max_tokens=OCR_MAX_TOKENS,
        stream=False,
    )
    text = resp.choices[0].message.content or ""
    text = text.strip()
    if not text:
        raise ValueError(f"{model} 返回空文本")
    return text


class OcrError(Exception):
    """OCR 识别失败（message 为用户可读信息，不含内部细节）。"""


def ocr_image(image_path: str) -> str:
    """先单发首选模型，失败再并发竞速兜底模型。返回识别文本。
    全部失败时抛出 OcrError（用户友好文案），由路由层转为 502，绝不返回错误文本当识别结果。
    """
    if _is_dummy_key():
        raise OcrError("OCR 服务未配置：请在 backend/.env 中设置 RECALL_SILICONFLOW_API_KEY 后重启")

    size = os.path.getsize(image_path)
    if size > MAX_IMAGE_BYTES:
        raise OcrError("图片过大（超过 10MB），请压缩后重试")

    data_url = _image_to_data_url(image_path)
    errors: list[str] = []

    # 1) 首选模型单发：免费档下单发比并发更稳更快（规避并发节流）
    try:
        text = _ocr_single(OCR_PRIMARY, data_url)
        logger.info("OCR 命中首选模型：%s", OCR_PRIMARY)
        return text
    except Exception as e:
        errors.append(f"{OCR_PRIMARY}: {e}")
        logger.warning("OCR 首选 %s 失败：%s，转竞速兜底", OCR_PRIMARY, e)

    # 2) 兜底：并发竞速其余模型，谁先成功用谁
    if OCR_FALLBACKS:
        with ThreadPoolExecutor(max_workers=len(OCR_FALLBACKS)) as pool:
            futures = {pool.submit(_ocr_single, m, data_url): m for m in OCR_FALLBACKS}
            for fut in as_completed(futures):
                model = futures[fut]
                try:
                    text = fut.result()
                    logger.info("OCR 兜底命中：%s", model)
                    return text
                except Exception as e:
                    errors.append(f"{model}: {e}")
                    logger.warning("OCR 兜底 %s 失败：%s", model, e)

    # 全部失败：只记录内部细节到日志，抛用户友好异常
    logger.error("OCR 全部模型失败：%s", "；".join(errors[-2:]))
    raise OcrError("OCR 识别失败，请重试或改用手动输入")
