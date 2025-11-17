import asyncio
from models import TrackedModel, BoxProduct
from kivymd.app import MDApp
from kivymd.uix.screen import MDScreen
from kivymd.uix.recycleview import MDRecycleView
from kivymd.uix.list import OneLineAvatarIconListItem
from kivy.clock import Clock
from kivy.lang import Builder
from kivymd.uix.list import (
	MDList,
	OneLineAvatarIconListItem,
	IconLeftWidgetWithoutTouch,
)
from kivy.properties import (
	ObjectProperty,
	StringProperty,
	DictProperty,
)
from controllers import (
	PalletController,
	BoxController,
	ProductController,
)


class ModelItem(OneLineAvatarIconListItem):
	display_icon = StringProperty()
	model = ObjectProperty()


class ModelRecycleView(MDRecycleView):
	controller = ObjectProperty()
	item_icon = StringProperty()
	when_item_pressed = ObjectProperty()
	
	def on_controller(self, _, controller):
		controller.listen('added', self.when_added)
		controller.listen('listed', self.when_listed)
	
	def get_dict(self, model):
		d =  {
			'model': model,
			'display_icon': self.item_icon,
			'when_item_pressed': self.when_item_pressed
		}
		
		if isinstance(model, TrackedModel):
			d['text'] = model.code
		elif isinstance(model, BoxProduct):
			d['text'] = model.product.name
	
		return d
	
	def when_added(self, model):
		self.data.append(self.get_dict(model))
	
	def when_listed(self, models):
		data = list(map(self.get_dict, models))
		self.data = data


class PalletsScreen(MDScreen):
	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		App.get_running_app().pallet_controller.listen('listed', self.when_pallets_listed)
	
	def when_pallets_listed(self, pallets):
		self.ids.container.remove_widget(self.ids.pallets_spinner)


class DetailsScreen(MDScreen):
	model = ObjectProperty()
	title = StringProperty('Título')
	inside_text = StringProperty()
	code = StringProperty('Código')
	created_at = StringProperty('Criação')
	finished_at = StringProperty('Finalização')
	go_back_to = StringProperty()
	controller = ObjectProperty()
	item_icon = StringProperty()
	when_item_pressed = ObjectProperty()

	def on_model(self, caller, model):			
		self.code = model.code
		self.created_at = model.created_at.strftime('%x')
		self.finished_at = model.finished_at.strftime('%x') if model.finished_at else 'Não Finalizado'
	
	def when_fab_press(self):
		match self.name:
			case 'pallet_details':
				App.get_running_app().create_box(self.model)
			case 'box_details':
				print('ADD PRODUCT YO BOX')


class App(MDApp):
	def __init__(self, session_cls):
		super().__init__()
		self.pallet_controller = PalletController(session_cls)
		self.box_controller = BoxController(session_cls)
		self.product_controller = ProductController(session_cls)
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
				),
			2
		)
	
	def create_pallet(self):
		asyncio.create_task(
			self.pallet_controller.add_new()
		)
	
	def create_box(self, pallet):
		asyncio.create_task(
			self.box_controller.add_new()
		)
	
	def inspect_pallet(self, pallet):
		self.box_controller.pallet = pallet
		asyncio.create_task(self.box_controller.list())
		screen = self.root.get_screen('pallet_details')
		screen.model = pallet
		self.go_to('pallet_details')
	
	def inspect_box(self, box):
		self.product_controller.box = box
		asyncio.create_task(self.product_controller.list())
		screen = self.root.get_screen('box_details')
		screen.model = box
		self.go_to('box_details')
	
	def go_to(self, screen, direction='left'):
		self.root.transition.direction = direction
		self.root.current = screen
