import pymysql
import re

conn = pymysql.connect(
    host='monorail.proxy.rlwy.net',
    user='root',
    password='BmjCFHlOpjLPjVXMroXskaEZBrKNIJai',
    port=52791,
    db='railway',
    charset='utf8mb4'
)
cursor = conn.cursor()

with open('inventario_taller_respaldo.sql', 'r', encoding='utf-8') as f:
    sql = f.read()

# Eliminar bloques DELIMITER
sql = re.sub(r'DELIMITER\s+\S+', '', sql)
sql = re.sub(r'\$\$', '', sql)

for statement in sql.split(';'):
    statement = statement.strip()
    if statement:
        try:
            cursor.execute(statement)
        except Exception as e:
            print(f"Advertencia: {e}")

conn.commit()
conn.close()
print('¡Importado correctamente!')