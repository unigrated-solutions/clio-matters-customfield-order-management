#!/usr/bin/env python3
import time
import logging

from nicegui import ui, app
from nicegui.events import KeyEventArguments, ClickEventArguments

from elements import *
from api import *

logging.basicConfig(level=logging.DEBUG)
USING_TEST_FIELDS = False

if USING_TEST_FIELDS:
    # Sample custom fields data
    app.storage.general['custom_fields'] = [
        {'id':000 , 'deleted': False, "name": "Field 0", "display_order": 0},
        {'id':111 , 'deleted': False, "name": "Field 1", "display_order": 1},
        {'id':222 , 'deleted': False, "name": "Field 2", "display_order": 2},
        {'id':333 , 'deleted': False, "name": "Field 3", "display_order": 3},
        {'id':444 , 'deleted': False, "name": "Field 4", "display_order": 4},
        {'id':555 , 'deleted': False, "name": "Field 5", "display_order": 5},
        {'id':666 , 'deleted': False, "name": "Field 6", "display_order": 6},
        {'id':777 , 'deleted': False, "name": "Field 7", "display_order": 7},
        {'id':888 , 'deleted': False, "name": "Field 8", "display_order": 8},    
        {'id':999 , 'deleted': True, "name": "Field 9", "display_order": 9},
        {'id':110 , 'deleted': False, "name": "Field 10", "display_order": 10},
        {'id':110 , 'deleted': True, "name": "Field 11", "display_order": 11},
        {'id':120 , 'deleted': False, "name": "Field 12", "display_order": 12},    
    ]
    app.storage.general['custom_field_sets'] = [
        {"id": 999, "name": "Field Set 1", "custom_fields": [{"id": 111},{"id": 222},{"id": 333},{"id": 444}]},
        {"id": 888, "name": "Field Set 2", "custom_fields": [{"id": 444},{"id": 555},{"id": 888},{"id": 222},{"id": 999}]}
        ]

else:
    if not app.storage.general.get('custom_fields'):
        app.storage.general['custom_fields'] = []
        
    if not app.storage.general.get('custom_field_sets'):
        app.storage.general['custom_field_sets'] = []
        
async def copy(selected_token):
    ui.run_javascript(f'navigator.clipboard.writeText("{selected_token}")')

@ui.page("/")
async def main_page():
    await ui.context.client.connected()
    app.storage.tab['api_client_loaded'] = False
    app.storage.tab['api_client'] = create_client_session()
    app.storage.tab['fields'] = []
    app.storage.tab['field_set_cards'] = []
    event_handler = EventHandler()
    field_handler = CustomFieldsHandler(event_handler)
    field_set_handler = CustomFieldSetsHandler()

    app.storage.tab['field_handler'] = field_handler
    app.storage.tab['field_set_handler'] = field_set_handler
    ui.add_body_html('''
    <script>
        document.addEventListener('DOMContentLoaded', () => {
            document.body.style.userSelect = 'none';
        });
    </script>
    ''')
    
    def store_access_token(token):
        app.storage.general['access_token'] = token
        ui.notify("Access Token Saved")
        
    with ui.header(elevated=True).style('background-color: #3874c8; padding: 10px 10px;').classes('items-center justify-between'):

        ui.label("Custom Field Management").style('font-size: 1.5em; font-weight: bold; color: white;')

        # ui.button('Delete Fields', on_click= lambda: app.storage.general['custom_fields'].pop())
        # ui.button('Update Fields', on_click=generate_custom_field_cards.refresh)
        # ui.button('Key Test', on_click= lambda: ui.notify(app.storage.tab['api_key']))
        # client_loaded = ui.label().bind_text_from(app.storage.tab, 'api_client_loaded')
        # ui.button('CLient Test', on_click= lambda: update_custom_fields(app.storage.tab['api_client']))
        
        with ui.row():
            save_button = ui.button(icon='save').style('height: 50px;')
            access_token = ui.input(
                placeholder="Enter Access Token...",
                password=True,
                password_toggle_button=True
            ).style(
                'width: 500px; height: 50px; font-size: 1.25em; border-radius: 5px; '
                'background-color: white; color: #333; padding-left: 12px; '
            )
            copy_button = ui.button(icon="content_copy").style('height: 50px;')
            copy_button.on('click', lambda: copy(access_token.value))
            save_button.on('click', lambda: store_access_token(access_token.value) )
            
            if app.storage.general.get('access_token'):
                access_token.set_value(app.storage.general['access_token'])
                update_access_token(app.storage.tab['api_client'], app.storage.general['access_token'])
            access_token.bind_value_to(app.storage.tab, 'api_key')
            access_token.on('change', lambda: update_access_token(app.storage.tab['api_client'], access_token.value))
            
        matter_contact_button = ui.button('Switch to Contact custom fields', on_click=field_handler.update_fields.refresh)
        matter_contact_button.disable()
    
    with ui.row().style('width: 100%; height: calc(100vh - 120px); display: flex;') as page_container:
        page_container.on('dblclick', event_handler.deselect_all_cards)
        
        # Scroll Area for Custom Field Sets
        with ui.scroll_area().style('flex: 1; height: 100%; padding: 0; margin: 0;'):
            field_set_handler.load()
            
        with ui.separator().style('height: 100%; width: 2px; flex-shrink: 0;'):
            pass

        # Right Section - Custom Fields
        with ui.column().style('flex: 1; height: 100%; padding: 10; margin: 0; display: flex; flex-direction: column; background-color: WhiteSmoke;'):
            
            # Search box always visible
            with ui.column().style('width: 100%; background-color: white; padding: 10px; position: sticky; top: 0; z-index: 10; box-shadow: 0px 2px 5px rgba(0, 0, 0, 0.1);'):
                
                def filter_fields():
                    search_text = custom_field_filter.value
                    logging.debug(f"Filtering with: {search_text}")
                    for card in app.storage.tab['cards']:
                        card.update_visibility(search_text)  # Update visibility
                    
                # Input field for filtering
                with ui.row().classes('w-full items-center justify-between'):
                    custom_field_filter = ui.input(placeholder="Filter fields by name...", on_change=filter_fields).style(
                        'width: 300px; font-size: 1.5em; border-radius: 5px; '
                        'border: 2px;'
                    )
                    toggle_deleted_field = ui.switch("Show Deleted", value=True).bind_value_to(app.storage.tab,'display_deleted')
                    toggle_deleted_field.on('click', lambda e: event_handler.toggle_deleted_field_visibility(e.sender.value))
                    ui.button(icon='refresh', on_click= lambda: field_handler.load_from_api(parent_type="matter", client=app.storage.tab['api_client']))

            # Scroll area for cards
            with ui.scroll_area().style('flex: 1; width: 100%; padding: 0; margin: 0;'):
                field_handler.load()

ui.run(storage_secret="CHANGEME", native=True, title="Matters" , window_size=(1440,810), uvicorn_logging_level="debug")