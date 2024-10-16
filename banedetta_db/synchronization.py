from .database import DB
from asyncio import sleep
from dataclasses import dataclass

@dataclass
class DataSynchronizer:
	db: DB
	platform: str

	async def synchronization(self):
		while True:
			for data in await self.db.get_no_posts_bans(self.platform):
				data["problem"] = "no_post"
				yield data

			for data in await self.db.get_resolved_bans(self.platform):
				data["problem"] = "resolved"
				yield data

			await sleep(3)
