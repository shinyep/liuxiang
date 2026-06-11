import sqlite3
import os

db_path = r'E:\liuxiang\flow_system\data\db.sqlite3'
print(f'数据库路径: {db_path}')
print(f'文件大小: {os.path.getsize(db_path)} bytes')
print()

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# 查看所有表
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = cursor.fetchall()
print('所有表:')
for t in tables:
    print(f'  - {t[0]}')
print()

# 查看 shipment 表结构
cursor.execute('PRAGMA table_info(api_shipment)')
columns = cursor.fetchall()
print('api_shipment 表结构:')
for col in columns:
    print(f'  {col[1]}: {col[2]}')
print()

# 统计记录数
cursor.execute('SELECT COUNT(*) FROM api_shipment')
count = cursor.fetchone()[0]
print(f'总记录数: {count}')
print()

# 查看前几条数据
cursor.execute('SELECT id, shipment_date, customer_id, created_at FROM api_shipment LIMIT 5')
rows = cursor.fetchall()
print('前5条数据:')
for row in rows:
    print(f'  ID={row[0]}, 日期={row[1]}, 客户={row[2]}, 录入时间={row[3]}')

conn.close()
