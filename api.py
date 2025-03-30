#!/usr/bin/env python3
import sys
import json
from pathlib import Path
import logging

# Add client/ directory to sys.path
client_path = Path(__file__).parent / 'client'
sys.path.insert(0, str(client_path))

from nicegui import ui, app, run

from client import Client

logging.basicConfig(level=logging.DEBUG)

def create_client_session(api_key=""):
    app.storage.tab['api_client_loaded'] = True
    return Client(access_token=api_key, store_responses=False, async_requests=False)

def update_access_token(client:Client, api_key):
    ui.notify(f'Setting Access Token: {api_key}')
    client.set_bearer_token(api_key)
    
def get_custom_fields(client:Client=None, parent_type="matter"):
    try:
        response = {"Success": True}
        response = client.all.custom_fields(fields="id,name,display_order,deleted", parent_type=parent_type)
        logging.debug(json.dumps(response, indent=2))
        return response
    
    except Exception as e:
        logging.debug(f"An error occurred: {e}")


def get_custom_field_sets(client:Client=None):
    try:
        response = {"Success": True}
        response = client.all.custom_field_sets(fields="id,name,custom_fields{id}")
        logging.debug(json.dumps(response, indent=2))
        return response
    
    except Exception as e:
        logging.debug(f"An error occurred: {e}")

#Replace with API patch call    
def log_display_order_change(item_id, new_order):
    ui.notify(f"Moving item '{item_id}' to new display_order: {new_order}")
    return True  # Simulate a successful result

def move_item(moving_id, target_id, position, on_display_order_change):
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

def bulk_move_items(moving_ids, target_id, position):
    cards = app.storage.tab['fields']

    # Map of id to card for lookup
    id_to_order = {card.id: card.display_order for card in cards}
    moving_ids = sorted(moving_ids, key=lambda x: id_to_order.get(x, float('inf')))

    first_move_complete = False
    for id in moving_ids:
        if not first_move_complete:
            success = move_item(id, target_id, position, log_display_order_change)
            if success:
                first_move_complete = True
                position = 'after'
                target_id = id
        else:
            success = move_item(id, target_id, position, log_display_order_change)
            if success:
                target_id = id
                
def move_selected_cards(target_id, position):
    cards = app.storage.tab['fields']

    selected_cards = [card for card in cards if card.selected]
    if not selected_cards:
        ui.notify("No cards selected!", color="red")
        return

    moving_ids = [card.id for card in selected_cards]
    if not moving_ids:
        return
    
    bulk_move_items(moving_ids, target_id, position)
    app.storage.tab['field_handler'].generate_custom_field_cards()