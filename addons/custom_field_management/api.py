#!/usr/bin/env python3
import json
import logging

from nicegui import ui, app

from clio_manage_python_client import ClioManage as Client

logging.basicConfig(level=logging.DEBUG)
    
def update_custom_field_display_order(field_id, new_position):
    client = app.storage.tab['custom_field_management_api']
    field_id=str(field_id)
    new_position=str(new_position)

    try:
        response = client.patch.custom_fields(id=field_id, display_order=new_position, fields="id,etag,name,parent_type,field_type,displayed,deleted,required,display_order,picklist_options{id,etag,option,deleted_at}")
        data = response.get("data")
        if not data:
            logging.debug(f"❌ Failed to get data for field {field_id}")
            return False
        
        """Update general storage after API reorder, excluding 'id' from value."""
        storage = app.storage.general["customfield_management_storage"]["custom_field_data"]
        
        field_id = str(data.get("id"))
        if field_id and isinstance(storage.get(field_id), dict):
            filtered_data = {k: v for k, v in data.items() if k != "id"}
            app.storage.general["customfield_management_storage"]["custom_field_data"][field_id]=filtered_data
            
        logging.debug(json.dumps(response, indent=2))
        return True
    
    except Exception as e:
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
           
def get_custom_fields(client: Client = None, parent_type=None, **kwargs):
    try:
        params = {
            "fields": "id,etag,name,parent_type,field_type,displayed,deleted,required,display_order,picklist_options{id,etag,option,deleted_at}",
            "order": "display_order(asc)",
        }

        if parent_type is not None:
            params["parent_type"] = parent_type

        params.update(kwargs)

        response = client.all.custom_fields(**params)
        return response

    except Exception as e:
        logging.debug(f"An error occurred: {e}")

def get_custom_field_sets(client:Client=None, parent_type=None, **kwargs):
    params = {
        "fields": "id,etag,name,parent_type,displayed,custom_fields{id,etag}",
    }
    
    if parent_type is not None:
        params["parent_type"] = parent_type
        
    params.update(kwargs)
    
    try:
        response = client.all.custom_field_sets(**params)
        return response
    
    except Exception as e:
        logging.debug(f"An error occurred: {e}")

def update_custom_field(client,**kwargs):
    try:
        response = client.patch.custom_fields(fields="all,picklist_options{all}", **kwargs)

        logging.debug(json.dumps(response, indent=2))
        return response
    
    except Exception as e:
        logging.debug(f"An error occurred: {e}")
        return False
        
def update_custom_field_set_label(client, fieldset_id, new_name):
    try:
        response = client.patch.custom_field_sets(id=fieldset_id, fields="name", name=new_name)
        logging.debug(json.dumps(response, indent=2))
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
    storage = app.storage.general.get("customfield_management_storage", {})
    custom_field_data = storage.get("custom_field_data", {})

    # Clean kwargs of None, empty list, empty dict, and empty string
    cleaned_kwargs = {
        k: v for k, v in kwargs.items()
        if v not in (None, "", [], {})
    }

    # Handle display_order auto-assignment
    if not cleaned_kwargs.get("display_order"):  
        parent_type = cleaned_kwargs.get("parent_type").title()
        if parent_type:
            # Get all display_order values for the same parent_type
            matching_orders = [
                field.get("display_order", 0)
                for field in custom_field_data.values()
                if field.get("parent_type") == parent_type and isinstance(field.get("display_order"), int)
            ]
            cleaned_kwargs["display_order"] = (max(matching_orders) + 1) if matching_orders else 1

    try:
        response = client.post.custom_fields(**cleaned_kwargs)
        logging.debug(json.dumps(response, indent=2))
        return response
    
    except Exception as e:
        logging.debug(f"An error occurred: {e}")
        return False
     
def create_custom_field_set(client, **kwargs):
    kwargs.setdefault('fields', 'all')
    kwargs.setdefault('parent_type', 'matter')
    try:
        response = client.post.custom_field_sets(**kwargs)
        logging.debug(json.dumps(response, indent=2))
        return True
    
    except Exception as e:
        logging.debug(f"An error occurred: {e}")
        return False
    
def load_matter_field_values(**kwargs):
    try:
        client = app.storage.tab['custom_field_management_api']
        # response = client.get.matters(fields='id,display_number,description,custom_field_values{id,field_name,field_display_order,value,soft_deleted},user{all}', **kwargs)
        # app.storage.general['matters'] = response.get('data')
        response = client.get.matters(fields='id,display_number,description,custom_field_values{id,field_name,field_display_order,value,soft_deleted}', custom_field_ids = [5677876])
        app.storage.general['matter_query'] = response.get('data')
        logging.debug(json.dumps(response, indent=2))
        return response
    
    except Exception as e:
        logging.debug(f"An error occurred: {e}")
        return False