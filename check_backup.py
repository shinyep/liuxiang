import sqlite3

# 检查最新的备份
backup_path = r'e:\liuxiang\数据库备份\db_backup_周五-2026-04-22-00-29.sqlite3'
conn = sqlite3.connect(backup_path)
c = conn.cursor()

c.execute('SELECT COUNT(*) FROM api_shipment')
print(f'总记录数: {c.fetchone()[0]}')

c.execute('''
    SELECT id, customer_id, material_number, shipment_date,
           production_date_code, batch_number, packaging_line
    FROM api_shipment WHERE customer_id = 558 ORDER BY id
''')
print('\n客户 558 记录:')
for r in c.fetchall():
    print(f'  ID={r[0]}, material={r[2]}, date={r[3]}, batch={r[5]}')

conn.close()
