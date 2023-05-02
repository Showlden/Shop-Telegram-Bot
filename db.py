import sqlite3

class Database:
	def __init__(self, db_file):
		self.connect = sqlite3.connect(db_file)
		self.cursor = self.connect.cursor()
		self.cursor.execute("""CREATE TABLE IF NOT EXISTS clothes(
									id INTEGER PRIMARY KEY,
									photo_id TEXT,
									name TEXT,
									price TEXT)""")
		self.connect.commit()

	def get_item(self, item_id):
		with self.connect:
			self.cursor.execute(f"SELECT * FROM clothes WHERE id = {item_id}")
			data = self.cursor.fetchone()
		return data	

	def get_len_items(self):
		with self.connect:
			self.cursor.execute(f"SELECT id FROM clothes")
			data = self.cursor.fetchall()
		return len(data)

	def set_item(self, photo_id, name, price):
		with self.connect:
			self.cursor.execute("INSERT INTO clothes (photo_id, name, price) VALUES(?, ?, ?)", (photo_id, name, price))
	

