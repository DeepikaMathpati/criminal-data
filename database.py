import sqlite3

db = sqlite3.connect(
    "crime.db",
    check_same_thread=False
)

cursor = db.cursor()
cursor.execute("""
CREATE TABLE IF NOT EXISTS Criminal(
    Criminal_ID INTEGER PRIMARY KEY,
    Name TEXT,
    Age INTEGER,
    Gender TEXT
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS Crime(
    Crime_ID INTEGER PRIMARY KEY,
    Crime_Type TEXT,
    Crime_Date TEXT,
    Crime_Time TEXT,
    Location_ID INTEGER,
    Criminal_ID INTEGER
)
""")

db.commit()

# Ensure we have a text `Location` column to store address/pincode
cursor.execute("PRAGMA table_info(Crime)")
cols = [row[1] for row in cursor.fetchall()]
if 'Location' not in cols:
    cursor.execute("ALTER TABLE Crime ADD COLUMN Location TEXT")
    db.commit()