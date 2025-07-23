from nicegui import ui, app
import logging

logging.basicConfig(level=logging.DEBUG)

from .elements import EventHandler, AppElementVisibility
from layout import load_layout, get_tool_menu

def check_storage():
    
    if not app.storage.general.get('matter_custom_fields'):
        app.storage.general['matter_custom_fields'] = []
    if not app.storage.general.get('matter_custom_field_sets'):
        app.storage.general['matter_custom_field_sets'] = []
        
    if not app.storage.general.get('contact_custom_fields'):
        app.storage.general['contact_custom_fields'] = []
    if not app.storage.general.get('contact_custom_field_sets'):
        app.storage.general['contact_custom_field_sets'] = []
        
def add_to_tool_menu(event_handler):
    tool_menu = get_tool_menu()
    with tool_menu:
        with ui.menu_item('Custom Field Management', auto_close=False):
            with ui.item_section().props('side'):
                ui.icon('keyboard_arrow_right')
            with ui.menu().props('anchor="top end" self="top start" auto-close'):
                ui.menu_item('Matters', on_click= lambda: event_handler.set_parent_type('matter'))
                ui.menu_item('Contacts', on_click= lambda: event_handler.set_parent_type('contact'))

@ui.page("/customfield_management")
async def customfield_management_page():
        
    check_storage()
    
    ui.query('.nicegui-content').classes('p-0 m-0 gap-0')
    await ui.context.client.connected()
    
    app.storage.client['fields'] = []
    app.storage.client['field_set_cards'] = []
    parent_type = app.storage.general.get('parent_type', "matter")
    
    event_handler = EventHandler(parent_type)
    visibility_handler = AppElementVisibility()
    app.storage.client['visibility_handler'] = visibility_handler

    # ui.add_body_html('''
    #     <script>
    #         document.addEventListener('DOMContentLoaded', () => {
    #             document.body.style.userSelect = 'none';
    #         });
    #     </script>
    #     ''')
    load_layout(event_handler)
    add_to_tool_menu(event_handler)
    
    with ui.row().style('width: 100%; height: calc(100vh - 50px); margin: 0; padding: 5px 2px; display: flex;') as page_container:
        field_handler, field_set_handler = event_handler.init_containers(page_container)
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
