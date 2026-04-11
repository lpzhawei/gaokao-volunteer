"""
数据库管理模块
负责SQLite数据库的初始化、表结构创建和基础CRUD操作
"""
import sqlite3
import sys
import os
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

# 获取应用根目录（打包后或开发环境）
# PyInstaller onedir 模式：datas 声明的文件都在 _internal/ 子目录中
if getattr(sys, 'frozen', False):
    BASE_DIR = Path(sys.executable).parent / "_internal"
else:
    BASE_DIR = Path(__file__).parent.parent.parent

# 数据库路径（只使用本目录下的数据库）
DB_PATH = BASE_DIR / "data" / "db" / "gaokao.db"

# 回退路径（用于错误提示）
FALLBACK_DB_PATH = DB_PATH

# 资源文件路径（图标等）
RESOURCES_DIR = BASE_DIR / "resources"


def _get_active_db_path():
    """获取可用的数据库路径"""
    if DB_PATH.exists():
        return DB_PATH
    return None


def init_db():
    """初始化数据库（检查连接）"""
    conn = get_connection()
    conn.close()


def get_connection():
    """获取数据库连接（只使用本目录数据库）"""
    if not DB_PATH.exists():
        logger.error("数据库文件不存在：%s", DB_PATH)
        raise FileNotFoundError(f"数据库文件不存在：{DB_PATH}")
    
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def _clean_lock_files():
    """清理 SQLite 残留锁文件（WAL/SHM）"""
    lock_files = [
        DB_PATH.with_suffix(".db-wal"),
        DB_PATH.with_suffix(".db-shm"),
        DB_PATH.with_suffix(".db-journal"),
    ]
    for lf in lock_files:
        if lf.exists():
            try:
                lf.unlink()
                logger.info("已清理残留锁文件：%s", lf)
            except Exception as e:
                logger.warning("清理锁文件失败：%s - %s", lf, e)


def init_database():
    """初始化数据库连接"""
    _clean_lock_files()
    return get_connection()


def close_connection(conn):
    """关闭数据库连接"""
    if conn:
        conn.close()
        _clean_lock_files()


def get_table_columns(table_name: str) -> list[str]:
    """获取表的列名"""
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(f"PRAGMA table_info({table_name})")
        return [row[1] for row in cur.fetchall()]
    finally:
        conn.close()


def execute_many(sql: str, params: list):
    """批量执行SQL"""
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.executemany(sql, params)
        conn.commit()
    finally:
        conn.close()


def execute_one(sql: str, params: tuple = ()):
    """执行SQL并返回一行"""
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(sql, params)
        return cur.fetchone()
    finally:
        conn.close()


def execute_all(sql: str, params: tuple = ()):
    """执行SQL并返回所有行"""
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(sql, params)
        return cur.fetchall()
    finally:
        conn.close()


def execute_write(sql: str, params: tuple = ()):
    """执行写操作SQL"""
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(sql, params)
        conn.commit()
    finally:
        conn.close()