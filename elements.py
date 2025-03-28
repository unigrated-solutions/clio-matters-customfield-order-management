import time
import logging

from nicegui import ui, app
from nicegui.events import KeyEventArguments

logging.basicConfig(level=logging.DEBUG)

def generate_selection_range(number1, number2):
    """Generates a range excluding both number1 and number2."""
    if number1 < number2:
        return range(number1 + 1, number2)  # Excludes both ends
    elif number1 > number2:
        return range(number1 - 1, number2, -1)  # Excludes both ends
    return []  # If both numbers are the same, return an empty range

def calculate_final_positions(custom_fields, moving_ids, target_position):
    """
    Calculates the final positions of all items after moving selected cards.

    Parameters:
    - custom_fields (list): List of dictionaries with 'display_order'.
    - moving_ids (list): List of current positions to be moved.
    - target_position (int): The position where items should be inserted.

    Returns:
    - list: Updated list of custom fields with adjusted positions.
    """
    # Sort moving items by their current position
    moving_items = sorted(
        [item for item in custom_fields if item["display_order"] in moving_ids],
        key=lambda x: x["display_order"]
    )

    # Get remaining items (excluding moving items)
    remaining_items = [item for item in custom_fields if item["display_order"] not in moving_ids]

    # Count how many moving items came from below the target position
    count_below_target = sum(1 for item in moving_items if item["display_order"] < target_position)

    # Adjust the insertion position dynamically
    adjusted_target_position = target_position - count_below_target

    # Create a new list for the reordered items
    new_items = []

    for idx, item in enumerate(remaining_items):
        if idx == adjusted_target_position:
            new_items.extend(moving_items)  # Insert all moving items at the correct spot
        new_items.append(item)

    # If adjusted_target_position is at the end, append moving items
    if adjusted_target_position >= len(remaining_items):
        new_items.extend(moving_items)

    # Reassign `display_order` values
    for idx, item in enumerate(new_items):
        item["display_order"] = idx + 1  # Keep positions starting from 1

    return new_items

def move_selected_cards(target_position=5):
    """Gathers selected cards, updates positions, and regenerates UI in new order."""
    cards = app.storage.tab['cards']
    custom_fields = app.storage.general['custom_fields']
    
    # Get selected cards
    selected_cards = [card for card in cards if card.selected]
    ui.notify(selected_cards)
    
    if not selected_cards:
        ui.notify("No cards selected!", color="red")
        return

    # Extract moving IDs
    moving_ids = [card.display_order for card in selected_cards]

    # Calculate new positions
    updated_fields = calculate_final_positions(custom_fields, moving_ids, target_position)

    # **Update the global `custom_fields` with the new order**
    app.storage.general['custom_fields'] = sorted(updated_fields, key=lambda x: x["display_order"])  # Sort by position
    app.storage.tab['card_list'].refresh()
    for field_set in app.storage.tab['field_set_cards']:

        field_set.reorder_custom_fields.refresh()

    # Notify success
    ui.notify(f"Moved {len(selected_cards)} cards to position {target_position}!", color="green")

class EventHandler:
    def __init__(self):
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
                # ui.notify('Shift Down')
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
            
    def handle_card_click(self, custom_field_card):
        # ui.notify(custom_field_card)
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
    
    def toggle_deleted_field_visibility(self, value):
        for card in self.custom_field_cards:
            if card.deleted:
                card.set_visibility(value)
            
class CustomFieldCard:
    """A reusable card component for displaying and filtering custom fields."""

    def __init__(self, field_data, event_handler: EventHandler):
        """Initialize the card with field data."""
        
        self.event_handler = event_handler
        self.field_data = field_data
        self.selected = False  # Track whether the card is selected

        # Create a card with default styles
        self.card = ui.card().tight().style('width: 100%; cursor: pointer; transition: background-color 0.3s; padding: 5px;')

        # Bind name and position dynamically from field data
        self.id = field_data["id"]
        self.name = field_data["name"]
        self.display_order = field_data["display_order"]  # Ensure position updates dynamically
        self.deleted = field_data["deleted"]
        
        if self.deleted:
            self.name += (": (Deleted)")
            
        with self.card:
            with ui.context_menu():
                ui.menu_item("Insert Above", lambda: move_selected_cards(self.display_order - 1))
                ui.menu_item('Insert Below', lambda: move_selected_cards(self.display_order))
                
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
        self.card = ui.card().classes('w-full justify-center')
        self.reorder_custom_fields()  # initial layout call

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
            ui.label(self.name).classes('text-xl font-bold w-full text-center')

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
