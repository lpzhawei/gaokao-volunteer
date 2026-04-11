import sqlite3, pandas as pd

conn = sqlite3.connect('data/db/gaokao.db')

# 检查现有 body_restrict 格式
df = pd.read_sql("SELECT body_restrict, COUNT(*) as cnt FROM admission_data WHERE body_restrict IS NOT NULL AND body_restrict != '' GROUP BY body_restrict ORDER BY cnt DESC LIMIT 30", conn)
print("现有 body_restrict 格式:")
print(df.to_string())
print()

# 看几条具体数据
df2 = pd.read_sql("SELECT college_name, major_name, body_restrict FROM admission_data WHERE body_restrict IS NOT NULL AND body_restrict != '' AND body_restrict != '无' LIMIT 20", conn)
print("具体示例:")
print(df2.to_string())
print()

# 检查城市和赛道字段是否已有
cur = conn.cursor()
cur.execute('PRAGMA table_info(admission_data)')
cols = [c[1] for c in cur.fetchall()]
print("现有admission_data字段:", cols)

conn.close()
