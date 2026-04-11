import sys, os, sqlite3
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, '.')

# Test 1: Labels
from src.core.config import get_track_label, get_city_level_label, get_nature_label, get_risk_description
print('[PASS] 标签函数导入成功')

# Test 2: Models
from src.core.models import StudentProfile, VolunteerItem
p = StudentProfile(estimated_score=580, subject_first='物理', rank_2026=74000)
v = VolunteerItem(
    seq=1, college_code='1225', college_name='清华大学', major_name='计算机科学与技术',
    subject_type='物理', batch='本科批', tier='冲', min_score_3yr=680, avg_score_3yr=685,
    rank_diff=-5000, admit_prob=0.3, risk_level='高', college_nature='公办',
    city='北京', city_level='一线城市/省会城市', major_track='工：新工科和数学',
    tuition='5000', color_restrict_detail=''
)
city_emoji, city_lbl = get_city_level_label(v.city_level)
v.city_level_emoji = city_emoji
v.city_level_label = city_lbl
track_e, track_lvl, track_d = get_track_label(v.major_track)
v.track_emoji = track_e
v.track_level = track_lvl
v.track_desc = track_d
nat_e, nat_lbl, nat_tip = get_nature_label(v.college_nature)
v.nature_emoji = nat_e
v.nature_label = nat_lbl
v.nature_tip = nat_tip
v.risk_desc = get_risk_description(v.admit_prob)
print(f'[PASS] VolunteerItem: 城市={v.city_level_emoji}{v.city_level_label} 赛道={v.track_emoji}{v.track_desc} 性质={v.nature_emoji}{v.nature_label} 风险={v.risk_desc}')

# Test 3: Filters
from src.core.filters import get_body_restrict_detail
profile = StudentProfile(estimated_score=580, subject_first='物理', rank_2026=74000, color_vision='色弱')
item = {'major_name': '计算机科学与技术', 'body_restrict': '', 'color_restrict_detail': ''}
result = get_body_restrict_detail(item, profile)
print(f'[PASS] 体检检查: {result["summary"]}')

# Test 4: Hexagram
from src.gui.hexagram_chart import get_track_data
data = get_track_data('工：新工科和数学', '新一线城市/省会城市')
print(f'[PASS] 六边形数据: {data}')

# Test 5: Database
conn = sqlite3.connect('data/db/gaokao.db')
cur = conn.cursor()
cur.execute("SELECT COUNT(*) FROM admission_data WHERE year=2025 AND city IS NOT NULL AND city != ''")
cnt = cur.fetchone()[0]
cur.execute("SELECT COUNT(*) FROM admission_data WHERE year=2025")
total = cur.fetchone()[0]
print(f'[PASS] 数据库: {cnt}/{total} 条记录含城市信息 ({cnt/total*100:.1f}%)')
conn.close()

print()
print('=== 全部测试通过！===')
