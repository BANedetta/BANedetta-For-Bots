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
		conn = await connect(self.host, self.user, self.password, self.schema, self.port)
		try:
			yield conn
		finally:
			conn.close()

	@asynccontextmanager
	async def get_cursor(self):
		async with self.get_connection() as conn:
			async with conn.cursor(DictCursor) as cur:
				yield cur
			await conn.commit()

	async def init(self) -> None:
		# await self.execute_query("SET sql_notes = 0;")
		await self.execute_query("""
			CREATE TABLE IF NOT EXISTS bans_data (
				id INT AUTO_INCREMENT PRIMARY KEY,
				banned VARCHAR(255),
				`by` VARCHAR(255),
				reason TEXT,
				confirmed BOOL,
				status VARCHAR(9) DEFAULT "waiting",
				unbanned BOOL,
				vk_post INT,
				tg_post INT,
				tg_post_c INT,
				created DATETIME DEFAULT CURRENT_TIMESTAMP
			);
		""")
		# await self.execute_query("SET sql_notes = 1;")

	async def execute_query(self, query: str, params: tuple = ()) -> None:
		async with self.get_cursor() as cur:
			await cur.execute(query, params)

	async def fetch_one(self, query: str, params: tuple = ()) -> dict:
		async with self.get_cursor() as cur:
			await cur.execute(query, params)
			return await cur.fetchone() or {}

	async def fetch_all(self, query: str, params: tuple = ()) -> list:
		async with self.get_cursor() as cur:
			await cur.execute(query, params)
			return await cur.fetchall() or []

	async def get_data(self, id: int) -> dict:
		return await self.fetch_one("SELECT * FROM bans_data WHERE id = %s", (id,))

	async def get_last_data(self) -> dict:
		return await self.fetch_one("SELECT * FROM bans_data ORDER BY id DESC LIMIT 1;")

	async def get_next_datas(self, id: int) -> list:
		return await self.fetch_all("SELECT * FROM bans_data WHERE id > %s ORDER BY id ASC;", (id,))

	async def update_post_id(self, platform: str, post_id: int, id: int) -> None:
		await self.execute_query(f"UPDATE bans_data SET {platform}_post = %s WHERE id = %s;", (post_id, id))

	async def get_datas_by_nickname(self, nickname: str, sort: str = "DESC") -> dict:
		return await self.fetch_one(f"SELECT * FROM bans_data WHERE banned = %s ORDER BY id {sort.upper()} LIMIT 1;", (nickname,))

	async def get_data_by_post_id(self, platform: str, post_id: int) -> dict:
		return await self.fetch_one(f"SELECT * FROM bans_data WHERE {platform}_post = %s LIMIT 1;", (post_id,))

	async def deny(self, id: int) -> None:
		await self.execute_query("UPDATE bans_data SET unbanned = %s, status = %s WHERE id = %s;", (True, "deny", id))

	async def confirm(self, id: int) -> None:
		await self.execute_query("UPDATE bans_data SET unbanned = %s, status = %s WHERE id = %s;", (False, "confirmed", id))

	async def get_no_posts_bans(self, platform: str) -> list:
		return await self.fetch_all(f"SELECT * FROM bans_data WHERE confirmed IS NOT TRUE AND status = %s AND {platform}_post IS NULL;", ("waiting",))

	async def get_resolved_bans(self, platform: str) -> list:
		return await self.fetch_all(f"SELECT * FROM bans_data WHERE confirmed IS NOT TRUE AND status != %s AND {platform}_post > -1;", ("waiting",))

	async def update_c_post_id(self, post_id: int, id: int) -> None:
		await self.execute_query(f"UPDATE bans_data SET tg_post_c = %s WHERE id = %s;", (post_id, id))