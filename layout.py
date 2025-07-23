from nicegui import ui, app

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .addons.custom_field_management.elements import EventHandler

file_menu:ui.menu = None
tool_menu:ui.menu = None

def get_file_menu():
    return file_menu
def get_tool_menu():
    return tool_menu

def load_layout(event_handler: "EventHandler") -> None:
    global file_menu, tool_menu
    
    async def copy_token(selected_token):
        ui.run_javascript(f'navigator.clipboard.writeText("{selected_token}")')
        ui.notify('Copied to clipboard')

    def store_access_token(token):
        app.storage.general['access_token'] = token
        ui.notify("Access Token Saved")
        
    with ui.header(elevated=True).style('background-color: #3874c8; padding: 5px 2px;').classes('items-center justify-between'):
        with ui.row():
            with ui.row().classes('w-full items-center').style('gap: 5px;') as menu_bar:
                #App Menu
                with ui.button(text="File").classes('text-white').props('flat').style('height: 30px; width: 60px; '):
                    with ui.menu() as file_menu:
                        # ui.menu_item('Create Access Token', create_access_token)
                        ui.menu_item('Create Access Token').set_enabled(False)
                        ui.separator()
                        ui.menu_item('Close', app.shutdown)
                
                #Tools Menu
                with ui.button(text="Tools").classes('text-white').props('flat').style('height: 30px; width: 60px;'):
                    tool_menu = ui.menu()
                    
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
