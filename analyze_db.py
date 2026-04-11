import sqlite3, pandas as pd

conn = sqlite3.connect('data/db/gaokao.db')
cur = conn.cursor()

cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = cur.fetchall()
print('数据库表:', [t[0] for t in tables])
print()

cur.execute('PRAGMA table_info(admission_data)')
cols = cur.fetchall()
print('admission_data 列:')
for c in cols:
    print(f'  {c[1]} {c[2]}')
print()

cur.execute('PRAGMA table_info(colleges)')
cols = cur.fetchall()
print('colleges 列:')
for c in cols:
    print(f'  {c[1]} {c[2]}')

conn.close()
