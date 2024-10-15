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
		conn = None

		try:
			conn = await connect(self.host, self.user, self.password, self.schema, self.port)
			yield conn
		except Exception as e:
			raise e
		finally:
			if conn:
				conn.close()

	async def init(self) -> None:
		async with self.get_connection() as conn:
			async with conn.cursor() as cur:
				await cur.execute("SET sql_notes = 0;")
				await cur.execute("""
					CREATE TABLE IF NOT EXISTS bans_data (
						id INT AUTO_INCREMENT PRIMARY KEY,
						banned VARCHAR(255),
						`by` VARCHAR(255),
						reason TEXT,
						confirmed BOOL,
						unbanned BOOL,
						vk_post INT,
						tg_post INT,
						created DATETIME DEFAULT CURRENT_TIME
					);
				""")
				await cur.execute("SET sql_notes = 1;")
				await conn.commit()

	async def get_data(self, id: int) -> dict:
		async with self.get_connection() as conn:
			async with conn.cursor(DictCursor) as cur:
				await cur.execute("SELECT * FROM bans_data WHERE id = %s", (id,))
				return await cur.fetchone() or {}

	async def get_last_data(self) -> dict:
		async with self.get_connection() as conn:
			async with conn.cursor(DictCursor) as cur:
				await cur.execute("SELECT * FROM bans_data ORDER BY id DESC LIMIT 1;")
				return await cur.fetchone() or {}

	async def get_next_datas(self, id: int) -> dict:
		async with self.get_connection() as conn:
			async with conn.cursor(DictCursor) as cur:
				await cur.execute("SELECT * FROM bans_data WHERE id > %s ORDER BY id ASC;", (id,))
				return await cur.fetchall() or {}

	async def update_post_id(self, platform: str, post_id: int, id: int) -> None:
		async with self.get_connection() as conn:
			async with conn.cursor() as cur:
				await cur.execute(f"UPDATE bans_data SET {platform}_post = %s WHERE id = %s;", (post_id, id,))
				await conn.commit()

	async def get_data_by_nickname(self, nickname: str, sort: str = "DESC") -> dict:
		async with self.get_connection() as conn:
			async with conn.cursor(DictCursor) as cur:
				await cur.execute(f"SELECT * FROM bans_data WHERE banned = %s ORDER BY id {sort.upper()} LIMIT 1;", (nickname,))
				return await cur.fetchone() or {}

	async def get_data_by_post_id(self, platform: str, post_id: int) -> dict:
		async with self.get_connection() as conn:
			async with conn.cursor(DictCursor) as cur:
				await cur.execute(f"SELECT * FROM bans_data WHERE {platform}_post = %s LIMIT 1;", (post_id,))
				return await cur.fetchone() or {}

	async def deny(self, id: int) -> None:
		async with self.get_connection() as conn:
			async with conn.cursor() as cur:
				await cur.execute("UPDATE bans_data SET confirmed = %s, unbanned = %s, WHERE id = %s;", (False, True, id,))
				await conn.commit()

	async def confirm(self, id: int) -> None:
		async with self.get_connection() as conn:
			async with conn.cursor() as cur:
				await cur.execute("UPDATE bans_data SET confirmed = %s, unbanned = %s, WHERE id = %s;", (True, False, id,))
				await conn.commit()

	async def clear_posts(self, id: int) -> None:
		async with self.get_connection() as conn:
			async with conn.cursor() as cur:
				await cur.execute("UPDATE bans_data SET vk_post = %s, tg_post = %s, WHERE id = %s;", (-1, -1, id,))
				await conn.commit()
