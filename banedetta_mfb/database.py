from aiomysql import connect, DictCursor
from contextlib import asynccontextmanager
from dataclasses import dataclass

@dataclass
class DB:
	host: str
	user: str
	password: str
	schema: str
	port: int

	@asynccontextmanager
	async def get_connection(self):
		try:
			conn = await connect(self.host, self.user, self.password, self.schema, self.port)
			yield conn
		except Exception as e:
			raise e
		finally:
			if conn:
				conn.close()

	async def init(self):
		async with self.get_connection() as conn:
			async with conn.cursor() as cur:
				await cur.execute("SET sql_notes = 0;")
				await cur.execute("""
					CREATE TABLE IF NOT EXISTS bans_data (
						id INT AUTO_INCREMENT PRIMARY KEY,
						nickname VARCHAR(255),
						`by` VARCHAR(255),
						reason TEXT,
						confirmed BOOL,
						unbanned BOOL DEFAULT FALSE,
						vk_post INT,
						tg_post INT
					);
				""")
				await cur.execute("SET sql_notes = 1;")
				await conn.commit()

	async def get_data(self, id: int):
		async with self.get_connection() as conn:
			async with conn.cursor(DictCursor) as cur:
				await cur.execute("SELECT * FROM bans_data WHERE id = %s", (id,))
				return await cur.fetchone()

	async def get_last_data(self):
		async with self.get_connection() as conn:
			async with conn.cursor(DictCursor) as cur:
				await cur.execute("SELECT * FROM bans_data ORDER BY id DESC LIMIT 1;")
				return await cur.fetchone()

	async def get_next_datas(self, id):
		async with self.get_connection() as conn:
			async with conn.cursor(DictCursor) as cur:
				await cur.execute("SELECT * FROM bans_data WHERE id > %s ORDER BY id ASC;", (id,))
				return await cur.fetchall()

	async def update_post_id(self, platform: str, post_id: int, id: int):
		async with self.get_connection() as conn:
			async with conn.cursor(DictCursor) as cur:
				await cur.execute(f"UPDATE bans_data SET {platform}_post = %s WHERE id = %s;", (post_id, id,))
				await conn.commit()

	async def get_data_by_nickname(self, nickname: str, sort: str = "DESC"):
		async with self.get_connection() as conn:
			async with conn.cursor(DictCursor) as cur:
				await cur.execute(f"SELECT * FROM bans_data WHERE nickname = %s ORDER BY id {sort.upper()} LIMIT 1;", (nickname,))
				return await cur.fetchone()
