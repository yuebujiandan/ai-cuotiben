"""内容安全过滤（教育场景敏感词 + 输入输出双端检查）。

命中敏感词时返回固定提示，不生成内容。列表为教育产品常见风险词，
实际生产可接入专业内容安全服务（如腾讯云内容安全 / 百度内容审核）。
"""
import logging

logger = logging.getLogger(__name__)

BLOCKED_WORDS = [
    # 色情/低俗
    "色情", "黄色网站", "黄片", "淫秽", "裸聊", "约炮",
    # 暴力/恐怖
    "杀人", "绑架", "恐怖袭击", "炸弹制作", "枪支交易", "自杀方法", "自残",
    # 违法/作弊
    "代考", "代写论文", "作弊神器", "办假证", "洗钱", "诈骗话术", "赌博平台",
    "翻墙软件", "刷单兼职",
    # 毒品
    "毒品", "制毒", "冰毒", "摇头丸",
    # 政治敏感（兜底）
    "法轮功", "藏独", "台独", "港独",
]

_FILTERED_PROMPT = "该问题不在我可回答范围内。"


def check(text: str) -> bool:
    """返回 True 表示命中敏感词，应拦截。"""
    if not text:
        return False
    for w in BLOCKED_WORDS:
        if w in text:
            logger.info("内容安全拦截：命中词 %s", w)
            return True
    return False


def filtered_message() -> str:
    return _FILTERED_PROMPT
