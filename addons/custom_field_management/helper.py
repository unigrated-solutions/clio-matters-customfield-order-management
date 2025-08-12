
from nicegui import ui, app
import logging

def get_deleted_custom_field_ids(parent_type) -> list[str]:
    """Return a list of custom field IDs where 'deleted' is True."""
    storage = app.storage.general.get('customfield_management_storage', {})
    custom_field_data = storage.get('custom_field_data', {})

    deleted_fields = [
        field_id
        for field_id, data in custom_field_data.items()
        if isinstance(data, dict) and data.get('deleted') is True and data.get("parent_type") == parent_type.title()
    ]
    ui.notify(deleted_fields)
    return deleted_fields


def get_matters_containing_field(field_id) -> list[str]:
    ui.notify(f"Get containing matters: {field_id}")
    client = app.storage.tab['custom_field_management_api']
    ui.notify(client)
    try:
        params = {
            "fields": "id,display_number,description",
            "custom_field_ids__": [field_id]
        }

        response = client.all.matters(**params)
        logging.debug(response)
        ui.notification(response, multi_line= True, timeout=0, close_button=True)
        return response

    except Exception as e:
        logging.debug(f"An error occurred: {e}")
        