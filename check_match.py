import sqlite3, pandas as pd, re

DB = 'data/db/gaokao.db'
REF_FILE = '../河北-2025高报数据参考.xlsx'

def clean_college_name(name):
    if not name:
        return ''
    return re.sub(r'\[.*?\]', '', name).strip()

conn = sqlite3.connect(DB)

# 读数据库
db_df = pd.read_sql(
    "SELECT DISTINCT college_name, major_name FROM admission_data WHERE year = 2025 AND subject_type = '物理' LIMIT 50",
    conn
)
db_df['college_name_clean'] = db_df['college_name'].apply(clean_college_name)
print("数据库院校+专业名示例:")
for _, r in db_df.head(30).iterrows():
    print(f"  {r['college_name_clean']} | {r['major_name']}")

print()

# 读参考数据
ref_df = pd.read_excel(REF_FILE, sheet_name='Sheet1', header=1)
ref_2025 = ref_df[ref_df['年份'] == 2025]
ref_2025 = ref_2025[ref_2025['科类'] == '物理']
ref_2025['college_name_clean'] = ref_2025['院校名称'].apply(clean_college_name)
print("参考数据院校+专业名示例:")
for _, r in ref_2025.head(30).iterrows():
    print(f"  {r['college_name_clean']} | {r['专业名称']}")

conn.close()
