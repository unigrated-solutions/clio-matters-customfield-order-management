import logging

from nicegui import ui, app

from .elements import api_input, toggle_deleted_fields, FieldContainer, FieldSetContainer
from .dialogs import launch_field_set_dialog, fix_field_display_order_dialog, loading_dialog
from .events import *
from .styles import styles
from .helper import get_deleted_custom_field_ids
from layout.page import get_header_containers

from clio_manage_python_client import ClioManage as API_Connection

logging.basicConfig(level=logging.DEBUG)
                    
async def customfield_management_page(parent_type):
    
    current_page = 'customfield_management'
    current_user = app.storage.user['current_user']
    parent_type = parent_type
    field_set_container = None
    field_container = None
    key_input = None
    ui.add_css(styles)
    ui.keyboard(on_key=handle_key_event)
            
    api_client = API_Connection(access_token='', store_responses=False, async_requests=False)
    center_container, right_container = get_header_containers()
    with right_container:
        def update_client_key(new_access_token):
            api_client.set_bearer_token(new_access_token)
            ui.notify('Access Token Set')
            
        right_container.clear()
        key_input:ui.input = api_input(current_user, callback=update_client_key)
        
    with center_container:
        center_container.clear()
        ui.label(f'{parent_type.title()} Custom Fields')
    
    global_storage = app.storage.general['customfield_management_storage']
    
    app.storage.client['field_parent_type'] = parent_type
    app.storage.client['last_clicked'] = None
    app.storage.client['selected_fields'] = []
    app.storage.client['fields'] = {}
    app.storage.client['field_set_cards'] = {}
    
    await ui.context.client.connected()
    loading = loading_dialog()
    app.storage.user['last_page'] = f'/customfield_management/{parent_type}'
    
    app.storage.tab['current_page'] = current_page
    app.storage.tab['custom_field_management_api'] = api_client
    
    async def load_field_storage():
        await field_container.load_from_api(api_client)
        await field_set_container.load_from_api()    
        
    app.storage.client['load_field_storage'] = load_field_storage
    
    with ui.row().classes('page-container') as page_container:
        
        # Left Section - Custom Field Sets
        with ui.column().classes('full-height-container') as fieldset_outer_container:
        
            ui.label('Custom Field Sets').classes(
                'w-full text-2xl font-bold p-2 rounded text-center shadow-sm text-black'
            ).style(
                'background-color: #eff6ff; border: 1px solid #bfdbfe; '
            )
            # Scroll Area for Custom Field Sets
            with ui.scroll_area().classes('scroll-container'):
                field_set_container = FieldSetContainer(parent_type=parent_type)
                
            with ui.row().classes('column-footing'):
                ui.input(placeholder="Filter by name...").classes('filter-box').props('dense size=32').disable()
                
                with ui.row():
                    ui.button(icon='add', on_click=launch_field_set_dialog)
                    
        ui.separator().style('height: 100%; width: 2px; flex-shrink: 0;')

        # Right Section - Custom Fields
        with ui.column().classes('full-height-container') as field_outer_container:
            with ui.row().classes('relative w-full items-center border-2 border-gray-300 p-2 rounded').style(
                'background-color: #eff6ff; border: 1px solid #bfdbfe; '
            ):
                
                # Absolutely centered label
                ui.label('Custom Fields').classes('text-2xl font-bold absolute left-1/2 transform -translate-x-1/2')

                # Right-aligned dropdown
                with ui.row().classes('ml-auto'):
                    with ui.dropdown_button():
                        with ui.column().classes('p-4'):
                            delete_switch = ui.switch(
                                'Show Deleted',
                                value=True,
                                on_change=lambda: toggle_deleted_fields(delete_switch.value)
                            )
                            ui.button('Show Deleted Fields', on_click= lambda: get_deleted_custom_field_ids(parent_type))
            # Scroll area for cards
            with ui.scroll_area().classes('scroll-container'):
                field_container = FieldContainer(parent_type=parent_type, global_storage=global_storage)       

            # Filter row with proper wrapping
            with ui.row().classes('column-footing'):

                def filter_fields():
                    search_text = custom_field_filter.value.strip().lower()
                    logging.debug(f"Filtering with: {search_text}")

                    field_cards = app.storage.client.get('fields', {})

                    for card in field_cards.values():
                        if hasattr(card, 'update_visibility'):
                            card.update_visibility(search_text)
                        else:
                            logging.warning(f"Card {getattr(card, 'clio_id', 'unknown')} does not support visibility filtering.")
                            
                custom_field_filter = ui.input(
                    placeholder="Filter fields by name...",
                    on_change=filter_fields,
                ).classes('filter-box').props('dense size=32')
                with custom_field_filter.add_slot('prepend'):
                    ui.icon('search')
                    
                with custom_field_filter.add_slot('append'):
                    clear_icon = ui.icon('clear').classes('clear-icon') 
                    clear_icon.on('click', lambda: custom_field_filter.set_value(''))
        
                with ui.row():
                    ui.button(icon='add', on_click=launch_field_dialog)
                    ui.button(icon='refresh', on_click= lambda: load_field_storage())

    if key_input.value:
        await load_field_storage()
    
    if custom_field_filter.value:
        filter_fields()
        
    loading.close()