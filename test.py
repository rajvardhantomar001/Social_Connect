import mysql.connector
conn = mysql.connector.connect(
    host="localhost",
    port="3306",
    user="root",
    password="",
    database="connectify"
)

user_id = 2
cursor = conn.cursor(dictionary=True)
cursor.execute('SELECT * FROM users WHERE user_id = %s', (user_id,))
user_profile = cursor.fetchone()

query = """
    SELECT * 
    FROM users 
    WHERE location = %s AND interest = %s
"""
values = (user_profile['location'], user_profile['interest'])
cursor.execute(query, values)
provider_profiles = cursor.fetchall()
print(provider_profiles)