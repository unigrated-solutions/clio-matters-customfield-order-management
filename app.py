#!/usr/bin/env python3
import time
import logging
import secrets
from urllib.parse import urlencode

from nicegui import ui, app

from elements import *
from api import *

logging.basicConfig(level=logging.DEBUG)

def check_storage():
    
    if not app.storage.general.get('matter_custom_fields'):
        app.storage.general['matter_custom_fields'] = []
    if not app.storage.general.get('matter_custom_field_sets'):
        app.storage.general['matter_custom_field_sets'] = []
        
    if not app.storage.general.get('contact_custom_fields'):
        app.storage.general['contact_custom_fields'] = []
    if not app.storage.general.get('contact_custom_field_sets'):
        app.storage.general['contact_custom_field_sets'] = []
        
@ui.page("/")
async def new_tab():
    ui.navigate.to(customfield_management_page)
    
@ui.page("/customfield_management")
async def customfield_management_page():
    
    async def copy_token(selected_token):
        ui.run_javascript(f'navigator.clipboard.writeText("{selected_token}")')
        ui.notify('Copied to clipboard')
    
    check_storage()
    
    ui.query('.nicegui-content').classes('p-0 m-0 gap-0')
    await ui.context.client.connected()
    
    app.storage.client['fields'] = []
    app.storage.client['field_set_cards'] = []
    parent_type = app.storage.general.get('parent_type', "matter")
    
    event_handler = EventHandler(parent_type)
    visibility_handler = AppElementVisibility()
    app.storage.client['visibility_handler'] = visibility_handler

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
                with ui.button(text="View").classes('text-white').props('flat').style('height: 30px; width: 60px;'):
                    with ui.menu() as menu:
                        # ui.menu_item('Create Access Token', create_access_token)
                        with ui.menu_item('Custom Fields', auto_close=False):
                            with ui.item_section().props('side'):
                                ui.icon('keyboard_arrow_right')
                            with ui.menu().props('anchor="top end" self="top start" auto-close'):
                                ui.menu_item('Matters', on_click= lambda: event_handler.set_parent_type('matter'))
                                ui.menu_item('Contacts', on_click= lambda: event_handler.set_parent_type('contact'))


        with ui.row():
            access_token = ui.input(
                placeholder="Enter Access Token...",
                password=True,
                password_toggle_button=True
            ).props('v-model="text" dense="dense" size=48').style(
                'width: 250px; border-radius: 5px; '
                'background-color: white; color: #333; padding-left: 12px;'
            ).bind_value(app.storage.general, 'access_token')
            
            event_handler.update_access_token(access_token.value)
            
            access_token.bind_value_to(app.storage.client, 'api_key')
            access_token.on('change', lambda: event_handler.update_access_token(access_token.value))
            
            
            copy_button = ui.button(icon="content_copy").style('height: 35px; width: 35px;')
            copy_button.on('click', lambda: copy_token(access_token.value))
            save_button = ui.button(icon='save').style('height: 35px; width: 35px;')
            save_button.on('click', lambda: store_access_token(access_token.value) )

    # right_drawer = ExpandableRightDrawer(event_handler=event_handler)
    # await right_drawer.refresh()
    
    with ui.row().style('width: 100%; height: calc(100vh - 50px); margin: 0; padding: 5px 2px; display: flex;') as page_container:
        field_handler, field_set_handler = event_handler.init_handlers(page_container)
        page_container.on('dblclick', event_handler.deselect_all_fields)
        
        # Left Section - Custom Field Sets
        with ui.column().style('flex: 1; gap: 0; height: 100%; padding: 10; margin: 0; display: flex; flex-direction: column; background-color: WhiteSmoke'):
            ui.label('Custom Field Sets').classes('w-full text-2xl bg-white font-bold border border-gray-300 p-2 rounded text-center')
            
            # Scroll Area for Custom Field Sets
            with ui.scroll_area().style('flex: 1; width: 100%; padding: 0; margin: 0; '
                                        'border-radius: 5px; border: 2px solid #ccc; padding: 0;'):
                field_set_handler.load()
                
            with ui.row().classes('w-full items-center').style('justify-content: space-between; padding: 5px 2px; flex-wrap: wrap; gap: 8px; background-color: white;'):
                ui.input(placeholder="Filter by name...").style(
                    'flex: 1 1 200px; min-width: 150px; max-width: 300px; '
                    'border-radius: 5px; border: 2px solid #ccc; padding: 0;'
                    ).props('dense size=32').disable()
                with ui.row():
                    ui.button(icon='add', on_click=field_set_handler.show_field_set_creation_dialog)
                    ui.button(icon='refresh', on_click=lambda: field_set_handler.load_from_api()).disable()

        ui.separator().style('height: 100%; width: 2px; flex-shrink: 0;')


        # Right Section - Custom Fields
        with ui.column().style(
            'flex: 1; gap: 0; height: 100%; padding: 0; margin: 0; display: flex; flex-direction: column; background-color: WhiteSmoke; '
            ):
            ui.label('CustomFields').classes('w-full text-2xl bg-white font-bold border border-gray-300 p-2 rounded text-center')
            
            # Scroll area for cards
            with ui.scroll_area().style('flex: 1; width: 100%; padding: 0; margin: 0; '
                                        'border-radius: 5px; border: 2px solid #ccc; padding: 0;'):
                field_handler.load()
                
            # Filter row with proper wrapping
            with ui.row().classes('w-full items-center').style('justify-content: space-between; padding: 5px 2px; flex-wrap: wrap; gap: 8px; background-color: white;'):

                def filter_fields():
                    search_text = custom_field_filter.value
                    logging.debug(f"Filtering with: {search_text}")
                    for card in app.storage.client['fields']:
                        card.update_visibility(search_text)
                        
                custom_field_filter = ui.input(
                    placeholder="Filter fields by name...",
                    on_change=filter_fields
                ).style(
                    'flex: 1 1 200px; min-width: 150px; max-width: 300px; '
                    'border-radius: 5px; border: 2px solid #ccc; padding: 0;'
                ).props('dense size=32')
                
                event_handler.set_field_filter_element(custom_field_filter)
                
                if not app.storage.client.get('display_deleted'):
                    app.storage.client['display_deleted'] = False
                with ui.row():
                    toggle_deleted_field = ui.switch("Show Deleted").bind_value_to(visibility_handler, 'display_deleted').props('dense')
                    toggle_details = ui.switch("Show Details").bind_value_to(visibility_handler, 'display_field_details').props('dense')
                with ui.row():
                    ui.button(icon='add', on_click=field_handler.show_field_creation_dialog)
                    ui.button(icon='refresh', on_click=lambda: field_handler.load_from_api())

    
ui.run(port=8080, storage_secret="CHANGEME", title= 'Custom Field Management', uvicorn_logging_level="debug", reload=False, native=True , window_size=(1440,900))