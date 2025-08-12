from nicegui import ui, app
from layout.page import get_tool_menu
from .api import load_matter_field_values
from .page import customfield_management_page

def update_nav_menu():
    tool_menu = get_tool_menu()
    with tool_menu:
        with ui.menu_item('Custom Field Management', auto_close=False):
            with ui.item_section().props('side'):
                ui.icon('keyboard_arrow_right')
            with ui.menu().props('anchor="top end" self="top start" auto-close'):
                ui.menu_item('Matters', on_click= lambda: ui.navigate.to('/app/customfield_management/matter'))
                ui.menu_item('Contacts', on_click= lambda: ui.navigate.to('/app/customfield_management/contact'))
        
def init_storage():
    # Initialize the root storage dictionary
    page_data: dict = app.storage.general.setdefault('customfield_management_storage', {})

    # Initialize flat dictionaries for all fields and field sets by ID
    page_data.setdefault('custom_field_data', {})
    page_data.setdefault('custom_field_set_data', {})
    page_data.setdefault('custom_field_map', {})
    page_data.setdefault('custom_field_set_map', {})

    # Initialize per-category sorted ID lists
    for category in ['matter', 'contact']:
        category_data = page_data.setdefault(category, {})
        category_data.setdefault('custom_field_id_list', [])
        category_data.setdefault('custom_field_set_id_list', [])
    
    # Add user API keys
    page_data.setdefault('clio_api_keys', {})

def init():
    # from .page import customfield_management_page
    subpages: ui.sub_pages = app.storage.client['subpages']
    subpages.add('/customfield_management/matter', lambda: customfield_management_page(parent_type="matter"))
    subpages.add('/customfield_management/contact', lambda: customfield_management_page(parent_type="contact"))

    init_storage()
    update_nav_menu()