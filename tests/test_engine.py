"""
集成测试 —— 使用内存数据库测试引擎 generate() 主流程
通过 mock 数据库连接，使用 MagicMock 包装阻止 close
"""
import sqlite3
import pytest
from unittest.mock import patch, MagicMock, PropertyMock
from src.core.models import StudentProfile
from src.core.engine import RecommendEngine
from tests.conftest import _init_test_db


@pytest.fixture
def mem_db():
    """创建内存数据库并初始化测试数据"""
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    _init_test_db(conn)
    return conn


@pytest.fixture
def safe_conn(mem_db):
    """返回一个 MagicMock 包装的连接，close 不真正关闭"""
    wrapper = MagicMock(wraps=mem_db)
    # 让 close 变成空操作
    wrapper.close = MagicMock()
    # cursor() 返回真实游标
    wrapper.cursor = mem_db.cursor
    wrapper.commit = mem_db.commit
    wrapper.execute = mem_db.execute
    wrapper.executemany = mem_db.executemany
    wrapper.executescript = mem_db.executescript
    wrapper.row_factory = PropertyMock(return_value=mem_db.row_factory)
    return wrapper


def _make_engine(**overrides):
    defaults = dict(
        estimated_score=595,
        subject_first="物理",
        subject_elective1="化学",
        subject_elective2="生物",
        color_vision="正常",
        naked_eye_vision="5.0",
        gender="男",
        height_cm=175,
        weight_kg=65,
        rank_2026=74000,
        accept_private=True,
        accept_joint=False,
    )
    defaults.update(overrides)
    profile = StudentProfile(**defaults)
    return RecommendEngine(profile)


class TestEngineGenerate:
    """引擎 generate() 集成测试"""

    @pytest.fixture(autouse=True)
    def _patch_db(self, safe_conn):
        self._patches = [
            patch("src.core.engine.get_connection", return_value=safe_conn),
            patch("src.core.ranking.get_connection", return_value=safe_conn),
        ]
        for p in self._patches:
            p.start()
        yield
        for p in self._patches:
            p.stop()

    def test_basic_generate(self):
        engine = _make_engine()
        result = engine.generate(batch="本科批", total=96)
        assert isinstance(result, list)
        for i, item in enumerate(result):
            assert item.seq == i + 1

    def test_no_rank_returns_empty(self):
        engine = _make_engine(rank_2026=0)
        result = engine.generate()
        assert result == []

    def test_color_blind_filter(self):
        engine = _make_engine(color_vision="色盲")
        result = engine.generate()
        for item in result:
            assert "飞行技术" not in item.major_name

    def test_private_college_filter(self):
        engine = _make_engine(rank_2026=250000, accept_private=False)
        result = engine.generate()
        for item in result:
            assert "民办" not in item.college_nature

    def test_joint_college_filter(self):
        engine = _make_engine(rank_2026=12000)
        result = engine.generate()
        for item in result:
            assert "中外合作" not in item.college_nature

    def test_elective_requirement_filter(self):
        engine = _make_engine(
            estimated_score=640,
            subject_elective1="地理",
            subject_elective2="政治",
            rank_2026=25000,
        )
        result = engine.generate()
        for item in result:
            assert "临床医学" not in item.major_name

    def test_ranking_order(self):
        engine = _make_engine()
        result = engine.generate()
        if len(result) >= 30:
            chong = result[:29]
            for i in range(len(chong) - 1):
                assert chong[i].min_rank_2025 <= chong[i + 1].min_rank_2025
            bao = result[29:]
            for i in range(len(bao) - 1):
                assert bao[i].min_rank_2025 <= bao[i + 1].min_rank_2025

    def test_tier_labels(self):
        engine = _make_engine()
        result = engine.generate()
        for item in result:
            assert item.tier in ("冲", "稳", "保")

    def test_equivalent_score(self):
        engine = _make_engine()
        equiv = engine.get_student_equivalent_score(2025)
        assert 580 <= equiv <= 610
