from kivymd.app import MDApp
from kivy.lang import Builder
from kivymd.uix.screen import MDScreen
from functools import partial
from kivy.clock import Clock
from kivymd.uix.dialog import MDDialog
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.button import MDFlatButton
from kivy.properties import (
	ObjectProperty,
	StringProperty,
	DictProperty,
)
from controllers import (
	PalletController,
	ControllerEvent,
	BoxController,
)
from kivymd.uix.list import (
	MDList,
	OneLineAvatarIconListItem,
	IconLeftWidgetWithoutTouch,
)


class PalletsScreen(MDScreen):
	pass


class PalletDetailsScreen(MDScreen):
	pallet_dto = DictProperty()
	code = StringProperty()
	created_at = StringProperty()
	finished_at = StringProperty()

	def on_enter(self, *args):
		App.get_running_app().box_controller.list_boxes(self.pallet_dto['id'])
	
	def on_leave(self, *args):
		self.ids.boxes_list.clear_widgets()
	
	def on_pallet_dto(self, sender, pallet_dto):
		self.code = pallet_dto['code']
		controller = App.get_running_app().pallet_controller
		controller.listen(ControllerEvent.DETAILS_LOADED, self.when_details_loaded)
		controller.load_details(pallet_dto['id'])
	
	def when_details_loaded(self, details_dto):
		self.created_at = details_dto['created_at']
		self.finished_at = details_dto['finished_at']
	
	def hide_spinner(self):
		self.ids.spinner.active = False


class PalletsList(MDList):
	controller = ObjectProperty()
	
	def on_controller(self, _, controller):
		controller.listen(ControllerEvent.ADDED, self.when_added)
		controller.listen(ControllerEvent.LISTED, self.when_listed)

	def when_added(self, pallet_dto):
		self.add_item(pallet_dto)
	
	def when_listed(self, pallet_dtos):
		for dto in pallet_dtos:
			Clock.schedule_once(
				lambda _, d=dto: self.add_item(d)
			)
	
	def add_item(self, pallet_dto):
		item = OneLineAvatarIconListItem(text=pallet_dto['code'])
		icon = IconLeftWidgetWithoutTouch(icon='shipping-pallet')
		item.on_release = partial(self.when_item_clicked, pallet_dto)
		item.add_widget(icon)
		Clock.schedule_once(
			lambda _, i=item: self.add_widget(i)
		)
	
	def when_item_clicked(self, pallet_dto):
		App.get_running_app().inspect_pallet(pallet_dto)


class BoxDetailsScreen(MDScreen):
	box_dto = DictProperty()
	code = StringProperty()
	created_at = StringProperty()
	finished_at = StringProperty()

	def on_box_dto(self, sender, box_dto):
		self.code = box_dto['code']
		controller = App.get_running_app().box_controller
		controller.listen(ControllerEvent.DETAILS_LOADED, self.when_details_loaded)
		controller.load_details(box_dto['id'])
	
	def when_details_loaded(self, details_dto):
		self.created_at = details_dto['created_at']
		self.finished_at = details_dto['finished_at']


class BoxesList(MDList):
	controller = ObjectProperty()
	
	def on_controller(self, sender, controller):
		controller.listen(ControllerEvent.LISTED, self.when_listed)
		controller.listen(ControllerEvent.ADDED, self.when_added)
	
	def when_added(self, box_dto):
		self.add_item(box_dto)
	
	def when_listed(self, box_dtos):
		for dto in box_dtos:
			Clock.schedule_once(
				lambda _, d=dto: self.add_item(d)
			)
	
	def add_item(self, box_dto):
		item = OneLineAvatarIconListItem(text=box_dto['code'])
		icon = IconLeftWidgetWithoutTouch(icon='dropbox')
		item.on_release = partial(self.when_item_clicked, box_dto)
		item.add_widget(icon)
		self.add_widget(item)
	
	def when_item_clicked(self, box_dto):
		App.get_running_app().inspect_box(box_dto)


class AddProductDialogContent(MDBoxLayout):
	pass


class App(MDApp):
	def __init__(self):
		super().__init__()
		self.add_product_dialog = None
		self.pallet_controller = PalletController()
		self.box_controller = BoxController()
		self.pallet_controller.listen(ControllerEvent.ADDED, self.inspect_pallet)
		self.box_controller.listen(ControllerEvent.ADDED, self.inspect_box)

	def build(self):
		self.theme_cls.theme_style = 'Dark'
		self.theme_cls.primary_palette = 'Blue'
		return Builder.load_file('ui.kv')
	
	def on_start(self):
		self.pallet_controller.list_pallets()
	
	def create_pallet(self):
		self.pallet_controller.create_pallet()
	
	def inspect_pallet(self, pallet_dto):
		screen = self.root.get_screen('pallet_details')
		screen.pallet_dto = pallet_dto
		self.go_to('pallet_details', 'left')
	
	def create_box(self, pallet_dto):
		self.box_controller.create_box(pallet_dto)
	
	def inspect_box(self, box_dto):
		screen = self.root.get_screen('box_details')
		screen.box_dto = box_dto
		self.go_to('box_details', 'left')
	
	def go_to(self, screen, direction):
		self.root.transition.direction = direction
		self.root.current = screen
	
	def open_product_dialog(self):
		if not self.add_product_dialog:
			self.add_product_dialog = MDDialog(
			title='Adicionar Produto',
			type='custom',
			content_cls=AddProductDialogContent(),
			buttons=[
				MDFlatButton(text='Adicionar')
			]
		)
		self.add_product_dialog.open()


if __name__ == '__main__':
	App().run()