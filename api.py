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
    
def get_custom_fields(client:Client=None):
    try:
        response = {"Success": True}
        response = client.all.custom_fields(fields="id,name,display_order,deleted")
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
             
async def update_custom_fields(client:Client=None):
    ui.notify('Attempting to send request')
    response = await run.io_bound(get_custom_fields, client)
    app.storage.general['custom_fields'] = response.get('data', [])
    app.storage.tab['card_list'].refresh()
    
    if response:
        ui.notify(response)
    else:
        ui.notify("Failed to Download Fields")