from .database import DB
from asyncio import sleep
from dataclasses import dataclass

@dataclass
class DataSynchronizer:
	db: DB
	platform: str

	async def synchronization(self):
		while True:
			datas = await self.db.get_resolved_bans(self.platform)

			for data in datas:
				yield data

			await sleep(5)