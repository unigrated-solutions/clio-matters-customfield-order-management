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
    return Client(access_token=api_key, store_responses=False, async_requests=False)

# Patch request to API to update display_order
# Query/Path/Request Body arguments are already split automatically so there's no need to separate them 
# Converted the datatype on purpose to test the API clients validate_and_convert function
# https://github.com/unigrated-solutions/clio-api-python-client/blob/main/classes/base.py
# TODO: Update API client to convert Literal capitalization mismatches so that Matter/matter or Contact/contact get converted automatically
# https://github.com/unigrated-solutions/clio-api-python-client/commit/6e80fd0906d55548fb7d79b1352e268327234170
def update_custom_field_display_order(client:Client, field_id, new_position):
    field_id=str(field_id)
    new_position=str(new_position)
    try:
        response = {"Success": True}
        response = client.patch.custom_fields(id=field_id, display_order=new_position, fields='all')
        
        logging.info(json.dumps(response, indent=2))
        return response
    
    except Exception as e:
        logging.debug(f"An error occurred: {e}")
          
def get_custom_fields(client:Client=None, parent_type="matter"):
    # ui.notify(client)
    try:
        response = {"Success": True}
        response = client.all.custom_fields(fields="id,name,display_order,deleted, parent_type", parent_type=parent_type)
        logging.debug(json.dumps(response, indent=2))
        return response
    
    except Exception as e:
        logging.debug(f"An error occurred: {e}")


def get_custom_field_sets(client:Client=None, parent_type="Matter"):
    parent_type=parent_type.title()
    try:
        response = {"Success": True}
        response = client.all.custom_field_sets(fields="id,name,parent_type,custom_fields{id}", parent_type=parent_type)
        logging.debug(json.dumps(response, indent=2))
        return response
    
    except Exception as e:
        logging.debug(f"An error occurred: {e}")

def update_custom_field_set_label(client, fieldset_id, new_name):
    try:
        response = client.patch.custom_field_sets(id=fieldset_id, fields="name", name=new_name)
        print(response)
        logging.debug(json.dumps(response, indent=2))
        return {"Success": True}
    
    except Exception as e:
        logging.debug(f"An error occurred: {e}")