"""Recall 后端配置中心。
通过环境变量覆盖，全部提供开发默认值，方便本地直接启动。
"""
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # 硅基流动 SiliconFlow API（https://cloud.siliconflow.cn）
    siliconflow_api_key: str = "sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
    siliconflow_base_url: str = "https://api.siliconflow.cn/v1"
    siliconflow_model: str = "deepseek-ai/DeepSeek-V4-Flash"

    # SQLite 数据库
    database_url: str = "sqlite:///./recall.db"

    # ChromaDB 持久化目录
    chroma_dir: str = "./chroma_data"
    chroma_collection: str = "recall_questions"

    # CORS
    cors_origins: list[str] = ["http://localhost:5173"]

    class Config:
        env_file = ".env"
        env_prefix = "RECALL_"


settings = Settings()
