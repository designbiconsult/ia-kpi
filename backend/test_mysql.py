import pymysql

conn = pymysql.connect(
    host="procipa-conceito.ddns.net",
    port=33065,
    user="ctoviews",
    password="VmlkYUewhcmxluaGExMg==",
    database="dbview"
)
cur = conn.cursor()
cur.execute("SHOW TABLES;")
tabelas = cur.fetchall()
print(tabelas)
conn.close()
