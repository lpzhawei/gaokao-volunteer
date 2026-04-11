"""
pytest 共享 fixtures
提供内存 SQLite 数据库、mock profile 等
"""
import sys
import os
import sqlite3
import pytest

# 将项目根目录加入 sys.path，使 src 包可以被导入
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)


@pytest.fixture
def db_conn():
    """创建内存 SQLite 数据库并填充测试数据"""
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    _init_test_db(conn)
    yield conn
    conn.close()


@pytest.fixture
def mock_profile():
    """创建一个标准测试用 StudentProfile"""
    from src.core.models import StudentProfile
    return StudentProfile(
        estimated_score=580,
        subject_first="物理",
        subject_elective1="化学",
        subject_elective2="生物",
        color_vision="正常",
        naked_eye_vision="5.0",
        gender="男",
        height_cm=175,
        weight_kg=65,
        extra_score=0,
        pref_majors=["计算机/信息技术"],
        pref_provinces=["北京", "河北"],
        accept_private=True,
        accept_joint=False,
        rank_2026=74000,
        rank_offset_neg=0,
        rank_offset_pos=0,
    )


def _init_test_db(conn):
    """初始化测试数据库表结构和数据"""
    # ── 创建表 ─────────────────────────────────────
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS score_rank (
            year INTEGER NOT NULL,
            subject_type TEXT NOT NULL,
            score INTEGER NOT NULL,
            rank_cumulative INTEGER NOT NULL,
            PRIMARY KEY (year, subject_type, score)
        );

        CREATE TABLE IF NOT EXISTS admission_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            year INTEGER NOT NULL,
            college_code TEXT,
            college_name TEXT,
            major_name TEXT,
            subject_type TEXT,
            batch TEXT,
            province TEXT,
            min_score REAL,
            max_score REAL,
            avg_score REAL,
            min_rank INTEGER,
            plan_count INTEGER,
            actual_count INTEGER,
            body_restrict TEXT,
            elective_req TEXT,
            college_nature TEXT
        );

        CREATE TABLE IF NOT EXISTS colleges (
            code TEXT PRIMARY KEY,
            name TEXT,
            province TEXT,
            nature TEXT,
            tier TEXT
        );
    """)

    # ── 一分一段测试数据（物理类 2025年）────────────
    score_rank_data = [
        # (year, subject_type, score, rank_cumulative)
        (2025, "物理", 700, 100),
        (2025, "物理", 690, 300),
        (2025, "物理", 680, 800),
        (2025, "物理", 670, 2000),
        (2025, "物理", 660, 5000),
        (2025, "物理", 650, 10000),
        (2025, "物理", 640, 18000),
        (2025, "物理", 630, 30000),
        (2025, "物理", 620, 45000),
        (2025, "物理", 610, 60000),
        (2025, "物理", 600, 75000),
        (2025, "物理", 590, 90000),
        (2025, "物理", 580, 110000),
        (2025, "物理", 570, 130000),
        (2025, "物理", 560, 150000),
        (2025, "物理", 550, 170000),
        (2025, "物理", 500, 250000),
        (2025, "物理", 450, 300000),
        # 历史类 2025
        (2025, "历史", 650, 100),
        (2025, "历史", 640, 300),
        (2025, "历史", 600, 3000),
        (2025, "历史", 550, 10000),
    ]
    conn.executemany(
        "INSERT INTO score_rank (year, subject_type, score, rank_cumulative) VALUES (?, ?, ?, ?)",
        score_rank_data
    )

    # ── 投档数据测试数据 ──────────────────────────
    admission_data = [
        # (year, college_code, college_name, major_name, subject_type, batch, province, min_score, min_rank, body_restrict, elective_req, college_nature, plan_count, avg_score)
        # 冲刺专业（位次 < 74000）
        (2025, "1001", "北京大学", "计算机科学与技术", "物理", "本科批", "北京", 680, 800, "", "不限", "公办", 5, 685),
        (2025, "1002", "清华大学", "软件工程", "物理", "本科批", "北京", 678, 900, "", "物理,化学", "公办", 3, 682),
        (2025, "1003", "北京理工大学", "人工智能", "物理", "本科批", "北京", 650, 10000, "", "不限", "公办", 10, 655),
        (2025, "1004", "北京邮电大学", "计算机科学与技术", "物理", "本科批", "北京", 635, 20000, "", "不限", "公办", 8, 640),
        (2025, "1005", "河北工业大学", "计算机科学与技术", "物理", "本科批", "河北", 615, 40000, "", "不限", "公办", 20, 618),
        (2025, "1006", "燕山大学", "软件工程", "物理", "本科批", "河北", 605, 55000, "", "不限", "公办", 15, 608),
        (2025, "1007", "河北大学", "人工智能", "物理", "本科批", "河北", 598, 65000, "", "不限", "公办", 10, 600),
        # 锚点附近（位次 ≈ 74000）
        (2025, "1008", "河北师范大学", "计算机科学与技术", "物理", "本科批", "河北", 593, 72000, "", "不限", "公办", 30, 596),
        (2025, "1009", "石家庄铁道大学", "软件工程", "物理", "本科批", "河北", 592, 75000, "", "不限", "公办", 25, 595),
        # 保底专业（位次 > 74000）
        (2025, "1010", "河北科技大学", "计算机科学与技术", "物理", "本科批", "河北", 585, 85000, "", "不限", "公办", 30, 588),
        (2025, "1011", "河北工程大学", "软件工程", "物理", "本科批", "河北", 575, 100000, "", "不限", "公办", 20, 578),
        (2025, "1012", "华北理工大学", "人工智能", "物理", "本科批", "河北", 565, 115000, "", "不限", "公办", 25, 568),
        # 民办院校（用于过滤测试）
        (2025, "2001", "河北传媒学院", "计算机科学与技术", "物理", "本科批", "河北", 500, 200000, "", "不限", "民办", 50, 505),
        # 中外合作（用于过滤测试）
        (2025, "1001", "北京大学", "计算机科学与技术(中外合作)", "物理", "本科批", "北京", 650, 12000, "", "不限", "中外合作", 2, 655),
        # 体检受限专业
        (2025, "1013", "中国民航大学", "飞行技术", "物理", "本科批", "天津", 600, 60000, "色盲不录;色弱不录", "不限", "公办", 5, 605),
        (2025, "1014", "大连海事大学", "航海技术", "物理", "本科批", "辽宁", 570, 120000, "", "不限", "公办", 10, 573),
        # 公安类
        (2025, "1015", "中国人民公安大学", "刑事科学技术", "物理", "本科批", "北京", 620, 45000, "", "化学", "公办", 5, 623),
        # 选科要求严格
        (2025, "1016", "某大学", "临床医学", "物理", "本科批", "北京", 640, 25000, "", "化学和生物", "公办", 10, 645),
        # 非偏好省份
        (2025, "1017", "浙江大学", "计算机科学与技术", "物理", "本科批", "浙江", 660, 5000, "", "不限", "公办", 3, 665),
        # 非偏好专业
        (2025, "1018", "北京师范大学", "学前教育", "物理", "本科批", "北京", 610, 60000, "", "不限", "公办", 5, 613),
        # 无位次数据（需要从分数反查）
        (2025, "1019", "某学院", "数据科学", "物理", "本科批", "河北", 595, None, "", "不限", "公办", 10, 598),
    ]
    conn.executemany(
        """INSERT INTO admission_data 
           (year, college_code, college_name, major_name, subject_type, batch, province, 
            min_score, min_rank, body_restrict, elective_req, college_nature, plan_count, avg_score)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        admission_data
    )

    conn.commit()
