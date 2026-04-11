"""
数据库迁移脚本：从参考数据导入 enrichment 信息
新增字段：city, city_level, major_track, tuition, color_restrict_detail
"""
import sqlite3, pandas as pd, re
from pathlib import Path

SRC = Path(__file__).parent
DB = SRC / 'data' / 'db' / 'gaokao.db'
REF_FILE = SRC.parent / '河北-2025高报数据参考.xlsx'

def clean_college_name(name):
    """去除院校名后的[公办]等标签"""
    if not name:
        return ''
    return re.sub(r'\[.*?\]', '', name).strip()

def extract_color_restrict(note):
    """从专业备注中提取体检限制详情"""
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

print("=" * 60)
print("1. 添加新字段到 admission_data 表")
print("=" * 60)
conn = sqlite3.connect(DB)
cur = conn.cursor()

# 检查字段是否已存在
cur.execute('PRAGMA table_info(admission_data)')
existing_cols = [c[1] for c in cur.fetchall()]
print("现有字段:", existing_cols)

new_fields = {
    'city': 'TEXT',
    'city_level': 'TEXT',
    'major_track': 'TEXT',
    'tuition': 'TEXT',
    'color_restrict_detail': 'TEXT',
    'province_detail': 'TEXT',
}
for field, ftype in new_fields.items():
    if field not in existing_cols:
        cur.execute(f'ALTER TABLE admission_data ADD COLUMN {field} {ftype}')
        print(f"  + 新增字段: {field}")
    else:
        print(f"  已有字段: {field}")

conn.commit()
print()

print("=" * 60)
print("2. 读取参考数据")
print("=" * 60)
ref_df = pd.read_excel(REF_FILE, sheet_name='Sheet1', header=1)
print(f"参考数据总行数: {len(ref_df)}")

# 只取2025年数据
ref_2025 = ref_df[ref_df['年份'] == 2025].copy()
print(f"2025年数据行数: {len(ref_2025)}")

# 清理院校名
ref_2025['college_name_clean'] = ref_2025['院校名称'].apply(clean_college_name)

# 提取体检限制详情
ref_2025['color_restrict_detail'] = ref_2025['专业备注'].apply(extract_color_restrict)

# 处理学费
def clean_tuition(t):
    if pd.isna(t) or str(t).strip() in ('', '待定', '免费'):
        return str(t) if not pd.isna(t) else '待定'
    return str(int(t)) if str(t).replace('.', '').replace('-', '').isdigit() else str(t)

ref_2025['tuition'] = ref_2025['学费'].apply(clean_tuition)

# 处理专业赛道
ref_2025['major_track'] = ref_2025['专业版块'].fillna('')

# 处理城市
ref_2025['city'] = ref_2025['城市'].fillna('')
ref_2025['city_level'] = ref_2025['城市水平标签'].fillna('')
ref_2025['province_detail'] = ref_2025['所在省'].fillna('')

print(f"\n城市分布:\n{ref_2025['city_level'].value_counts().to_string()}")
print(f"\n专业赛道分布:\n{ref_2025['major_track'].value_counts().to_string()}")
print()

print("=" * 60)
print("3. 构建匹配键并更新数据库")
print("=" * 60)

# 创建匹配键: college_name_clean + major_name
# 由于参考数据的专业名可能带括号备注，需要做模糊匹配
# 策略：按 college_name_clean + 专业名称前10字 匹配

def make_key(row):
    cn = clean_college_name(str(row.get('院校名称', '')))
    mn = str(row.get('专业名称', ''))[:20]
    return (cn, mn)

ref_2025['match_key'] = ref_2025.apply(make_key, axis=1)

# 读取现有数据库数据
db_df = pd.read_sql(
    "SELECT id, year, college_name, major_name, body_restrict, city, city_level, major_track FROM admission_data WHERE year = 2025",
    conn
)
db_df['college_name_clean'] = db_df['college_name'].apply(clean_college_name)
db_df['match_key'] = db_df.apply(lambda r: (r['college_name_clean'], str(r['major_name'])[:20]), axis=1)

print(f"数据库2025年数据行数: {len(db_df)}")

# 建立参考数据索引
ref_index = {}
for _, row in ref_2025.iterrows():
    key = row['match_key']
    if key not in ref_index:
        ref_index[key] = row

# 统计匹配情况
matched = 0
update_batch = []
for _, row in db_df.iterrows():
    key = row['match_key']
    if key in ref_index:
        ref_row = ref_index[key]
        update_batch.append({
            'id': row['id'],
            'city': ref_row['city'],
            'city_level': ref_row['city_level'],
            'major_track': ref_row['major_track'],
            'tuition': ref_row['tuition'],
            'color_restrict_detail': ref_row['color_restrict_detail'],
            'province_detail': ref_row['province_detail'],
        })
        matched += 1
    else:
        # 尝试只用院校名匹配
        cn = row['college_name_clean']
        ref_by_college = [r for k, r in ref_index.items() if k[0] == cn]
        if ref_by_college:
            # 找专业名最接近的
            best = None
            best_score = -1
            mn = str(row['major_name'])
            for r in ref_by_college:
                rm = str(r['专业名称'])
                # 简单相似度：共同前缀长度
                score = 0
                for i in range(min(len(mn), len(rm))):
                    if mn[i] == rm[i]:
                        score += 1
                    else:
                        break
                if score > best_score and score >= 4:
                    best_score = score
                    best = r
            if best is not None:
                update_batch.append({
                    'id': row['id'],
                    'city': best['city'],
                    'city_level': best['city_level'],
                    'major_track': best['major_track'],
                    'tuition': best['tuition'],
                    'color_restrict_detail': best['color_restrict_detail'],
                    'province_detail': best['province_detail'],
                })
                matched += 1

print(f"精确匹配: {matched}/{len(db_df)} ({matched/len(db_df)*100:.1f}%)")
print(f"待更新记录数: {len(update_batch)}")

# 批量更新
for i, upd in enumerate(update_batch):
    cur.execute("""
        UPDATE admission_data SET
            city = ?,
            city_level = ?,
            major_track = ?,
            tuition = ?,
            color_restrict_detail = ?,
            province_detail = ?
        WHERE id = ?
    """, (
        upd['city'], upd['city_level'], upd['major_track'],
        upd['tuition'], upd['color_restrict_detail'], upd['province_detail'],
        upd['id']
    ))
    if (i + 1) % 2000 == 0:
        print(f"  已更新 {i+1}/{len(update_batch)}...")
        conn.commit()

conn.commit()
print("  数据库更新完成!")

print()
print("=" * 60)
print("4. 验证更新结果")
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
print(f"  有城市信息: {row[1]} ({row[1]/row[0]*100:.1f}%)")
print(f"  有城市级别: {row[2]} ({row[2]/row[0]*100:.1f}%)")
print(f"  有专业赛道: {row[3]} ({row[3]/row[0]*100:.1f}%)")
print(f"  有学费信息: {row[4]} ({row[4]/row[0]*100:.1f}%)")

print()
print("城市级别分布:")
cur.execute("SELECT city_level, COUNT(*) FROM admission_data WHERE year=2025 AND city_level IS NOT NULL AND city_level!='' GROUP BY city_level ORDER BY COUNT(*) DESC")
for r in cur.fetchall():
    print(f"  {r[0]}: {r[1]}")

print()
print("专业赛道分布:")
cur.execute("SELECT major_track, COUNT(*) FROM admission_data WHERE year=2025 AND major_track IS NOT NULL AND major_track!='' GROUP BY major_track ORDER BY COUNT(*) DESC")
for r in cur.fetchall():
    print(f"  {r[0]}: {r[1]}")

conn.close()
print()
print("迁移完成!")
