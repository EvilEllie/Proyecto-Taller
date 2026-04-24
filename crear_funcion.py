import pymysql

conn = pymysql.connect(
    host='monorail.proxy.rlwy.net',
    user='root',
    password='BmjCFHlOpjLPjVXMroXskaEZBrKNIJai',
    port=52791,
    db='railway',
    charset='utf8mb4',
    autocommit=True
)
cursor = conn.cursor()

sql = """CREATE FUNCTION IF NOT EXISTS stock_bajo(cant INT)
RETURNS VARCHAR(20)
DETERMINISTIC
BEGIN
  DECLARE estado VARCHAR(20);
  IF cant <= 5 THEN
    SET estado = 'STOCK BAJO';
  ELSE
    SET estado = 'STOCK NORMAL';
  END IF;
  RETURN estado;
END"""

try:
    cursor.execute(sql)
    print('Funcion creada!')
except Exception as e:
    print(f'Error: {e}')
finally:
    conn.close()