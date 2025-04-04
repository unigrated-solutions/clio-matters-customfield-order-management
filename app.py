#!/usr/bin/env python3
import time
import logging
import secrets
from urllib.parse import urlencode

from nicegui import ui, app

from elements import *
from api import *

logging.basicConfig(level=logging.DEBUG)
    
async def copy(selected_token):
    ui.run_javascript(f'navigator.clipboard.writeText("{selected_token}")')
    ui.notify('Copied to clipboard')

# async def create_access_token():
    
    # def link_dialog(target):
    #     with ui.dialog() as dialog,ui.card().style('width: 1440px; max-width: none; height: 810px;'):
    #         with ui.element('q-toolbar'):
    #             with ui.element('q-toolbar-title'):
    #                 ui.label('pop window')
    #             ui.button(icon='close',on_click=dialog.close).props('flat round dense')
    #         with ui.element('q-card-section').classes('w-full h-full'):
    #             with ui.element('iframe').classes('w-full h-full'):
    #                 ui.navigate.to(target)
    #     return dialog

#     """Fetch client ID, store credentials with state, and open the OAuth URL in a new tab."""

#     # client_id = selected_row.get("client_id")
#     # client_secret = selected_row.get("client_secret")
    
#     client_id = "123"
#     client_secret = "123"

#     if not client_id or not client_secret:
#         ui.notify("Client ID or Client Secret is missing!", type="warning")
#         return

#     # Generate a random state token
#     state = secrets.token_urlsafe(16)
#     timestamp = time.time()

#     # Store state, timestamp, client ID, and client secret in storage
#     app.storage.general[f"oauth_state_{state}"] = {
#         "timestamp": timestamp,
#         "client_id": client_id,
#         "client_secret": client_secret,
#     }

#     # Construct the OAuth URL
#     params = {
#         "response_type": "code",
#         "client_id": client_id,
#         "redirect_uri": REDIRECT_URI,
#         "state": state
#     }
#     auth_url = f"{AUTH_BASE_URL}?{urlencode(params)}"
#     print(auth_url)
#     link_dialog(auth_url).open()

@ui.page("/")
async def new_tab():
    ui.navigate.to(customfield_management_page)
    
@ui.page("/customfield_management")
async def customfield_management_page():
    
    if not app.storage.general.get('custom_fields'):
        app.storage.general['custom_fields'] = {"matter": [], "contact": []}
        
    if not app.storage.general.get('custom_field_sets'):
        app.storage.general['custom_field_sets'] = {"matter": [], "contact": []}
    
    ui.query('.nicegui-content').classes('p-0 m-0 gap-0')
    await ui.context.client.connected()
    
    app.storage.tab['fields'] = []
    app.storage.tab['field_set_cards'] = []
    parent_type = app.storage.general.get('parent_type', "matter")
    
    event_handler = EventHandler(parent_type)
    field_handler, field_set_handler = event_handler.init_handlers()

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
    
    # async def update_matter_contact_button_text():
    #     if event_handler.parent_type == "matter":
    #         matter_contact_button.set_text("Switch to Matter custom fields")

    #     if event_handler.parent_type == "contact":
    #         matter_contact_button.set_text("Switch to Contact custom fields")
    
    with ui.header(elevated=True).style('background-color: #3874c8; padding: 5px 2px;').classes('items-center justify-between'):
        with ui.row():
            with ui.row().classes('w-full items-center').style('gap: 5px;') as menu_bar:
                #App Menu
                with ui.button(text="File").classes('text-white').props('flat').style('height: 30px; width: 60px; '):
                    with ui.menu() as menu:
                        # ui.menu_item('Create Access Token', create_access_token)
                        ui.menu_item('Create Access Token').set_enabled(False)
                        ui.separator()
                        ui.menu_item('Close', app.shutdown)
                
                #Tools
                with ui.button(text="Tools").classes('text-white').props('flat').style('height: 30px; width: 60px;'):
                    with ui.menu() as menu:
                        # ui.menu_item('Create Access Token', create_access_token)
                        ui.menu_item('Custom Field Management', on_click= lambda: ui.navigate.to(customfield_management_page))
        with ui.row():
            access_token = ui.input(
                placeholder="Enter Access Token...",
                password=True,
                password_toggle_button=True
            ).props('v-model="text" dense="dense" size=48').style(
                'width: 250px; border-radius: 5px; '
                'background-color: white; color: #333; padding-left: 12px;'
            )
            
            if app.storage.general.get('access_token'):
                access_token.set_value(app.storage.general['access_token'])
                event_handler.update_access_token(app.storage.general['access_token'])
            
            access_token.bind_value_to(app.storage.tab, 'api_key')
            access_token.on('change', lambda: event_handler.update_access_token(access_token.value))
            
            
            copy_button = ui.button(icon="content_copy").style('height: 35px; width: 35px;')
            copy_button.on('click', lambda: copy(access_token.value))
            save_button = ui.button(icon='save').style('height: 35px; width: 35px;')
            save_button.on('click', lambda: store_access_token(access_token.value) )


    ExpandableRightDrawer(event_handler=event_handler)
    with ui.row().style('width: 100%; height: calc(100vh - 50px); margin: 0; padding: 5px 2px; display: flex;') as page_container:
        page_container.on('dblclick', event_handler.deselect_all_fields)
        

        with ui.column().style('flex: 1; gap: 0; height: 100%; padding: 10; margin: 0; display: flex; flex-direction: column; background-color: WhiteSmoke'):
            ui.label('Field Sets').classes('w-full text-2xl bg-white font-bold border border-gray-300 p-2 rounded text-center')
            # Scroll Area for Custom Field Sets
            with ui.scroll_area().style('flex: 1; width: 100%; padding: 0; margin: 0;'):
                field_set_handler.load()
                
        ui.separator().style('height: 100%; width: 2px; flex-shrink: 0;')


        # Right Section - Custom Fields
        with ui.column().style('flex: 1; gap: 0; height: 100%; padding: 0; margin: 0; display: flex; flex-direction: column; background-color: WhiteSmoke;'):
            ui.label('Fields').classes('w-full text-2xl bg-white font-bold border border-gray-300 p-2 rounded text-center')
            
            # Scroll area for cards
            with ui.scroll_area().style('flex: 1; width: 100%; padding: 0; margin: 0;'):
                field_handler.load()
                
            # Search box always visible
            with ui.column().style('width: 100%; background-color: white; padding: 10px; position: sticky; top: 0; z-index: 10; box-shadow: 0px 2px 5px rgba(0, 0, 0, 0.1);'):
                
                def filter_fields():
                    search_text = custom_field_filter.value
                    logging.debug(f"Filtering with: {search_text}")
                    for card in app.storage.tab['fields']:
                        card.update_visibility(search_text)  # Update visibility
                    
                # Input field for filtering
                with ui.row().classes('w-full items-center justify-between').style('padding: 5px, 2px;'):
                    custom_field_filter = ui.input(placeholder="Filter fields by name...", on_change=filter_fields).style(
                        'width: 300px;  border-radius: 5px; '
                        'border: 2px; padding: 0;'
                    ).props('v-model="text" dense="dense" size=32')
                    
                    if not app.storage.tab.get('display_deleted'):
                        app.storage.tab['display_deleted'] = False
                        
                    toggle_deleted_field = ui.switch("Show Deleted").bind_value_from(app.storage.tab,'display_deleted').props('dense')
                    toggle_deleted_field.on('click', lambda e: event_handler.toggle_display_deleted())
                    ui.button(icon='refresh', on_click= lambda: field_handler.load_from_api())

ui.run(storage_secret="CHANGEME", title= 'Custom Field Management', native=True , window_size=(1440,810), uvicorn_logging_level="debug")