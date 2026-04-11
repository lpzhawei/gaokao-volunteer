"""
改进版数据迁移：使用更精确的匹配策略
"""
import sqlite3, pandas as pd, re
from pathlib import Path

SRC = Path(__file__).parent
DB = SRC / 'data' / 'db' / 'gaokao.db'
REF_FILE = SRC.parent / '河北-2025高报数据参考.xlsx'

# 常见城市后缀（用于从院校名剥离）
CITY_SUFFIXES = [
    '成都市', '长春市', '济南市', '杭州市', '南宁市', '郑州市', '武汉市', '长沙市',
    '西安市', '昆明市', '北京市', '贵阳市', '南昌市', '哈尔滨市', '兰州市', '乌鲁木齐市',
    '合肥市', '上海市', '福州市', '重庆市', '南京市', '广州市', '保定市', '呼和浩特市',
    '银川市', '廊坊市', '沈阳市', '海口市', '石家庄市', '西宁市', '芜湖市', '赣州市',
    '天津市', '秦皇岛市', '沧州市', '珠海市', '柳州市', '桂林市', '蚌埠市', '马鞍山市',
    '吉林市', '绵阳市', '青岛市', '德阳市', '宁波市', '苏州市', '无锡市', '徐州市',
    '扬州市', '镇江市', '盐城市', '南通市', '泰州市', '宿迁市', '淮安市', '连云港市',
    '邯郸市', '唐山市', '张家口市', '承德市', '廊坊', '保定', '燕郊',
    '秦皇岛', '沧州', '石家庄', '北京', '上海', '武汉', '深圳', '青岛', '威海',
    '爱沙尼亚', '英国', '德国', '马来西亚', '波兰', '芬兰', '爱尔兰',
    '昆山', '深圳', '苏州',
]

# 特殊项目（非正常院校名后缀）
SPECIAL_PROGRAMS = [
    '按高考文化课成绩录取的艺术类专业', '八协计划', '地方专项计划', '少数民族预科班',
    '边防军人子女预科班', '中外合作办学', '国际本科学术互认课程项目',
    '京津冀职教改革项目', '合作培养项目', '国际合作专项', 'ZJUUIUC联合学院',
    '马来西亚分校', '爱尔兰校区', '芬兰校区', '波兰校区',
]

def strip_suffixes(name):
    """去除院校名中的城市后缀[]和()标注"""
    if not name:
        return ''
    # 去除[公办]等标签
    name = re.sub(r'\[.*?\]', '', name).strip()
    # 去除()和()内的内容（城市后缀）
    name = re.sub(r'[(（][^)）]+[)）]', '', name).strip()
    return name

def extract_color_restrict(note):
    if not note:
        return ''
    note = str(note)
    result = []
    if '色盲' in note:
        result.append('色盲')
    if '色弱' in note:
        result.append('色弱')
    if '视力' in note or '裸眼' in note:
        result.append('视力限制')
    if '身高' in note or '体重' in note:
        result.append('身高体重限制')
    return '; '.join(result) if result else ''

def clean_major_name(name):
    """简化专业名，去除括号内的备注"""
    if not name:
        return ''
    name = str(name)
    # 去除(八年制)(含：xxx)等内容
    name = re.sub(r'[(（][^)）]+[)）]', '', name)
    return name.strip()

def clean_tuition(t):
    if pd.isna(t) or str(t).strip() in ('', '待定', '免费'):
        return str(t) if not pd.isna(t) else '待定'
    return str(int(t)) if str(t).replace('.', '').replace('-', '').isdigit() else str(t)

print("=" * 60)
print("加载参考数据")
print("=" * 60)
ref_df = pd.read_excel(REF_FILE, sheet_name='Sheet1', header=1)
ref_2025 = ref_df[ref_df['年份'] == 2025].copy()
print(f"参考数据2025年: {len(ref_2025)} 行")

# 处理参考数据
ref_2025['college_clean'] = ref_2025['院校名称'].apply(strip_suffixes)
ref_2025['major_clean'] = ref_2025['专业名称'].apply(clean_major_name)
ref_2025['color_restrict_detail'] = ref_2025['专业备注'].apply(extract_color_restrict)
ref_2025['tuition'] = ref_2025['学费'].apply(clean_tuition)
ref_2025['major_track'] = ref_2025['专业版块'].fillna('')
ref_2025['city'] = ref_2025['城市'].fillna('')
ref_2025['city_level'] = ref_2025['城市水平标签'].fillna('')
ref_2025['province_detail'] = ref_2025['所在省'].fillna('')

# 构建复合匹配键：院校(去城市后缀) + 专业(去括号)
ref_2025['match_key'] = ref_2025['college_clean'] + '|' + ref_2025['major_clean']
ref_dict = {}
for _, row in ref_2025.iterrows():
    key = row['match_key']
    if key not in ref_dict:
        ref_dict[key] = row

print(f"参考数据唯一匹配键: {len(ref_dict)}")

print()
print("=" * 60)
print("处理数据库数据")
print("=" * 60)
conn = sqlite3.connect(DB)

# 清空2025年已填充字段，重新导入
cur = conn.cursor()
cur.execute("""
    UPDATE admission_data SET
        city = NULL, city_level = NULL, major_track = NULL,
        tuition = NULL, color_restrict_detail = NULL, province_detail = NULL
    WHERE year = 2025
""")
conn.commit()

db_df = pd.read_sql(
    "SELECT id, year, subject_type, college_name, major_name FROM admission_data WHERE year = 2025",
    conn
)
print(f"数据库2025年数据: {len(db_df)} 行")

db_df['college_clean'] = db_df['college_name'].apply(strip_suffixes)
db_df['major_clean'] = db_df['major_name'].apply(clean_major_name)
db_df['match_key'] = db_df['college_clean'] + '|' + db_df['major_clean']

# 统计匹配
matched_keys = set(db_df['match_key']) & set(ref_dict.keys())
print(f"直接匹配键数: {len(matched_keys)}")

# 构建更新批次
updates = []
unmatched = []
for _, row in db_df.iterrows():
    key = row['match_key']
    if key in ref_dict:
        ref = ref_dict[key]
        updates.append({
            'id': row['id'],
            'city': ref['city'],
            'city_level': ref['city_level'],
            'major_track': ref['major_track'],
            'tuition': ref['tuition'],
            'color_restrict_detail': ref['color_restrict_detail'],
            'province_detail': ref['province_detail'],
        })
    else:
        unmatched.append(row)

print(f"直接匹配更新: {len(updates)}")
print(f"未匹配: {len(unmatched)}")

# 尝试用院校名做索引，在专业名中模糊匹配
ref_by_college = {}
for key, ref_row in ref_dict.items():
    cn = ref_row['college_clean']
    if cn not in ref_by_college:
        ref_by_college[cn] = []
    ref_by_college[cn].append(ref_row)

fuzzy_updates = []
for row in unmatched:
    cn = row['college_clean']
    if cn in ref_by_college:
        candidates = ref_by_college[cn]
        # 找最接近的专业名
        mn = row['major_clean']
        best = None
        best_score = -1
        for cand in candidates:
            cm = cand['major_clean']
            # 计算简单相似度（共同前缀）
            score = 0
            for a, b in zip(mn, cm):
                if a == b:
                    score += 1
                else:
                    break
            # 也检查包含关系
            if mn in cm or cm in mn:
                score = max(score, min(len(mn), len(cm)))
            if score > best_score and score >= 4:
                best_score = score
                best = cand
        if best is not None:
            fuzzy_updates.append({
                'id': row['id'],
                'city': best['city'],
                'city_level': best['city_level'],
                'major_track': best['major_track'],
                'tuition': best['tuition'],
                'color_restrict_detail': best['color_restrict_detail'],
                'province_detail': best['province_detail'],
            })

print(f"模糊匹配更新: {len(fuzzy_updates)}")

all_updates = updates + fuzzy_updates
print(f"总计更新: {len(all_updates)} ({len(all_updates)/len(db_df)*100:.1f}%)")

# 执行批量更新
for i, upd in enumerate(all_updates):
    cur.execute("""
        UPDATE admission_data SET
            city = ?, city_level = ?, major_track = ?,
            tuition = ?, color_restrict_detail = ?, province_detail = ?
        WHERE id = ?
    """, (
        upd['city'], upd['city_level'], upd['major_track'],
        upd['tuition'], upd['color_restrict_detail'], upd['province_detail'],
        upd['id']
    ))
    if (i + 1) % 3000 == 0:
        print(f"  已更新 {i+1}/{len(all_updates)}...")
        conn.commit()

conn.commit()
print("数据库更新完成!")

# 验证
print()
print("=" * 60)
print("验证更新结果")
print("=" * 60)
cur.execute("""
    SELECT
        COUNT(*) as total,
        SUM(CASE WHEN city IS NOT NULL AND city != '' THEN 1 ELSE 0 END) as has_city,
        SUM(CASE WHEN city_level IS NOT NULL AND city_level != '' THEN 1 ELSE 0 END) as has_level,
        SUM(CASE WHEN major_track IS NOT NULL AND major_track != '' THEN 1 ELSE 0 END) as has_track,
        SUM(CASE WHEN tuition IS NOT NULL AND tuition != '' THEN 1 ELSE 0 END) as has_tuition
    FROM admission_data WHERE year = 2025
""")
row = cur.fetchone()
print(f"2025年总计: {row[0]}")
print(f"  有城市: {row[1]} ({row[1]/row[0]*100:.1f}%)")
print(f"  有城市级别: {row[2]} ({row[2]/row[0]*100:.1f}%)")
print(f"  有专业赛道: {row[3]} ({row[3]/row[0]*100:.1f}%)")
print(f"  有学费: {row[4]} ({row[4]/row[0]*100:.1f}%)")

print("\n城市级别分布:")
cur.execute("SELECT city_level, COUNT(*) FROM admission_data WHERE year=2025 AND city_level IS NOT NULL AND city_level!='' GROUP BY city_level ORDER BY COUNT(*) DESC")
for r in cur.fetchall():
    print(f"  {r[0]}: {r[1]}")

print("\n专业赛道分布:")
cur.execute("SELECT major_track, COUNT(*) FROM admission_data WHERE year=2025 AND major_track IS NOT NULL AND major_track!='' GROUP BY major_track ORDER BY COUNT(*) DESC LIMIT 15")
for r in cur.fetchall():
    print(f"  {r[0]}: {r[1]}")

conn.close()
print("\n完成!")
