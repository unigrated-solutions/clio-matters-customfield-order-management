import time
import logging

from nicegui import ui, app
from nicegui.events import KeyEventArguments

from api import *

logging.basicConfig(level=logging.DEBUG)

def generate_selection_range(number1, number2):
    """Generates a range excluding both number1 and number2."""
    if number1 < number2:
        return range(number1 + 1, number2)  # Excludes both ends
    elif number1 > number2:
        return range(number1 - 1, number2, -1)  # Excludes both ends
    return []  # If both numbers are the same, return an empty range

class EventHandler:
    def __init__(self):
        
        self.field_handler = None
        self.field_set_handler = None
        
        self.custom_field_cards = []
        self.mousedown = False
        self.shift_down = False
        self.ctrl_down = False
        self.keyboard = ui.keyboard(on_key=self.handle_key)

        self.last_card_clicked = None
        self.last_card_click_timestamp = 0

    def set_custom_field_cards(self, field_cards: list):
        self.custom_field_cards = field_cards

    def set_shift(self, position: bool):
        self.shift_down = position

    def set_ctrl(self, position: bool):
        self.ctrl_down = position

    def handle_key(self, e: KeyEventArguments):
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
            self.deselect_all_cards()
        
        if e.key == 't' and self.ctrl_down and e.action.keydown:
            self.toggle_display_deleted()            
    def handle_card_click(self, custom_field_card):

        # Save the previous clicked card before updating
        last_card = self.last_card_clicked  # Store the old value before updating
        last_cards_position = last_card.display_order if last_card else None  # Correctly reference the last position

        # Update the last clicked card and timestamp
        self.last_card_click_timestamp = time.time()
        self.last_card_clicked = custom_field_card  # Now update with the new clicked card

        # Deselect all if no modifier keys are held
        if not self.ctrl_down and not self.shift_down:
            print("Deselecting all")
            self.deselect_all_cards()

        # If Shift is held and a previous card exists, select the range
        print(last_cards_position)
        if self.shift_down and last_cards_position is not None:
            current_card_position = custom_field_card.display_order
            if last_cards_position != current_card_position:  # Ensure it's a different card
                selection_range = generate_selection_range(last_cards_position, current_card_position)
                self.select_cards_from_range(selection_range)

    def select_cards_from_range(self, valid_range):
        for card in self.custom_field_cards:
            print(card.display_order)
            if card.display_order in valid_range:
                card.select_card()

    def deselect_all_cards(self):
        for card in self.custom_field_cards:
            card.deselect_card()
    
    def do_nothing(self):
        pass
    
    def toggle_display_deleted(self):
        app.storage.tab["display_deleted"] = not app.storage.tab.get("display_deleted", False)
    
    def toggle_deleted_field_visibility(self, value):
        for card in self.custom_field_cards:
            if card.deleted:
                card.set_visibility(value)
                
    def parent_type_changed(self, new_parent_type):
        ui.notify(f'Parent type set to: {new_parent_type}')
        
class CustomFieldCard:
    """A reusable card component for displaying and filtering custom fields."""

    def __init__(self, field_data, event_handler: EventHandler, field_handler):
        """Initialize the card with field data."""
        
        self.event_handler = event_handler
        self.field_handler = field_handler
        self.field_data = field_data
        self.selected = False  # Track whether a card is selected

        # Create a card with default styles
        self.card = ui.card().tight().style('width: 100%; cursor: pointer; transition: background-color 0.3s; padding: 5px;')

        # Bind name and position dynamically from field data
        self.id = field_data["id"]
        self.name = field_data["name"]
        self.parent_type = field_data.get("parent_type")
        self.display_order = field_data["display_order"]  # Ensure position updates dynamically
        self.deleted = field_data["deleted"]
        
        if self.deleted:
            self.name += (": (Deleted)")
            
        with self.card:
            with ui.context_menu():
                ui.menu_item("Insert Above", lambda: self.field_handler.move_selected_cards(self.id, "before"))
                ui.menu_item('Insert Below', lambda: self.field_handler.move_selected_cards(self.id, "after"))
                
                
            with ui.row().style('width: 100%; justify-content: space-between;'):
                with ui.column():
                    self.name_label = ui.label().bind_text_from(self, 'name').style(
                        'font-size: 1.3em; font-weight: bold; color: #333;'
                    )
                with ui.column():
                    with ui.row():
                        ui.label('Display Order:').style('font-weight: bold;')
                        ui.label().bind_text_from(self, 'display_order')  # Ensure position updates in UI

        # Add click event for selection
        self.card.on('click', self.on_click)
    
    def on_click(self, e: KeyEventArguments):
        """Toggle selection state and update styling."""
        self.event_handler.handle_card_click(self)
        print("card clicked")
        print(time.time())
        if self.selected:
            self.deselect_card()
        else:
            self.select_card()
    
    def select_card(self):
        """Select this card and update its background color."""
        self.selected = True
        self.card.style('background-color: lightblue;')  # Highlight the card
        # ui.notify(f'{self.field_data["name"]} Selected')
        # logging.debug(f"Card '{self.field_data['name']}' selected.")

    def deselect_card(self):
        """Deselect this card and remove highlight."""
        self.selected = False
        self.card.style('background-color: white;')  # Remove highlight
        # ui.notify(f'{self.field_data["name"]} Deselected')
        # logging.debug(f"Card '{self.field_data['name']}' deselected.")

    def update_visibility(self, search_text):
        """Toggle visibility based on filter input."""
        self.card.visible = search_text.lower() in self.field_data["name"].lower()
        logging.debug(f"Card '{self.field_data['name']}' visibility: {self.card.visible}")

    def set_visibility(self, value):
        self.card.visible = value
        
    def update_position(self, new_position):
        """Update the card's current position dynamically."""
        self.display_order = new_position

class CustomFieldSetCard:
    def __init__(self, field_set_data):
        """Initialize the custom field set card with data."""
        self.field_set_data = field_set_data
        self.id = field_set_data["id"]
        self.name = field_set_data["name"]
        self.parent_type = field_set_data.get("parent_type")
        self.custom_fields = field_set_data["custom_fields"]  # [{'id': 111}, {'id': 222}, ...]

        # Lookup full custom field data from global storage
        all_fields = app.storage.general['custom_fields']
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
        self.card = ui.card().classes('w-full justify-center border border-gray-300 rounded-md !bg-white')


        self.reorder_custom_fields()  # initial layout call

    #This needs to be redone to reorder the element index in the layout rather than clearing and regenerating
    @ui.refreshable
    def reorder_custom_fields(self):
        # 🔄 Re-fetch the latest field info from storage
        all_fields = app.storage.general['custom_fields']
        custom_field_map = {
            field['id']: field
            for field in all_fields
            # if not field.get('deleted', False)
        }

        # Reconstruct custom_field_data from current storage
        self.custom_field_data = [
            custom_field_map[f['id']]
            for f in self.field_set_data['custom_fields']
            if f['id'] in custom_field_map
        ]

        # Sort by updated display_order
        self.custom_field_data.sort(key=lambda f: f['display_order'])

        # 🔄 Clear and regenerate the grid UI
        self.card.clear()
        with self.card:
            # Header label
            ui.label(self.name).classes('text-xl font-bold w-full text-center border border-gray-300 bg-gray-100 rounded px-2 py-1')

            with ui.grid(columns=2).classes('w-full gap-3'):
                for field in self.custom_field_data:
                    label = ui.label(field['name']).classes(
                        'text-lg font-semibold text-center border rounded p-3 bg-white shadow'
                    ).style(
                        'display: flex; align-items: center; justify-content: center; height: 100%;'
                    )

                    # ✅ Bind visibility only if the field is deleted
                    if field.get('deleted', False):
                        label.bind_visibility_from(app.storage.tab, 'display_deleted')

class CustomFieldSetsHandler:
    def __init__(self, field_handler=None):
        self.layout = None
        self.field_handler = field_handler
        
    def load(self):
        if not self.layout:
            self.layout = ui.column().style('width: 100%; padding: 20px;')
        with self.layout:
            for field_set in app.storage.general['custom_field_sets']:
                app.storage.tab['field_set_cards'].append(CustomFieldSetCard(field_set))

    def update_field_handler(self, new_handler):
        self.field_handler = new_handler
        
    def update_field_sets(self) -> None:
        app.storage.tab['field_set_cards'].clear()
        self.layout.clear()
        app.storage.tab['field_set_cards'] = []
        with self.layout:
            for field_set in app.storage.general['custom_field_sets']:
                app.storage.tab['field_set_cards'].append(CustomFieldSetCard(field_set))

    async def load_from_api(self, parent_type="matter", client:Client=None):
        response = await run.io_bound(get_custom_field_sets, client, parent_type)

        app.storage.general['custom_field_sets'] = response.get('data', [])
        self.update_field_sets()
        
        if response:
            return True
        else:
            return False
            
class CustomFieldsHandler:
    def __init__(self, event_handler, field_set_handler:CustomFieldSetsHandler=None):
        self.event_handler:EventHandler = event_handler
        self.field_set_handler:CustomFieldSetsHandler = field_set_handler
        self.layout = None
        
    def load(self):
        fields:list = app.storage.tab['fields']
        
        with ui.column().classes('w-full'):
            with ui.column().classes('w-full').style('gap: 7px;') as self.layout:
                for custom_field in app.storage.general['custom_fields']:
                    field = CustomFieldCard(custom_field, self.event_handler, self)
                    fields.append(field)

                self.event_handler.set_custom_field_cards(fields)
    
    def update_field_set_handler(self, new_handler:CustomFieldSetsHandler):
        self.field_set_handler = new_handler
        
    @ui.refreshable
    def update_fields(self) -> None:
        # ui.notify("Refreshing Fields")
        custom_field_cards = app.storage.tab['fields']
        field_data = app.storage.general['custom_fields']
        for card in custom_field_cards:
            new_index = card.display_order
            card.card.move(target_index=new_index)
            storage_index = next((i for i, d in enumerate(field_data) if d['id'] == card.id), -1)
            app.storage.general['custom_fields'][storage_index]['display_order'] = new_index
            
    def clear_and_refresh(self):
        fields:list = app.storage.tab['fields']
        fields.clear()
        self.layout.clear()
        with self.layout:
            for custom_field in app.storage.general['custom_fields']:
                field = CustomFieldCard(custom_field, self.event_handler, self)
                fields.append(field)

            self.event_handler.set_custom_field_cards(fields)

    async def load_from_api(self, parent_type="matter", client:Client=None):
        parent_type = app.storage.tab['visible_parent_type']

        response = await run.io_bound(get_custom_fields, client, parent_type)
        print(response)
        data = response.get('data', [])
        data = sorted(data, key=lambda x: x['display_order'])
        app.storage.general['custom_fields'] = data
        self.clear_and_refresh()

        if self.field_set_handler:
            await self.field_set_handler.load_from_api(parent_type, client)
        app.storage.general['parent_type'] = parent_type
        
        if response:
            ui.notify("Fields loaded from API")
        else:
            ui.notify("Failed to Download Fields")

    #Replace with API patch call    
    def log_display_order_change(self, item_id, new_order):
        ui.notify(f"Moving item '{item_id}' to new display_order: {new_order}")        
        return True  # Simulate a successful result
    
    def update_position(self, item_id, new_order):
        ui.notify(f"Moving item '{item_id}' to new display_order: {new_order}")
        update_custom_field_display_order(app.storage.tab['api_client'], item_id, new_order)
        
        return True  # Simulate a successful result

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
        