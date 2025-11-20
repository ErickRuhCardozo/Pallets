import asyncio
from models import TrackedModel, BoxProduct
from kivymd.app import MDApp
from kivymd.uix.screen import MDScreen
from kivymd.uix.label import MDLabel
from kivymd.uix.recycleview import MDRecycleView
from kivymd.uix.boxlayout import MDBoxLayout
from kivy.clock import Clock
from kivy.lang import Builder
from kivymd.uix.list import (
	OneLineAvatarIconListItem,
	TwoLineAvatarIconListItem,
	IRightBody,
)
from kivy.properties import (
	ObjectProperty,
	StringProperty,
	DictProperty,
)
from controllers import (
	PalletController,
	BoxController,
	BoxProductController,
)


class TrackedModelItem(OneLineAvatarIconListItem):
	icon = StringProperty()
	model = ObjectProperty()


class BoxProductItem(TwoLineAvatarIconListItem):
	quantity = StringProperty()
	model = ObjectProperty()


class ProductQuantityLabel(IRightBody, MDLabel):
	pass


class ModelView(MDRecycleView):
	controller = ObjectProperty()
	item_icon = StringProperty()
	when_item_pressed = ObjectProperty()
	
	def on_controller(self, _, controller):
		controller.listen('added', self.when_added)
		controller.listen('listed', self.when_listed)
	
	def when_added(self, model):
		self.data.append(self.get_dict(model))
	
	def when_listed(self, models):
		data = list(map(self.get_dict, models))
		for dt in data:
			Clock.schedule_once(
				lambda _, d=dt: self.data.append(d)
			)


class TrackedModelView(ModelView):	
	def get_dict(self, model):
		return  {
			'text': model.code,
			'model': model,
			'icon': self.item_icon,
			'when_item_pressed': self.when_item_pressed
		}


class BoxProductView(ModelView):
	def get_dict(self, model):
		return  {
			'text': model.product.name,
			'secondary_text': model.product.ean,
			'quantity': str(model.quantity),
			'model': model,
			'when_item_pressed': self.when_item_pressed
		}


class PalletsScreen(MDScreen):	
	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		App.get_running_app().pallet_controller.listen('listed', self.when_pallets_listed)
	
	def when_pallets_listed(self, pallets):
		self.ids.container.remove_widget(self.ids.pallets_spinner)


class DetailsScreen(MDScreen):
	model = ObjectProperty()
	code = StringProperty('Código')
	created_at = StringProperty('Criação')
	finished_at = StringProperty('Finalização')
	controller = ObjectProperty()
	
	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.loading_spinner = None
	
	def on_kv_post(self, caller):
		self.loading_spinner = self.ids.loading_spinner
	
	def on_leave(self, *args):
		if App.get_running_app().can_hide_modelview(self.name):
			self.ids.modelview.opacity = 0
			self.ids.modelview.disabled = True
			self.ids.modelview.data = []
			self.ids.container.add_widget(self.loading_spinner, index=1)
	
	def on_model(self, caller, model):			
		self.code = model.code
		self.created_at = model.created_at.strftime('%x')
		self.finished_at = model.finished_at.strftime('%x') if model.finished_at else 'Não Finalizado'
	
	def on_controller(self, caller, controller):
		controller.listen('listed', self.when_controller_listed)
	
	def when_controller_listed(self, _):
		self.ids.modelview.opacity = 1
		self.ids.modelview.disabled = False
		self.ids.container.remove_widget(self.loading_spinner)


class PalletDetailsScreen(DetailsScreen):
	pass


class BoxDetailsScreen(DetailsScreen):
	pass


class App(MDApp):
	def __init__(self, session_cls):
		super().__init__()
		self.pallet_controller = PalletController(session_cls)
		self.box_controller = BoxController(session_cls)
		self.boxproduct_controller = BoxProductController(session_cls)
		self.pallet_controller.listen('added', self.inspect_pallet)
		self.box_controller.listen('added', self.inspect_box)

	def build(self):
		self.theme_cls.theme_style = 'Dark'
		self.theme_cls.primary_palette = 'Blue'
		return Builder.load_file('ui.kv')
	
	def on_start(self):
		Clock.schedule_once(
			lambda dt:
				asyncio.create_task(
					self.pallet_controller.list()
				)
		)
	
	def add_pallet(self):
		asyncio.create_task(
			self.pallet_controller.add_new()
		)
	
	def add_box(self, pallet):
		asyncio.create_task(
			self.box_controller.add_new()
		)
	
	def show_product_dialog(self):
		pass
	
	def inspect_pallet(self, pallet):
		self.box_controller.pallet = pallet
		screen = self.root.get_screen('pallet_details')
		screen.model = pallet
		self.go_to('pallet_details')
		asyncio.create_task(self.box_controller.list())
	
	def inspect_box(self, box):
		print('inspecting box', box.id)
		self.boxproduct_controller.box = box
		screen = self.root.get_screen('box_details')
		screen.model = box
		self.go_to('box_details')
		asyncio.create_task(self.boxproduct_controller.list())
	
	def go_to(self, screen, direction='left'):
		self.root.transition.direction = direction
		self.root.current = screen
	
	def can_hide_modelview(self, from_screen):
		in_pallets = self.root.current == 'pallets'
		in_pallet_details = self.root.current == 'pallet_details'
		
		if in_pallets and from_screen == 'pallet_details':
			return True
		elif in_pallet_details and from_screen == 'box_details':
			return True
		
		return False
