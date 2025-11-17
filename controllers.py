from collections import defaultdict
from kivy.clock import Clock
from kivy.properties import ObjectProperty
from models import (
	Pallet,
	Box,
)
from sqlalchemy import (
	select,
	func,
)
from sqlalchemy.orm import selectinload


class Controller:
	def __init__(self, session_cls):
		self.listeners = defaultdict(list)
		self.session_cls = session_cls
	
	def listen(self, event, callback):
		if callback not in self.listeners.get(event, []):
			self.listeners[event].append(callback)
	
	def notify(self, event, *args, **kwargs):
		for callback in self.listeners.get(event, []):
			callback(*args, **kwargs)
	
	def connect(self):
		return self.session_cls()


class PalletController(Controller):
	async def add_new(self):
		async with self.connect() as session:
			query = select(func.count()).select_from(Pallet)
			count = await session.scalar(query)
			code = f'P{count + 1}'
			pallet = Pallet(code=code)
			session.add(pallet)
			await session.commit()

		Clock.schedule_once(lambda _, p=pallet: self.notify('added', p))
	
	async def list(self):
		async with self.connect() as session:
			query = select(Pallet)
			result = await session.scalars(query)
			pallets = result.all()
		
		Clock.schedule_once(lambda _, ps=pallets: self.notify('listed', ps))


class BoxController(Controller):
	pallet = None
	
	async def add_new(self):
		if self.pallet == None:
			raise Exception('Pallet not set!')
		
		async with self.connect() as session:
			query = (
				select(func.count())
				.select_from(Box)
				.where(Box.pallet_id == self.pallet.id)
			)
			count = await session.scalar(query)
			code = f'{self.pallet.code}C{count + 1}'
			box = Box(code=code, pallet_id=self.pallet.id)
			session.add(box)
			await session.commit()
		
		Clock.schedule_once(lambda _, b=box: self.notify('added', b))
	
	async def list(self):
		if self.pallet == None:
			raise Exception('Pallet not set')
		
		async with self.connect() as session:
			pallet = await session.merge(self.pallet)
			boxes = await pallet.awaitable_attrs.boxes
		
		Clock.schedule_once(lambda _, bs=boxes: self.notify('listed', bs))


class ProductController(Controller):
	box = None
	
	async def list(self):
		if self.box == None:
			raise Exception('Box not set!')
		
		async with self.connect() as session:
			box = await session.merge(self.box)
			products = await box.awaitable_attrs.products
			[await (await bp.awaitable_attrs.product).awaitable_attrs.name for bp in products] # Thafuck u were thinking?
		
		Clock.schedule_once(lambda _, ps=products: self.notify('listed', ps))
