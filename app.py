#!/usr/bin/env python3
import time
import logging

from nicegui import ui, app
from nicegui.events import KeyEventArguments, ClickEventArguments

logging.basicConfig(level=logging.DEBUG)

# Sample custom fields data
custom_fields = [
    {"name": "Field 1", "display_order": 1},
    {"name": "Field 2", "display_order": 2},
    {"name": "Field 3", "display_order": 3},
    {"name": "Field 4", "display_order": 4},
    {"name": "Field 5", "display_order": 5},
    {"name": "Field 6", "display_order": 6},
    {"name": "Field 7", "display_order": 7},
    {"name": "Field 8", "display_order": 8},    
    {"name": "Field 9", "display_order": 9},
    {"name": "Field 10", "display_order": 10},
    {"name": "Field 11", "display_order": 11},
    {"name": "Field 12", "display_order": 12},    
    

]
cards = []
card_list = None
event_handler = None

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
    global cards, card_list, custom_fields

    # Get selected cards
    selected_cards = [card for card in cards if card.selected]

    if not selected_cards:
        ui.notify("No cards selected!", color="red")
        return

    # Extract moving IDs
    moving_ids = [card.display_order for card in selected_cards]

    # Calculate new positions
    updated_fields = calculate_final_positions(custom_fields, moving_ids, target_position)

    # **Update the global `custom_fields` with the new order**
    custom_fields = sorted(updated_fields, key=lambda x: x["display_order"])  # Sort by position

    # Clear old UI elements
    card_list.clear()
    cards.clear()

    # Regenerate UI with updated order
    with card_list:
        with ui.column().classes('w-full').style('gap: 7px;'):
            for field in custom_fields:  # **Using updated sorted custom_fields**
                card_instance = CustomFieldCard(field, event_handler)
                cards.append(card_instance)

    # Update event handler with new cards
    event_handler.set_custom_field_cards(cards)

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
        # print(e)
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

    def container_click(self, e: ClickEventArguments):
        # print("Container clicked")
        if time.time() - self.last_card_click_timestamp > 0.2:  # Increased timeout to prevent quick deselect
            self.deselect_all_cards()
            self.last_card_clicked = None
            
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
        self.name = field_data["name"]
        self.display_order = field_data["display_order"]  # Ensure position updates dynamically

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

    def update_position(self, new_position):
        """Update the card's current position dynamically."""
        self.display_order = new_position
        
@ui.page("/")
def main_page():
    global cards, card_list, event_handler
    event_handler = EventHandler()
    with ui.header(elevated=True).style('background-color: #3874c8; padding: 10px 10px;').classes('items-center justify-between'):
        # Left-aligned title
        ui.label("Custom Field Management").style('font-size: 1.5em; font-weight: bold; color: white;')


        access_token = ui.input(
            placeholder="Enter Access Token..."
        ).style(
            'width: 600px; font-size: 1.5em; border-radius: 5px; '
            'border: 2px solid white; background-color: white; color: #333; '
            'box-sizing: border-box; text-indent: 5px;'
        )

    """Main NiceGUI Page with Clickable and Filterable Custom Field Cards."""
    with ui.row().style('width: 100%; height: calc(100vh - 120px); display: flex;') as page_container:
        page_container.on('click', event_handler.container_click)
        # Left Content (Inside a Scroll Area)
        with ui.scroll_area().style('flex: 1; height: 100%; padding: 0; margin: 0;'):
            with ui.column().style('width: 100%; padding: 20px;'):
                ui.label('Left Side Content')
                ui.button('Click Me', on_click=lambda: ui.notify('Left button clicked'))
                # Add button to trigger the move function
                ui.button("Move Selected Cards", on_click=move_selected_cards).style(
                    "margin-top: 10px; font-size: 1.2em; padding: 10px;"
                )


        # Divider
        with ui.separator().style('height: 100%; width: 2px; flex-shrink: 0;'):
            pass

        # Right Section - Custom Fields
        with ui.column().style('flex: 1; height: 100%; padding: 10; margin: 0; display: flex; flex-direction: column; background-color: WhiteSmoke;'):
            
            # Fixed Filter Input (Above the Scroll Area)
            with ui.column().style('width: 100%; background-color: white; padding: 10px; position: sticky; top: 0; z-index: 10; box-shadow: 0px 2px 5px rgba(0, 0, 0, 0.1);'):
                # Function to filter cards dynamically
                def update_cards():
                    search_text = filter_input.value
                    logging.debug(f"Filtering with: {search_text}")
                    for card in cards:
                        card.update_visibility(search_text)  # Update visibility
                    
                # Input field for filtering
                with ui.row():
                    filter_input = ui.input(placeholder="Filter fields by name...", on_change=update_cards).style(
                'width: 600px; font-size: 1.5em; border-radius: 5px; '
                'border: 2px;'
            )

            # Scroll Area for Cards (Below the Fixed Filter)
            card_list = ui.scroll_area().style('flex: 1; width: 100%; padding: 0; margin: 0;')
            with card_list:
                with ui.column().classes('w-full').style('gap: 7px;'):
                    # List to store card instances
                    cards = []

                    for field in custom_fields:
                        card_instance = CustomFieldCard(field, event_handler)  # Create a card for each field
                        cards.append(card_instance)  # Store the instance in the list
                    event_handler.set_custom_field_cards(cards)
                    
                    
ui.run()