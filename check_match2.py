import sqlite3, pandas as pd, re

DB = 'data/db/gaokao.db'
REF_FILE = '../河北-2025高报数据参考.xlsx'

conn = sqlite3.connect(DB)

# 看看有多少种城市后缀
db_df = pd.read_sql("SELECT DISTINCT college_name FROM admission_data WHERE year = 2025", conn)
suffixes = {}
for name in db_df['college_name']:
    m = re.search(r'[(（]([^)）]+)[)）]', name)
    if m:
        s = m.group(1)
        suffixes[s] = suffixes.get(s, 0) + 1

print("院校名中的城市后缀:")
for k, v in sorted(suffixes.items(), key=lambda x: -x[1]):
    print(f"  {k}: {v}")

print()
# 检查参考数据的院校名是否带括号
ref_df = pd.read_excel(REF_FILE, sheet_name='Sheet1', header=1)
ref_2025 = ref_df[ref_df['年份'] == 2025]
ref_colleges = ref_2025['院校名称'].unique()
print("参考数据院校名示例(带括号):")
for c in ref_colleges[:20]:
    print(f"  {c}")

conn.close()
