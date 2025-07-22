#!/usr/bin/env python3
import sys
import json
import time
from pathlib import Path
import logging

# Add client/ directory to sys.path
client_path = Path(__file__).parent / 'client'
sys.path.insert(0, str(client_path))

import httpx
from nicegui import ui, app, run
from fastapi import Request

from client.src.clio_manage_python_client.client import Client

logging.basicConfig(level=logging.DEBUG)

AUTH_BASE_URL = "https://app.clio.com/oauth/authorize"
TOKEN_URL = "https://app.clio.com/oauth/token"
DEAUTHORIZE_URL = "https://app.clio.com/oauth/deauthorize"

HOST = "127.0.0.1"
PORT = 8080

REDIRECT_URI = "http://127.0.0.1:8080/callback"

ACCESS_TOKEN_KEY = "123"

@app.get("/callback")
async def callback(request: Request):
    """Handle OAuth callback, validate state, and request access token."""
    query_params = request.query_params
    code = query_params.get("code")
    state = query_params.get("state")

    if not code or not state:
        return ui.notify("Invalid request: Missing code or state.", type="warning")

    state_key = f"oauth_state_{state}"
    state_data = app.storage.general.get(state_key)

    if not state_data:
        return ui.notify("Invalid or expired state.", type="warning")

    timestamp = state_data.get("timestamp", 0)
    
    # State token set to expire after 60 seconds
    # Removes state token before completing callback 
    if time.time() - timestamp > 60:
        del app.storage.general[state_key]
        return ui.notify("State expired. Please try again.", type="warning")

    client_id = state_data.get("client_id")
    client_secret = state_data.get("client_secret")

    if not client_id or not client_secret:
        del app.storage.general[state_key]
        return ui.notify("Stored client credentials missing. Please restart authentication.", type="warning")

    del app.storage.general[state_key]  # Remove state after use

    payload = {
        "client_id": client_id,
        "client_secret": client_secret,
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": REDIRECT_URI
    }
    headers = {"Content-Type": "application/x-www-form-urlencoded"}

    async with httpx.AsyncClient() as client:
        response = await client.post(TOKEN_URL, data=payload, headers=headers)

    if response.status_code == 200:
        token_data = response.json()
        access_token = token_data.get("access_token")

        # Store access token in app storage
        access_token_list = app.storage.general.get(ACCESS_TOKEN_KEY, [])
        new_token_entry = {
            "id": len(access_token_list) + 1,
            "access_token": access_token
        }
        access_token_list.append(new_token_entry)
        app.storage.general[ACCESS_TOKEN_KEY] = access_token_list
        return "Success"

    else:
        return "Error"
    
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
    print(client)
    print(field_id)
    print(new_position)
    try:
        response = client.patch.custom_fields(id=field_id, display_order=new_position, fields='all')
        
        logging.info(json.dumps(response, indent=2))
        return response
    
    except Exception as e:
        print(e)
        logging.debug(f"An error occurred: {e}")

def get_custom_field(client:Client=None, **kwargs):
    assert kwargs.get('id')
    
    kwargs.setdefault('fields', 'all')
    try:
        response = {"Success": True}
        response = client.get.custom_fields(**kwargs)
        logging.debug(json.dumps(response, indent=2))
        return response
    
    except Exception as e:
        logging.debug(f"An error occurred: {e}")
           
def get_custom_fields(client:Client=None, parent_type="matter"):
    try:
        response = {"Success": True}
        response = client.all.custom_fields(fields="id,name,parent_type,field_type,displayed,deleted,required,display_order,picklist_options{id,option}", parent_type=parent_type)
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

def update_custom_field(client, field_id, **kwargs):
    print(kwargs)
    try:
        response = client.patch.custom_fields(id=field_id, fields="all", **kwargs)
        print(response)
        logging.debug(json.dumps(response, indent=2))
        return True
    
    except Exception as e:
        logging.debug(f"An error occurred: {e}")
        return False
        
def update_custom_field_set_label(client, fieldset_id, new_name):
    try:
        response = client.patch.custom_field_sets(id=fieldset_id, fields="name", name=new_name)
        print(response)
        logging.debug(json.dumps(response, indent=2))
        ui.notify(f"Successfully to field set label to: {new_name}")
        return {"Success": True}
    
    except Exception as e:
        logging.debug(f"An error occurred: {e}")
        
def delete_custom_field(client, field_id):
    try:
        response = client.delete.custom_fields(id=field_id)
        print(response)
        logging.debug(json.dumps(response, indent=2))
        ui.notify(f"Successfully deleted: {field_id}")
        return {"Success": True}
    
    except Exception as e:
        logging.debug(f"An error occurred: {e}")
        
def create_custom_field(client, **kwargs):
    print(kwargs)
    kwargs.setdefault('fields', 'all')
    kwargs.setdefault('parent_type', 'matter')
    try:
        response = client.post.custom_fields(**kwargs)
        print(response)
        logging.debug(json.dumps(response, indent=2))
        return True
    
    except Exception as e:
        logging.debug(f"An error occurred: {e}")
        return False
    
def create_custom_field_set(client, **kwargs):
    kwargs.setdefault('fields', 'all')
    kwargs.setdefault('parent_type', 'matter')
    try:
        response = client.post.custom_field_sets(**kwargs)
        print(response)
        logging.debug(json.dumps(response, indent=2))
        return True
    
    except Exception as e:
        logging.debug(f"An error occurred: {e}")
        return False