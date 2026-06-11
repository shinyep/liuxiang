import sqlite3

db_path = r'e:\liuxiang\flow_system\dist\成品追溯与客户管理系统\data\db.sqlite3'
conn = sqlite3.connect(db_path)
c = conn.cursor()

# 查看客户 558 的记录
c.execute('''
    SELECT id, customer_id, material_number, shipment_date,
           production_date_code, batch_number, packaging_line
    FROM api_shipment WHERE customer_id = 558 ORDER BY id
''')
print('客户 558 当前记录:')
for r in c.fetchall():
    print(f'  ID={r[0]}, material={r[2]}, date={r[3]}, batch={r[5]}')

# 查看最大 ID
c.execute('SELECT MAX(id) FROM api_shipment')
print(f'\n最大 ID: {c.fetchone()[0]}')
c.execute('SELECT COUNT(*) FROM api_shipment')
print(f'总记录数: {c.fetchone()[0]}')

conn.close()
