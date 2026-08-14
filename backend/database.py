"""SQLite 数据库连接与会话管理（SQLAlchemy ORM）。"""
from sqlalchemy import create_engine, event
from sqlalchemy.orm import declarative_base, sessionmaker

from config import settings

engine = create_engine(
    settings.database_url,
    connect_args={"check_same_thread": False},
)


@event.listens_for(engine, "connect")
def _enable_sqlite_foreign_keys(dbapi_connection, connection_record):
    """SQLite 默认不校验外键，这里显式开启，防止悬空 notebook_id 等孤儿数据。"""
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base = declarative_base()


def get_db():
    """FastAPI 依赖：每个请求一个数据库会话。"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """建表（首次启动时调用），并对既有表做增量迁移。"""
    import models  # noqa: F401  确保模型注册
    Base.metadata.create_all(bind=engine)
    _migrate_columns()


def _migrate_columns():
    """对已有表做向后兼容的增量迁移（create_all 不会给旧表加列）。"""
    from sqlalchemy import text

    # (表名, 列名, 建列 SQL)
    MIGRATIONS = [
        ("questions", "notebook_id", "ALTER TABLE questions ADD COLUMN notebook_id INTEGER"),
        ("questions", "correct_streak", "ALTER TABLE questions ADD COLUMN correct_streak INTEGER DEFAULT 0"),
    ]
    with engine.connect() as conn:
        for table, column, ddl in MIGRATIONS:
            try:
                rows = conn.execute(text(f"PRAGMA table_info({table})")).fetchall()
                cols = {r[1] for r in rows}
                if column not in cols:
                    conn.execute(text(ddl))
                    conn.commit()
                    print(f"数据库迁移：{table}.{column} 已添加")
            except Exception as e:  # 迁移失败不阻塞启动
                print(f"数据库迁移警告（可忽略）：{table}.{column} {e}")

