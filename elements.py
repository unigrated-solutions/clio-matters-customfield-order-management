import time
import logging

from nicegui import ui, app
from nicegui.events import KeyEventArguments

from api import *

logging.basicConfig(level=logging.DEBUG)

async def confirm_dialog(message: str = "Are you sure?") -> ui.dialog:
    def key_press(e: KeyEventArguments):
        if e['key'] == 'Enter':
            dialog.submit(True)
        elif e['key'] == 'Escape':
            dialog.submit(False)
            
    with ui.dialog() as dialog, ui.card():
        ui.label(message).classes('text-lg').style('white-space: pre-line')

        with ui.row().classes('justify-end'):
            ui.button('Cancel', on_click=lambda: dialog.submit(False)).props('flat')
            ui.button('Confirm', on_click=lambda: dialog.submit(True)).props('color=primary')

        # Handle keyboard shortcuts
        dialog.on('keydown', lambda e: key_press(e.args))

    dialog.open()
    result = await dialog
    return result
    
class ExpandableRightDrawer(ui.right_drawer):
    def __init__(self, event_handler):
        super().__init__(bordered=True)
        
        self.event_handler = event_handler
        self.expanded = False  # track the state

        # Create the drawer
        with self.props('width=50').style(self.get_drawer_style()):
            
            self.toggle_row = ui.row().classes('w-full').style(self.get_toggle_row_style())
            with self.toggle_row:
                self.toggle_button = ui.button(on_click=self.toggle).style('''
                    width: 40px;
                    height: 40px;
                    min-width: 40px;
                    padding: 0;
                    margin: 0;
                ''')
                ui.separator()
                self.update_button_icon()
                
                
            with ui.column().style('gap: 8px;').bind_visibility_from(self, 'expanded').style('align-items: center;').classes('w-full') as self.contents:

                self.parent_type_menu = ui.button(f'{self.event_handler.parent_type.capitalize()} Custom Fields', icon='expand_more', on_click=None).style('''
                    font-weight: bold;
                    color: white;
                    text-transform: capitalize;
                    background-color: #1976d2;
                    border: 1px solid #ccc;
                    border-radius: 4px;
                ''')
                                
                with self.parent_type_menu:
                    with ui.menu():
                        ui.menu_item('Matter Custom Fields', on_click=lambda: self.set_parent_type('matter'))
                        ui.menu_item('Contacts Custom Fields', on_click=lambda: self.set_parent_type('contact'))
    
                # ui.button('Show Confirmation', on_click=lambda: await confirm_dialog("Do you want to proceed?"))
                ui.button("Create Field", on_click=lambda: self.event_handler.field_handler.create_field())
    
    async def set_parent_type(self, type):
        await self.event_handler.set_parent_type(type)
        self.parent_type_menu.set_text(f'{self.event_handler.parent_type.capitalize()} Custom Fields')
        
    def get_drawer_style(self) -> str:
        if self.expanded:
            return '''
                transition: width 0.3s ease;
                padding-top: 12px;
                padding-left: 12px;
                padding-right: 12px;
                align-items: center;
            '''
        else:
            return '''
                transition: width 0.3s ease;
                padding-top: 12px;
                padding-left: 0px;
                padding-right: 0px;
            '''
        
    def get_toggle_row_style(self) -> str:
        return '''
            justify-content: flex-start;
        ''' if self.expanded else '''
            justify-content: center;
        '''
        
    def toggle(self):
        self.expanded = not self.expanded

        # Update width using props (the last one wins)
        new_width = '300' if self.expanded else '50'
        self.props(f'width={new_width}').style(self.get_drawer_style())

        # Update toggle row alignment
        self.toggle_row.style(self.get_toggle_row_style())

        self.update_button_icon()

    def update_button_icon(self):
        self.toggle_button.props(f"icon={'chevron_right' if self.expanded else 'chevron_left'}")

class EventHandler:
    def __init__(self, parent_type):
        
        self.page_container = None
        self.api_client = create_client_session()
        self.parent_type = parent_type
        self.field_handler = None
        self.field_set_handler = None
        
        self.custom_field_cards = []
        self.mousedown = False
        self.shift_down = False
        self.ctrl_down = False
        self.keyboard = ui.keyboard(on_key=self.handle_key)

        self.last_card_clicked = None
        self.last_card_click_timestamp = 0
        
        self.is_editing_field = False
        self.editing_field = None

        self.fields_selected_count = 0
        
    def init_handlers(self, page_container):
        field_set_handler = CustomFieldSetsHandler(event_handler=self, parent_type=self.parent_type)
        field_handler = CustomFieldsHandler(event_handler=self, field_set_handler=field_set_handler, parent_type=self.parent_type)
        field_set_handler.update_field_handler(field_handler)
        
        self.field_handler = field_handler
        self.field_set_handler = field_set_handler
        
        self.page_container = page_container
        return self.field_handler, self.field_set_handler
    
    def update_access_token(self, api_key):
        ui.notify(f'Setting Access Token')
        self.api_client.set_bearer_token(api_key)
    
    def set_custom_field_cards(self, field_cards: list):
        self.custom_field_cards = field_cards

    def set_shift(self, position: bool):
        self.shift_down = position

    def set_ctrl(self, position: bool):
        self.ctrl_down = position

    async def handle_key(self, e: KeyEventArguments):
        # print(e.key)
        if e.key == 'Shift':
            if e.action.keydown:
                ui.notify('Shift Down')
                self.shift_down = True
            if e.action.keyup:
                self.shift_down = False
                # ui.notify('Shift Up')
        
        if e.key == 'Control':
            if e.action.keydown:
                # ui.notify('Control Down')
                self.ctrl_down = True
            if e.action.keyup:
                self.ctrl_down = False
                # ui.notify('Control Up')

        if e.key == "Escape":
            self.deselect_all_fields()
            
        # WARNING field will show as "deleted" in Clio's "modify order" tool
        if e.key == 'Delete' and e.action.keydown:
            await self.field_handler.delete_custom_fields()
        
        if e.key == 'd' and self.ctrl_down and e.action.keydown:
            self.toggle_display_deleted()   
        
        if e.key == 'n' and self.ctrl_down and e.action.keydown:
            await self.field_handler.show_field_creation_dialog()
            
        if e.key == 'F2' and e.action.keydown:
            if self.fields_selected_count == 1:
                self.last_card_clicked.toggle_name_changing()
        
        else:
            print(e.key)
            print(self.fields_selected_count)
            
    def handle_card_click(self, custom_field_card):
        
        # Save the previous clicked card before updating
        last_card = self.last_card_clicked  
        last_cards_position = last_card.display_order if last_card else None 
        # Update the last clicked card and timestamp
        self.last_card_clicked = custom_field_card

        # Deselect all if no modifier keys are held
        if not self.ctrl_down and not self.shift_down and custom_field_card != last_card:
            # print("Deselecting all")
            self.deselect_all_fields()
              
        # If Shift is held and a previous card exists, select the range
        elif self.shift_down and last_cards_position is not None:
            current_card_position = custom_field_card.display_order
            if last_cards_position != current_card_position:  # Ensure it's a different card
                selection_range = self.generate_selection_range(last_cards_position, current_card_position)
                self.select_cards_from_range(selection_range)
                self.increment_field_count()  

        if custom_field_card == last_card and last_card.selected:
            self.decrement_field_count()
            
        else:
            self.increment_field_count()            
            
    def increment_field_count(self):
        self.fields_selected_count += 1
        
    def decrement_field_count(self):
        self.fields_selected_count = max(0, self.fields_selected_count - 1)

    def generate_selection_range(self,number1, number2):
        """Generates a range excluding both number1 and number2."""
        if number1 < number2:
            return range(number1 + 1, number2)  # Excludes both ends
        elif number1 > number2:
            return range(number1 - 1, number2, -1)  # Excludes both ends
        return []  # If both numbers are the same, return an empty range

    def select_cards_from_range(self, valid_range):
        for card in self.custom_field_cards:
            # print(card.display_order)
            if card.display_order in valid_range:
                card.select_card()

    def deselect_all_fields(self):
        for card in self.custom_field_cards:
            card.deselect_card()
    
        self.fields_selected_count = 0
        
    def do_nothing(self):
        pass
    
    def toggle_display_deleted(self):
        app.storage.tab["display_deleted"] = not app.storage.tab.get("display_deleted", False)
                    
    async def toggle_parent_type(self):
        self.parent_type= "contact" if self.parent_type == "matter" else "matter"
        await self.field_handler.load_from_storage()

    async def set_parent_type(self, type):
        self.parent_type= type
        await self.field_handler.load_from_storage()
        
class CustomFields:
    def __init__(self, field_data, event_handler: EventHandler, field_handler):
        self.event_handler = event_handler
        self.field_handler = field_handler
        self.field_data = field_data

class CustomField(ui.card):
    def __init__(self, field_data={}, event_handler: EventHandler = None, field_handler=None):
        super().__init__()
        self.event_handler = event_handler
        self.field_handler = field_handler
        self.field_data = field_data
        self.selected = False

        self.id = field_data.get("id")
        self.name = "Test" #field_data.get("name")
        self.parent_type = field_data.get("parent_type")
        self.display_order = 0 # field_data.get("display_order")
        self.deleted = field_data.get("deleted")

        # Full height and centered content
        # with self.tight().style('width: 100%; justify-content: space-between; align-items: center; cursor: pointer; transition: background-color 0.3s; padding: 5px;'):
        with self.tight().style('width: 100%; cursor: pointer; transition: background-color 0.3s; padding: 5px;'):
            with ui.context_menu():
                ui.menu_item("Insert Above", lambda: self.field_handler.move_selected_cards(self.id, "before", self.parent_type))
                ui.menu_item('Insert Below', lambda: self.field_handler.move_selected_cards(self.id, "after", self.parent_type))
                
                
            with ui.row().style('width: 100%; justify-content: space-between;'):
                with ui.column():
                    self.name_label = ui.label().bind_text_from(self, 'name').style('font-size: 1.3em; font-weight: bold; color: #333;')
                with ui.column():
                    with ui.row():
                        ui.label('Display Order:').style('font-size: 1.3em; font-weight: bold; color: #333;')
                        ui.label().bind_text_from(self, 'display_order').style('font-size: 1.3em; font-weight: bold; color: #333;')  # Ensure position updates in UI

class CustomFieldCard:
    """A reusable card component for displaying and filtering custom fields."""

    def __init__(self, field_data, event_handler: EventHandler, field_handler):
        """Initialize the card with field data."""
        
        self.event_handler = event_handler
        self.field_handler = field_handler
        self.field_data = field_data
        self.selected = False 
        self.updating_name = False
        self.updating = False
        
        self.name_change = None
        self.last_click= time.time()
        
        # Bind name and position dynamically from field data
        self.id = field_data["id"]
        self.parent_type = field_data.get("parent_type", "").lower()
        self.name = field_data["name"]
        self.field_type = field_data['field_type']
        self.displayed = field_data['displayed'] #Default in clio
        self.deleted = field_data["deleted"]
        self.required = field_data['required']
        self.display_order = field_data["display_order"]
        if field_data.get('picklist_options'):
            self.picklist_options = field_data['picklist_options']
        else:
            self.picklist_options = None
        
        # Create a card with default styles
        self.card = ui.card().tight().style('width: 100%; cursor: pointer; transition: background-color 0.3s; padding: 5px;')

        
        self.label_style = 'font-size: 1.3em; font-weight: bold; color: #333;'
        self.labels = []
        
        if self.deleted:
            self.name += (": (Deleted)")
            self.card.bind_visibility_from(app.storage.tab, 'display_deleted')
            
        with self.card:
            with ui.context_menu():
                # Always Show
                ui.menu_item('Copy Id', self.copy_id)
                
                # Only show these when more than one field is selected
                ui.menu_item("Insert Above", lambda: self.field_handler.move_selected_cards(self.id, "before")) \
                    .bind_visibility_from(self.event_handler, 'fields_selected_count', backward=lambda v: v >= 1 and not self.selected)
                ui.menu_item("Insert Below", lambda: self.field_handler.move_selected_cards(self.id, "after")) \
                    .bind_visibility_from(self.event_handler, 'fields_selected_count', backward=lambda v: v >= 1 and not self.selected)
                
                # Only show these when less than two field is selected
                ui.menu_item("Duplicate", on_click=self.duplicate_field) \
                    .bind_visibility_from(
                        self.event_handler,
                        'fields_selected_count',
                        backward=lambda v: (v == 1 and self.selected) or (v == 0 and not self.selected)
                    )
                # ui.menu_item("Copy", on_click=lambda: ui.notify(self.to_dict())) \
                #     .bind_visibility_from(self.event_handler, 'fields_selected_count', backward=lambda v: (v == 1 and self.selected) or (v == 0 and not self.selected)
                #     )
                    
                ui.menu_item("Create Field Above", on_click=lambda: self.field_handler.show_field_creation_dialog(display_order=self.display_order -1)) \
                    .bind_visibility_from(self.event_handler, 'fields_selected_count', backward=lambda v: (v == 1 and self.selected) or (v == 0 and not self.selected) )
                
                ui.menu_item("Create Field Below", on_click=lambda: self.field_handler.show_field_creation_dialog(display_order=self.display_order +1)) \
                    .bind_visibility_from(self.event_handler, 'fields_selected_count', backward=lambda v: (v == 1 and self.selected) or (v == 0 and not self.selected) )
                    
            with ui.row().style('width: 100%; justify-content: space-between; align-items: center;'):
                with ui.column():
                    self.name_label = ui.label().bind_text_from(self, 'name').style(self.label_style).bind_visibility_from(self, 'updating_name', backward=lambda v: not v)
                    self.labels.append(self.name_label)
                    
                    self.name_change = ui.input(value=self.name).props('autofocus v-model="text" dense="dense" size=48').bind_visibility_from(self, 'updating_name').style(self.label_style)
                    self.name_change.on('keydown.enter', lambda e: self.update_name(e.sender.value))
                    self.name_change.on('keydown.escape', self.toggle_name_changing)
                
            
                with ui.row().style('align-items: center; gap: 16px;'):
                    # Group 1: Checkboxes
                    with ui.row().style('align-items: center; gap: 8px;'):
                        ui.checkbox('Default', on_change= lambda e: self.update_default(e.sender.value) if not self.updating else None).bind_value_from(self, 'displayed')
                        ui.checkbox('Required', on_change= lambda e: self.update_required(e.sender.value) if not self.updating else None).bind_value_from(self, 'required')

                    # Group 2: Position labels
                    with ui.row().style('align-items: center; gap: 4px;'):
                        self.labels.append(ui.label('Position:').style('font-weight: bold;'))
                        self.labels.append(ui.label().bind_text_from(self, 'display_order'))
                        # Add click event for selection
        
        self.card.on('click', lambda: self.on_click())
        self.card.on('dblclick', self.toggle_name_changing)

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "field_type": self.field_type,
            "displayed": self.displayed,
            "deleted": self.deleted,
            "required": self.required,
            "display_order": self.display_order,
            "picklist_options": self.picklist_options,
        }

    async def duplicate_field(self):
        data = self.to_dict()
        data['display_order'] = self.display_order + 1  # or += 1 for safety

        # Ensure field_handler is available on the instance
        await self.field_handler.show_field_creation_dialog(
            name=data.get('name'),
            field_type=data.get('field_type'),
            default=data.get('displayed'),
            required=data.get('required'),
            display_order=data.get('display_order'),
            picklist_options=data.get('picklist_options'),
        )
    
    async def on_click(self):
        self.last_click = time.time()  # Move this up!

        self.event_handler.handle_card_click(self)

        if self.selected:
            self.deselect_card()
        else:
            self.select_card()
        
    async def copy_id(self):
        ui.run_javascript(f'navigator.clipboard.writeText("{self.id}")')
        ui.notify('Copied to clipboard')
    
    def select_card(self):
        """Select this card and update its background color."""
        self.selected = True
        self.card.style('background-color: lightblue;')  # Highlight the card
        
    def deselect_card(self):
        """Deselect this card and remove highlight."""
        self.selected = False
        self.card.style('background-color: white;')  # Remove highlight
        if time.time() > self.last_click + .2:
            self.updating_name= False
        
    def update_visibility(self, search_text):
        """Toggle visibility based on filter input."""
        self.card.visible = search_text.lower() in self.field_data["name"].lower()
        logging.debug(f"Card '{self.field_data['name']}' visibility: {self.card.visible}")

    def set_visibility(self, value):
        self.card.visible = value
        
    def update_position(self, new_position):
        """Update the card's current position dynamically."""
        self.display_order = new_position

    def toggle_name_changing(self):
        self.updating_name = True if not self.updating_name else False
        if self.updating_name:
            self.select_card()
        
    def update_name(self, new_name):
        success = update_custom_field(self.event_handler.api_client, self.id, name=new_name)
        if success:
            self.field_data['name'] = new_name
            self.name = new_name
            self.updating_name = False
            ui.notify(f"Successfully updated Name: {new_name}")
    
    async def update_default(self, displayed):
        if self.updating or self.displayed == displayed:
            return
        self.updating = True
        success = update_custom_field(self.event_handler.api_client, self.id, displayed=displayed)
        if success:
            self.displayed = displayed
            ui.notify(f"Successfully updated Default: {displayed}")
        self.updating = False
            
    async def update_required(self, is_required):
        if self.updating or self.required == is_required:
            return
        self.updating = True
        success = update_custom_field(self.event_handler.api_client, self.id, required=is_required)
        if success:
            self.required = is_required
            ui.notify(f"Successfully updated Required: {is_required}")
        self.updating = False
            
class CustomFieldSetCard:
    def __init__(self, field_set_data, event_handler):
        """Initialize the custom field set card with data."""
        self.field_set_data = field_set_data
        self.event_handler:EventHandler = event_handler
        
        self.id = field_set_data["id"]
        self.name = field_set_data["name"]
        self.parent_type = field_set_data.get("parent_type","").lower()
        self.custom_fields = field_set_data["custom_fields"]  # [{'id': 111}, {'id': 222}, ...]
        self.selected = False
        self.name_label = None
        self.updating_name = False
        
        # Lookup full custom field data from global storage
        all_fields = app.storage.general['custom_fields'][self.parent_type]
        custom_field_map = {field["id"]: field for field in all_fields if not field.get('deleted', False)}

        # Filter to get only associated fields, fully populated
        self.custom_field_data = [
            custom_field_map[f['id']]
            for f in self.custom_fields
            if f['id'] in custom_field_map
        ]

        # Sort by display_order
        self.custom_field_data.sort(key=lambda f: f['display_order'])

        # Card Layout
        self.card = ui.card().tight().classes('justify-center border border-gray-300 rounded-md').style('width: 100%; padding: 5px;')
        self.card.on('keydown', lambda: ui.notify("F2"))
        self.reorder_custom_fields()  # initial layout call

    def update_name(self, new_name):
        update_custom_field_set_label(self.event_handler.api_client, self.id, new_name)
        self.field_set_data['name'] = new_name
        self.name = new_name
        self.updating_name = False
        
    def selection_toggle(self):
        if not self.selected:
            self.selected = True
            self.name_label.style('background-color: lightblue;')
            
        else:
            self.selected = False
            self.name_label.style('background-color: whitesmoke;')
        
    def toggle_name_changing(self):
        self.updating_name = True if not self.updating_name else False
        
    #This needs to be redone to reorder the element index in the layout rather than clearing and regenerating
    @ui.refreshable
    def reorder_custom_fields(self):

        all_fields = app.storage.general['custom_fields'][self.parent_type]
        custom_field_map = {
            field['id']: field
            for field in all_fields
        }

        # Reconstruct custom_field_data from current storage
        self.custom_field_data = [
            custom_field_map[f['id']]
            for f in self.field_set_data['custom_fields']
            if f['id'] in custom_field_map
        ]

        # Sort by updated display_order
        self.custom_field_data.sort(key=lambda f: f['display_order'])

        self.card.clear()
        with self.card:
            # Header label
            name_change = ui.input(value=self.name).props('v-model="text" dense="dense" size=48').bind_visibility_from(self, 'updating_name').classes('text-xl font-bold w-full text-center border border-gray-300 rounded px-2 py-1').style('background-color: lightgray;').props('input-class="text-center"')
            name_change.on('keydown.enter', lambda e: self.update_name(e.sender.value))
            name_change.on('keydown.escape', self.toggle_name_changing)
            
            self.name_label = ui.label().bind_text_from(self, 'name').classes('text-xl font-bold w-full text-center border border-gray-300 rounded px-2 py-1').style('background-color: whitesmoke; cursor: pointer')
            self.name_label.bind_visibility_from(self, 'updating_name', backward=lambda v: not v)
            self.name_label.on('dblclick', self.toggle_name_changing)
            self.name_label.on('click', self.selection_toggle)
            
            with ui.grid(columns=2).classes('w-full gap-3'):
                for field in self.custom_field_data:
                    label = ui.label(field['name']).classes(
                        'text-lg font-semibold text-center border rounded p-3 bg-white shadow'
                    ).style(
                        'display: flex; align-items: center; justify-content: center; height: 100%; cursor: pointer'
                    )

                    if field.get('deleted', False):
                        label.bind_visibility_from(app.storage.tab, 'display_deleted')

class CustomFieldSetsHandler:
    def __init__(self, event_handler=None, field_handler = None, parent_type:str = None):
        self.event_handler:EventHandler = event_handler
        self.field_handler = field_handler
        self.parent_type = parent_type
        
        self.layout = None
        
    def load(self):
        if not self.layout:
            self.layout = ui.column().style('width: 100%;')
            
        with self.layout:
            for field_set in app.storage.general['custom_field_sets'][self.parent_type]:
                app.storage.tab['field_set_cards'].append(CustomFieldSetCard(field_set, self.event_handler))

    def update_field_handler(self, new_handler):
        self.field_handler = new_handler
        
    def update_parent_type(self, new_parent_type):
        self.parent_type = new_parent_type
        
    def update_field_sets(self) -> None:
        app.storage.tab['field_set_cards'].clear()
        self.layout.clear()
        app.storage.tab['field_set_cards'] = []
        with self.layout:
            for field_set in app.storage.general['custom_field_sets'][self.parent_type]:
                app.storage.tab['field_set_cards'].append(CustomFieldSetCard(field_set, self.event_handler))

    async def load_from_storage(self, parent_type="matter"):
        parent_type = self.event_handler.parent_type
        if parent_type != self.parent_type:
            self.parent_type = parent_type
        
        self.update_field_sets()
        
    async def load_from_api(self, parent_type="matter"):
        parent_type = self.event_handler.parent_type
        if parent_type != self.parent_type:
            self.parent_type = parent_type
            
        response = await run.io_bound(get_custom_field_sets, self.event_handler.api_client, self.parent_type)

        app.storage.general['custom_field_sets'][parent_type] = response.get('data', [])
        self.update_field_sets()
        
        if response:
            return True
        else:
            return False
            
class CustomFieldsHandler:
    def __init__(self, event_handler:EventHandler=None, field_set_handler:CustomFieldSetsHandler=None, parent_type:str = None):
        
        self.event_handler:EventHandler = event_handler
        self.field_set_handler:CustomFieldSetsHandler = field_set_handler
        self.parent_type = parent_type
        self.layout = None
        self.keyboard = ui.keyboard(on_key=self.handle_key)
    
    def load(self):
        fields:list = app.storage.tab['fields']
        
        with ui.column().classes('w-full'):
            with ui.column().classes('w-full').style('gap: 7px;') as self.layout:
                for custom_field in app.storage.general['custom_fields'][self.parent_type]:
                    field = CustomFieldCard(custom_field, self.event_handler, self)
                    fields.append(field)

                self.event_handler.set_custom_field_cards(fields)
    
        self.update_fields()
    
    async def handle_key(self, e: KeyEventArguments):

        # if e.key == "Escape":
        #     self.deselect_all_fields()
            
        # # WARNING field will show as "deleted" in Clio's "modify order" tool
        # if e.key == 'Delete' and e.action.keydown:
        #     await self.field_handler.delete_custom_fields()
        
        # if e.key == 'd' and self.ctrl_down and e.action.keydown:
        #     self.toggle_display_deleted()   
        
        # if e.key == 'n' and self.ctrl_down and e.action.keydown:
        #     await self.field_handler.show_field_creation_dialog()
            
        if e.key == 'F2' and e.action.keydown:
            ui.notify("F2 Keyboard event in field handler")
            # if self.fields_selected_count == 1:
            #     self.last_card_clicked.toggle_name_changing()
        
        else:
            ui.notify(f"{e.key} Keyboard event in field handler")
            # print(self.fields_selected_count)
                
    def update_field_set_handler(self, new_handler:CustomFieldSetsHandler):
        self.field_set_handler = new_handler
        
    def update_fields(self) -> None:

        custom_field_cards = app.storage.tab['fields']
        field_data = app.storage.general['custom_fields'][self.parent_type]
        for card in custom_field_cards:
            new_index = card.display_order
            card.card.move(target_index=new_index)
            storage_index = next((i for i, d in enumerate(field_data) if d['id'] == card.id), -1)
            app.storage.general['custom_fields'][self.parent_type][storage_index]['display_order'] = new_index
            
    def clear_and_refresh(self):
        fields:list = app.storage.tab['fields']
        fields.clear()
        self.layout.clear()
        with self.layout:
            for custom_field in app.storage.general['custom_fields'][self.parent_type]:
                field = CustomFieldCard(custom_field, self.event_handler, self)
                fields.append(field)

            self.event_handler.set_custom_field_cards(fields)

    async def load_from_storage(self):
        parent_type = self.event_handler.parent_type
        if parent_type != self.parent_type:
            self.parent_type = parent_type
            self.field_set_handler.update_parent_type(parent_type)

        self.clear_and_refresh()
        self.update_fields()

        if self.field_set_handler:
            ui.notify("Field set handler test")
            await self.field_set_handler.load_from_storage()
        
        app.storage.general['parent_type'] = parent_type

    async def load_from_api(self):
        parent_type = self.event_handler.parent_type
        if parent_type != self.parent_type:
            self.parent_type = parent_type
            self.field_set_handler.update_parent_type(parent_type)
        
        response = await run.io_bound(get_custom_fields, self.event_handler.api_client, parent_type)
        print(response)
        data = response.get('data', [])
        data = sorted(data, key=lambda x: x['display_order'])
        app.storage.general['custom_fields'][self.parent_type] = data
        self.clear_and_refresh()

        if self.field_set_handler:
            ui.notify("Field set handler test")
            await self.field_set_handler.load_from_api(parent_type=self.parent_type)
        app.storage.general['parent_type'] = parent_type
        
        if response:
            # ui.notify("Fields loaded from API")
            ui.notification(message=response, multi_line=True, timeout=None, close_button=True)
        else:
            ui.notify("Failed to Download Fields")

    #Replace with API patch call    
    def log_display_order_change(self, item_id, new_order):
        ui.notify(f"Moving item '{item_id}' to new display_order: {new_order}")        
        return True
    
    def update_position(self, item_id, new_order):
        ui.notify(f"Moving item '{item_id}' to new display_order: {new_order}")
        update_custom_field_display_order(self.event_handler.api_client, item_id, new_order)
        
        return True

    def move_item(self, moving_id, target_id, position, on_display_order_change):
        cards = app.storage.tab['fields']
        cards = sorted(cards, key=lambda x: x.display_order)

        moving_item = next(card for card in cards if card.id == moving_id)
        target_item = next(card for card in cards if card.id == target_id)

        moving_order = moving_item.display_order
        target_order = target_item.display_order

        if moving_order == target_order:
            return True

        if moving_order < target_order:
            if position == 'after':
                new_order = target_order
                success = on_display_order_change(moving_id, new_order)
                if success:
                    for card in cards:
                        if card.id == moving_id:
                            card.display_order = new_order
                        elif moving_order < card.display_order <= target_order:
                            card.display_order -= 1
                    return True

            elif position == 'before':
                new_order = target_order - 1
                success = on_display_order_change(moving_id, new_order)
                if success:
                    for card in cards:
                        if card.id == moving_id:
                            card.display_order = new_order
                        elif moving_order < card.display_order < target_order:
                            card.display_order -= 1
                    return True

        elif moving_order > target_order:
            if position == 'after':
                new_order = target_order + 1
                success = on_display_order_change(moving_id, new_order)
                if success:
                    for card in cards:
                        if card.id == moving_id:
                            card.display_order = new_order
                        elif target_order < card.display_order < moving_order:
                            card.display_order += 1
                    return True

            elif position == 'before':
                new_order = target_order
                success = on_display_order_change(moving_id, new_order)
                if success:
                    for card in cards:
                        if card.id == moving_id:
                            card.display_order = new_order
                        elif target_order <= card.display_order < moving_order:
                            card.display_order += 1
                    return True

        return False

    def bulk_move_items(self, moving_ids, target_id, position):
        cards = app.storage.tab['fields']

        # Map of id to card for lookup
        id_to_order = {card.id: card.display_order for card in cards}
        moving_ids = sorted(moving_ids, key=lambda x: id_to_order.get(x, float('inf')))

        first_move_complete = False
        for id in moving_ids:
            if not first_move_complete:
                success = self.move_item(id, target_id, position, self.update_position)
                if success:
                    first_move_complete = True
                    position = 'after'
                    target_id = id
            else:
                success = self.move_item(id, target_id, position, self.update_position)
                if success:
                    target_id = id
                    
    def move_selected_cards(self, target_id, position):
        cards = app.storage.tab['fields']

        selected_cards = [card for card in cards if card.selected]
        if not selected_cards:
            ui.notify("No cards selected!", color="red")
            return

        moving_ids = [card.id for card in selected_cards]
        if not moving_ids:
            return
        
        self.bulk_move_items(moving_ids, target_id, position)
        self.update_fields()
        
        if self.field_set_handler:
            self.field_set_handler.update_field_sets()
        
        self.event_handler.deselect_all_fields()
        
    async def delete_custom_fields(self):
        names = []
        ids = []
        
        for card in app.storage.tab['fields']:
            if card.selected:
                names.append(card.name)
                ids.append(card.id)
        message = f'You are about to delete the following fields:\n{names}'
        
        if await confirm_dialog(message):
            for id in ids:
                delete_custom_field(self.event_handler.api_client, id)
                ui.notify(f'Deleted: {id}')
        else:
            ui.notify("Cancelling deleting")

    def create_custom_field_dialog(
        self,
        name: str = None,
        field_type: str = None,
        default: bool = False,
        required: bool = False,
        display_order: int = None,
        picklist_options: list[dict] = None
    ) -> ui.dialog:
        
        field_types = [
            "checkbox", "contact", "currency", "date", "time", "email",
            "matter", "numeric", "picklist", "text_area", "text_line", "url"
        ]

        if not picklist_options:
            picklist_options: list[str] = []

        with ui.dialog() as create_dialog, ui.card().style('width: 500px;'):
            ui.label('Create Custom Field').classes('w-full text-xl font-bold')

            name_input = ui.input('Name').classes('w-full').props('dense')
            if name:
                name_input.set_value(name)

            field_type_input = ui.select(field_types, label='Field Type').classes('w-full').props('dense').style('text-transform: capitalize;')
            if field_type in field_types:
                field_type_input.set_value(field_type)

            # === Dynamic Picklist Entry ===
            picklist_container = ui.column().classes('w-full')
            picklist_container.bind_visibility_from(field_type_input, 'value', value='picklist')

            def add_picklist_input():
                with ui.row().classes('w-full gap-2 items-center').style('width: 100%;') as row:
                    input_field = ui.input(placeholder='Picklist option...') \
                        .props('dense') \
                        .style('flex: 1;')

                    # ✅ Proper way to focus the input
                    ui.run_javascript(f'getElement("{input_field.id}").$refs.qRef.focus()')

                    add_button = ui.button('➕').props('dense')

                    def handle_add():
                        value = input_field.value.strip()
                        if value and value not in picklist_options:
                            picklist_options.append(value)
                            row.clear()

                            with row:
                                ui.label(value).classes('font-bold').style('flex: 1;')

                                def handle_remove():
                                    picklist_options.remove(value)
                                    row.delete()

                                ui.button('❌', on_click=handle_remove).props('dense flat color=negative')

                            add_picklist_input()

                    add_button.on('click', handle_add)
                    input_field.on('keydown.enter', lambda _: handle_add())

            with picklist_container:
                if picklist_options:
                    for item in picklist_options:
                        value = item.get("option", "").strip()
                        if value:
                            with ui.row().classes('w-full gap-2 items-center').style('width: 100%;') as row:
                                ui.label(value).classes('font-bold').style('flex: 1;')

                                def remove_closure(v=value, r=row):
                                    def do_remove():
                                        picklist_options[:] = [opt for opt in picklist_options if opt.get("option") != v]
                                        r.delete()
                                    return do_remove

                                ui.button('❌', on_click=remove_closure()).props('dense flat color=negative')

                add_picklist_input()  # Add the first row

            # === End Picklist Section ===

            display_order_input = ui.input('Display Order (optional)').classes('w-full').props('dense')
            if display_order is not None:
                display_order_input.set_value(str(display_order))

            default_checkbox = ui.checkbox('Default').props('dense')
            if default:
                default_checkbox.set_value(True)

            required_checkbox = ui.checkbox('Required').props('dense')
            if required:
                required_checkbox.set_value(True)

            with ui.row().classes('justify-end'):
                ui.button('Cancel', on_click=lambda: create_dialog.submit(None)).props('flat')

                def handle_submit():
                    result = {
                        'name': name_input.value,
                        'field_type': field_type_input.value,
                        'default': default_checkbox.value,
                        'required': required_checkbox.value,
                        'display_order': display_order_input.value or None,
                    }
                    if result['field_type'] == 'picklist':
                        result['picklist_options'] = [
                            {'option': o['option']} if isinstance(o, dict) else {'option': o}
                            for o in picklist_options
                        ]
                    # if result['field_type'] == 'picklist':
                    #     result['picklist_options'] = picklist_options
                    create_dialog.submit(result)

                ui.button('Create', on_click=handle_submit).props('color=primary')

        return create_dialog

        
    async def show_field_creation_dialog(self, action_type= "post", **kwargs):
        with self.event_handler.page_container:
            dialog=  self.create_custom_field_dialog(**kwargs)
            result = await dialog
            
            if action_type == "post":
                print(result)
                await self.create_field(**result)

    async def create_field(self, **kwargs):
        response = await run.io_bound(create_custom_field, client=self.event_handler.api_client, parent_type=self.parent_type, **kwargs)
        ui.notification(message=response, multi_line=True, timeout=None, close_button=True)