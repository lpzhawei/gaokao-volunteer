"""
位次查询与等效分计算
负责 score_rank 表的位次查询、分数反查、等效分转换
"""
import logging
from ..data.database import get_connection

logger = logging.getLogger(__name__)


class RankingService:
    """位次查询服务"""

    def __init__(self, subject_first: str):
        self.subject_first = subject_first
        self._cache = {}

    def get_rank(self, score: int, year: int) -> int:
        """查询指定年份指定分数对应的累计位次"""
        conn = get_connection()
        try:
            cur = conn.cursor()
            cur.execute("""
                SELECT rank_cumulative FROM score_rank
                WHERE year=? AND subject_type=? AND score<=?
                ORDER BY score DESC LIMIT 1
            """, (year, self.subject_first, score))
            row = cur.fetchone()
            if row:
                return row[0]
            return 999999   # 找不到则返回极大值
        finally:
            conn.close()

    def get_rank_cached(self, score: int, year: int) -> int:
        """查询位次，结果缓存避免重复查询"""
        cache_key = (score, year, self.subject_first)
        if cache_key not in self._cache:
            self._cache[cache_key] = self.get_rank(score, year)
        return self._cache[cache_key]

    def get_score_by_rank(self, rank: int, year: int) -> int:
        """根据位次反查对应分数（近似值）"""
        conn = get_connection()
        try:
            cur = conn.cursor()
            cur.execute("""
                SELECT score FROM score_rank
                WHERE year=? AND subject_type=? AND rank_cumulative>=?
                ORDER BY rank_cumulative ASC LIMIT 1
            """, (year, self.subject_first, rank))
            row = cur.fetchone()
            return row[0] if row else 0
        finally:
            conn.close()

    def get_equivalent_score(self, score: int, from_year: int, to_year: int) -> int:
        """
        计算等效分：将某年份的分数转换为目标年份的等效分
        算法：分数 → 位次 → 目标年份的分数
        """
        actual_from = from_year if from_year <= 2025 else 2025
        actual_to = to_year if to_year <= 2025 else 2025

        if actual_from == actual_to:
            return score

        rank = self.get_rank(score, actual_from)
        if rank >= 999999:
            return 0

        return self.get_score_by_rank(rank, actual_to)

    def get_equivalent_score_by_rank(self, rank_2026: int, to_year: int) -> int:
        """
        用2026位次直接计算等效分
        算法：2026位次 → 直接查 to_year 年的一分一段 → 得到等效分
        """
        if rank_2026 <= 0:
            return 0
        actual_to = to_year if to_year <= 2025 else 2025
        return self.get_score_by_rank(rank_2026, actual_to)

    def get_student_equivalent_score(self, rank_2026: int, year: int = 2025) -> int:
        """
        获取考生的等效分
        必须使用用户输入的2026位次，未输入则返回0
        """
        if rank_2026 > 0:
            return self.get_equivalent_score_by_rank(rank_2026, year)
        return 0

    def get_student_rank(self, rank_2026: int) -> int:
        """获取考生位次：必须使用用户输入的2026位次"""
        return rank_2026 if rank_2026 > 0 else 0
