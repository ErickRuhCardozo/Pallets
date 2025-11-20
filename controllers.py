from collections import defaultdict
from kivy.clock import Clock
from kivy.properties import ObjectProperty
from models import (
	Pallet,
	Box,
	BoxProduct,
)
from sqlalchemy import (
	select,
	func,
)
from sqlalchemy.orm import selectinload
from sqlalchemy.orm.exc import DetachedInstanceError


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

		dto = Pallet(
			id=pallet.id,
			code=code,
			created_at=pallet.created_at
		)
		Clock.schedule_once(lambda _, p=dto: self.notify('added', p))
	
	async def list(self):
		async with self.connect() as session:
			query = select(Pallet)
			result = await session.scalars(query)
			pallets = result.all()
		
		dtos = list(
			map(
				lambda p: Pallet(
					id=p.id,
					code=p.code,
					created_at=p.created_at,
					finished_at=p.finished_at
				),
				pallets
			)
		)
		Clock.schedule_once(lambda _, ps=dtos: self.notify('listed', ps))


class BoxController(Controller):
	pallet: Pallet = None
	
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

		dto = Box(
			id=box.id,
			code=code,
			created_at=box.created_at
		)
		Clock.schedule_once(lambda _, b=dto: self.notify('added', b))
	
	async def list(self):
		if self.pallet == None:
			raise Exception('Pallet not set')
		
		if self.pallet.boxes != []:
			dtos = self.pallet.boxes
		else:
			async with self.connect() as session:
				pallet = await session.merge(self.pallet)
				boxes = await pallet.awaitable_attrs.boxes
				session.expunge_all()
			
			dtos = list(
				map(
					lambda b: Box(
						id=b.id,
						code=b.code,
						created_at=b.created_at,
						finished_at=b.finished_at
					),
					boxes
				)
			)
			self.pallet.boxes = dtos

		Clock.schedule_once(lambda _, bs=dtos: self.notify('listed', bs))


class BoxProductController(Controller):
	box: BoxProduct = None
	
	async def list(self):
		if self.box == None:
			raise Exception('Box not set!')
		
		if self.box.products != []:
			dtos = self.box.products
		else:
			async with self.connect() as session:
				box = await session.merge(self.box)
				products = await box.awaitable_attrs.products
				dtos = []
				
				for bp in products:
					product = await bp.awaitable_attrs.product
					dtos.append(
						BoxProduct(
							id=bp.id,
							quantity=bp.quantity,
							product=product
						)
					)
					
			self.box.products = dtos
		
		Clock.schedule_once(lambda _, ps=dtos: self.notify('listed', ps))
