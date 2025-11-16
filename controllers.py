from collections import defaultdict
from enum import IntEnum, auto
from sqlalchemy.orm import sessionmaker
from models import (
	Model,
	Pallet,
	Box
)
from sqlalchemy import (
	select,
	func,
	create_engine,
)


ENGINE = create_engine(url='sqlite:///pallets.db', echo=False)
Session = sessionmaker(bind=ENGINE, expire_on_commit=False)
Model.metadata.create_all(ENGINE)


class ControllerEvent(IntEnum):
	ADDED = auto()
	LISTED = auto()
	DETAILS_LOADED = auto()


class Controller:
	def __init__(self):
		self.listeners = defaultdict(list)
	
	def listen(self, event, callback):
		self.listeners[event].append(callback)
	
	def notify(self, event, *args, **kwargs):
		for callback in self.listeners.get(event, []):
			callback(*args, **kwargs)


class PalletController(Controller):
	def create_pallet(self):
		with Session() as session:
			query = select(func.count()).select_from(Pallet)
			count = session.scalar(query)
			code = f'P{count + 1}'
			pallet = Pallet(code=code)
			session.add(pallet)
			session.commit()

		dto = {'id': pallet.id, 'code': pallet.code}
		self.notify(ControllerEvent.ADDED, dto)
	
	def list_pallets(self):
		with Session() as session:
			query = select(Pallet.id, Pallet.code)
			result = session.execute(query)
			dtos = list(
				map(
					lambda x: {'id': x[0], 'code': x[1]},
					result.all()
				)
			)

		self.notify(ControllerEvent.LISTED, dtos)
	
	def load_details(self, pallet_id):
		with Session() as session:
			query = (
				select(Pallet.created_at, Pallet.finished_at)
				.where(Pallet.id == pallet_id)
			)
			result = session.execute(query)
			created_at, finished_at = result.one()
		
		dto = {
			'created_at': created_at.strftime('%x'),
			'finished_at': finished_at.strftime('%x') if finished_at else 'Não Finalizado'
		}
		self.notify(ControllerEvent.DETAILS_LOADED, dto)


class BoxController(Controller):
	def create_box(self, pallet_dto):
		with Session() as session:
			query = (
				select(func.count())
				.select_from(Box)
				.where(Box.pallet_id == pallet_dto['id'])
			)
			count = session.scalar(query)
			code = f'{pallet_dto["code"]}C{count + 1}'
			box = Box(code=code, pallet_id=pallet_dto['id'])
			session.add(box)
			session.commit()
			dto = {'id': box.id, 'code': code}
		
		self.notify(ControllerEvent.ADDED, dto)

	def list_boxes(self, pallet_id):
		with Session() as session:
			query = (
				select(Box.id, Box.code)
				.where(Box.pallet_id == pallet_id)
			)
			result = session.execute(query)
			dtos = list(
				map(
					lambda x: {'id': x[0], 'code': x[1]},
					result.all()
				)
			)
		
		self.notify(ControllerEvent.LISTED, dtos)
	
	def load_details(self, box_id):
		with Session() as session:
			query = (
				select(Box.created_at, Box.finished_at)
				.where(Box.id == box_id)
			)
			result = session.execute(query)
			created_at, finished_at = result.one()
			
		dto = {
			'created_at': created_at.strftime('%x'),
			'finished_at': finished_at.strftime('%x') if finished_at else 'Não Finalizada'
		}
		self.notify(ControllerEvent.DETAILS_LOADED, dto)


class BoxProductController(Controller):
	def add_product(self):
		pass