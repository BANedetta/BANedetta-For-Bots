from .database import DB
from asyncio import sleep
from dataclasses import dataclass

@dataclass
class DataSynchronizer:
	db: DB
	platform: str

	async def synchronize_problems(self):
		while True:
			for data, problem in (
				(await self.db.get_no_post_bans(self.platform), "no_post"),
				(await self.db.get_resolved_bans(self.platform), "resolved"),
			):
				for d in data:
					d["problem"] = problem
					yield d

			await sleep(10)
