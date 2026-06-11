import sqlite3
import os

db_path = r'E:\liuxiang\flow_system\data\db.sqlite3'
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# 查看 customer 表结构
cursor.execute('PRAGMA table_info(api_customer)')
columns = cursor.fetchall()
print('api_customer 表结构:')
for col in columns:
    print(f'  {col[1]}: {col[2]}')
print()

# 统计记录数
cursor.execute('SELECT COUNT(*) FROM api_customer')
count = cursor.fetchone()[0]
print(f'客户总数: {count}')
print()

# 查看前几条数据
cursor.execute('SELECT id, name, area_code FROM api_customer LIMIT 5')
rows = cursor.fetchall()
print('前5条客户数据:')
for row in rows:
    print(f'  ID={row[0]}, 名称={row[1]}, 区域代码={row[2]}')

conn.close()
