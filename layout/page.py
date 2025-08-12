from nicegui import ui, app

app.storage.general.indent = True

file_menu:ui.menu = None
tool_menu:ui.menu = None
center_container:ui.row = None
right_container:ui.row = None

def get_file_menu():
    return file_menu
def get_tool_menu():
    return tool_menu
def get_header_containers():
    return center_container, right_container

def load_layout() -> None:
    global file_menu, tool_menu, center_container,right_container
    
    ui.query('.nicegui-content').classes('m-0 gap-0').style('padding: 0 2px;')
    with ui.header(elevated=True).style('background-color: #3874c8; height:50px; padding: 5px 2px;').classes('flex items-center justify-between'):
        
        # LEFT SECTION (menu bar)
        with ui.row().classes('items-center').style('flex: 1;'):
            with ui.row().classes('items-center').style('gap: 5px;') as menu_bar:
                # App Menu
                with ui.button(text="File").classes('text-white').props('flat').style('height: 30px; width: 60px;'):
                    with ui.menu() as file_menu:
                        ui.separator()
                        ui.menu_item('Close', app.shutdown)

                # Tools Menu
                with ui.button(text="Tools").classes('text-white').props('flat').style('height: 30px; width: 60px;'):
                    tool_menu = ui.menu()

        # CENTER SECTION (always centered)
        with ui.row().classes('justify-center').style('flex: 1;') as center_container:
            with ui.row().classes('items-center'):
                ui.label().classes('text-white')

        # RIGHT SECTION (optional, align right)
        with ui.row().classes('justify-end items-center').style('flex: 1; padding-right: 10px;') as right_container:
            ui.label().classes('text-white')
    
    with ui.footer().style('background-color: #3874c8; height: 50px; padding: 5px 2px;').classes('items-center justify-between'):
        ui.label('FOOTER')