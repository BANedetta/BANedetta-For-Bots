from banedetta_mfb import DB, Polling

test = DB("localhost", "root", "qwerty", "banedetta", 3306)

import asyncio

async def main():
	# await test.init()
	# await test.update_post_id("tg", 148, 2)
	print(await test.get_data_by_nickname("tester", "asc"))
	# polling = Polling(test)

	# async for row in polling.polling():
	# 	print(row)

asyncio.run(main())