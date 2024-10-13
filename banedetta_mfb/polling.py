from .database import DB
from asyncio import sleep
from dataclasses import dataclass
from typing import TYPE_CHECKING

@dataclass
class Polling:
	db: DB
	__trigger: bool = True

	async def polling(self):
		last_id = 0

		if self.__trigger:
			last_id = (await self.db.get_last_data())["id"]
			self.__trigger = False

		while True:
			new_data = await self.db.get_next_datas(last_id)

			for row in new_data:
				yield row
				last_id = max(last_id, row["id"])

			await sleep(1)