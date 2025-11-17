import asyncio
from os.path import exists as file_exists
from kivy.base import Logger # For PyDroid
from models import Model
from views import App
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.ext.asyncio import (
	create_async_engine,
	async_sessionmaker,
)


DB_NAME = 'pallets.db'


async def main():
	engine = create_async_engine(
		url=f'sqlite+aiosqlite:///{DB_NAME}',
		connect_args={'check_same_thread': False},
		echo=False,
	)
	Session = async_sessionmaker(
		bind=engine,
		expire_on_commit=False,
		class_=AsyncSession
	)
	
	if not file_exists(DB_NAME):
		async with engine.begin() as conn:
			await conn.run_sync(Model.metadata.create_all)
	
	app = App(Session)
	await app.async_run()
	await engine.dispose()


if __name__ == '__main__':
	asyncio.run(main())