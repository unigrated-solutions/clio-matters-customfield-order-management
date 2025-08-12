import os
import sys
from typing import TYPE_CHECKING
import webbrowser
from urllib.parse import urlencode

from nicegui import ui, run, app

from .api import create_custom_field_set, update_custom_field, create_custom_field

if TYPE_CHECKING:
    from nicegui.events import KeyEventArguments


def find_chrome_path():
    """
    Attempts to find the Google Chrome executable path in an OS-independent manner.
    Returns the path if found, otherwise None.
    """
    if sys.platform.startswith('win'):
        # Windows
        chrome_paths = [
            os.path.join(os.environ.get('PROGRAMFILES', ''), 'Google', 'Chrome', 'Application', 'chrome.exe'),
            os.path.join(os.environ.get('PROGRAMFILES(X86)', ''), 'Google', 'Chrome', 'Application', 'chrome.exe')
        ]
    elif sys.platform == 'darwin':
        # macOS
        chrome_paths = [
            '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'
        ]
    else:
        # Linux and other Unix-like systems
        chrome_paths = [
            '/usr/bin/google-chrome',
            '/usr/bin/chromium-browser'
        ]

    for path in chrome_paths:
        if os.path.exists(path) and os.path.isfile(path):
            return path
    
    # Check PATH environment variable
    if 'PATH' in os.environ:
        for p_dir in os.environ['PATH'].split(os.pathsep):
            if sys.platform.startswith('win'):
                exe_name = 'chrome.exe'
            else:
                exe_name = 'google-chrome' # Or 'chromium-browser'
            
            full_path = os.path.join(p_dir, exe_name)
            if os.path.exists(full_path) and os.path.isfile(full_path):
                return full_path

    return None

async def confirm_dialog(message: str = "Are you sure?") -> ui.dialog:
    def key_press(e: KeyEventArguments):
        if e['key'] == 'Enter':
            dialog.submit(True)
        elif e['key'] == 'Escape':
            dialog.submit(False)
            
    with ui.dialog() as dialog, ui.card():
        ui.label(message).classes('text-lg').style('white-space: pre-line')

        with ui.row().classes('justify-end'):
            ui.button('Cancel', on_click=lambda: dialog.submit(False)).props('flat')
            ui.button('Confirm', on_click=lambda: dialog.submit(True)).props('color=primary')

        # Handle keyboard shortcuts
        dialog.on('keydown', lambda e: key_press(e.args))

    dialog.open()
    result = await dialog
    return result
    
async def launch_field_set_dialog(action_type= "post", **kwargs):

    def show(
        name: str = '',
        default: bool = False,
        parent_type: str = 'Matter'
    ) -> ui.dialog:
        
        with ui.dialog() as create_dialog, ui.card().style('width: 500px;'):
            ui.label('Create Custom Field Set').classes('w-full text-xl font-bold')

            name_input = ui.input('Name', value=name, placeholder='Field Set Name').classes('w-full').props('dense')
            default_checkbox = ui.checkbox(text=f'Default, this will be applied to all new and existing {parent_type}s')
            parent_type_selector = ui.select(["Matter", "Contact"], value=parent_type)
            
            with ui.row().classes('justify-end'):
                ui.button('Cancel', on_click=lambda: create_dialog.submit(None)).props('flat')

                def handle_submit():
                    result = {
                        'name': name_input.value,
                        'displayed': default_checkbox.value,
                        'parent_type': parent_type_selector.value,
                    }
                    create_dialog.submit(result)

                ui.button('Create', on_click=handle_submit).props('color=primary')

        return create_dialog

    async def create_field_set(**kwargs):
        response = await run.io_bound(create_custom_field_set, client=app.storage.tab['custom_field_management_api'], **kwargs)
        if response:
            ui.notify(f'Field Created: {kwargs}')
        
    dialog = show(**kwargs)
    result = await dialog
    
    if action_type == "post" and result:
        print(f"Field Set Dialog Results: {result}")
        await create_field_set(**result)
        
async def launch_field_dialog(method= "post", **kwargs):
    print("Enter Field Dialog")
    def launch_custom_field_dialog(
        method,
        name: str = None,
        field_type: str = None,
        default: bool = False,
        required: bool = False,
        display_order: int = None,
        picklist_options: list[dict] = [],
        **kwargs
    ) -> ui.dialog:
        print("Launch Field Dialog")
        field_types = [
            "checkbox", "contact", "currency", "date", "time", "email",
            "matter", "numeric", "picklist", "text_area", "text_line", "url"
        ]
        picklist_options = picklist_options.copy() # Copy to remove reference to storage
        with ui.dialog() as create_dialog, ui.card():
            ui.label('Create Custom Field').classes('w-full text-xl font-bold') \
                .bind_visibility_from(locals(), 'method', backward=lambda v: v == 'post')
            ui.label('Edit Custom Field').classes('w-full text-xl font-bold') \
                .bind_visibility_from(locals(), 'method', backward=lambda v: v == 'patch')

            name_input = ui.input(placeholder="Enter field name" , value=name).classes('w-full') \
                .props('autofocus')
            
            field_type_input = ui.select(field_types, label='Field Type', value=field_type) \
                .classes('w-full') \
                .props('dense') \
                .style('text-transform: capitalize;') \
                .bind_enabled_from(locals(), 'method', backward=lambda v: v == 'post')


            # === Dynamic Picklist Entry ===
            picklist_container = ui.column().classes('w-full')
            picklist_container.bind_visibility_from(field_type_input, 'value', value='picklist')

            added_names: list[str] = []
            removed_ids: list[str] = []
            with picklist_container:
                picklist_options_container = ui.column().classes('w-full')

                def add_picklist_option(name: str, existing_id: str = None):
                    name = name.strip()
                    if not name:
                        return

                    if not existing_id:
                        added_names.append(name)

                    with picklist_options_container:
                        with ui.row().classes('w-full gap-2 items-center').style('width: 100%;') as option_row:
                            ui.label(name).classes('font-bold').style('flex: 1;')

                            def handle_remove():
                                if existing_id:
                                    removed_ids.append(existing_id)
                                option_row.delete()

                            ui.button('❌', on_click=handle_remove).props('dense flat color=negative')

                # Add preexisting options using the same function
                for item in picklist_options or []:
                    if isinstance(item, dict):
                        value = item.get('option', '').strip()
                        option_id = item.get('id')  # assumed format
                    else:
                        value = str(item).strip()
                        option_id = None

                    if value:
                        add_picklist_option(value, existing_id=option_id)

                # Input and add button
                with ui.row().classes('w-full gap-2 items-center').style('width: 100%;'):
                    input_field = ui.input(placeholder='Picklist option...') \
                        .props('dense') \
                        .style('flex: 1;')
                    ui.run_javascript(f'getElement("{input_field.id}").$refs.qRef.focus()')
                    add_button = ui.button('➕').props('dense')

                    def handle_add():
                        value = input_field.value.strip()
                        if value:
                            add_picklist_option(value)
                            input_field.set_value('')  # Clear input

                    add_button.on('click', handle_add)
                    input_field.on('keydown.enter', lambda _: handle_add())

            display_order_input = ui.input('Display Order (optional)', value=display_order).classes('w-full').props('dense') \
                .bind_visibility_from(locals(), 'method', backward=lambda v: v == 'post')

            default_checkbox = ui.checkbox('Default').props('dense')
            if default:
                default_checkbox.set_value(True)

            required_checkbox = ui.checkbox('Required').props('dense')
            if required:
                required_checkbox.set_value(True)

            with ui.row().classes('justify-end'):
                ui.button('Cancel', on_click=lambda: create_dialog.submit(None)).props('flat')

                def handle_submit():
                    result = {}


                    result['name'] = name_input.value
                    result['field_type'] = field_type_input.value
                    result['default'] = default_checkbox.value
                    result['required'] = required_checkbox.value
                    result['display_order'] = display_order_input.value
                    # current_display_order = display_order_input.value or None
                    # if str(current_display_order) != str(display_order if display_order is not None else ''):
                    #     result['display_order'] = current_display_order

                    # Picklist changes
                    if result.get('field_type', field_type) == 'picklist':
                        result['added_names'] = added_names
                        result['removed_ids'] = removed_ids
                        if added_names or removed_ids:
                            result['picklist_options'] = [
                                {'option': o['option']} if isinstance(o, dict) else {'option': o}
                                for o in picklist_options
                            ]

                    create_dialog.submit(result)


                ui.button('Confirm', on_click=handle_submit).props('color=primary')
            create_dialog.on('keypress.enter', handle_submit)
            
            ui.run_javascript(f'getElement({name_input.id}).$refs.qRef.focus()')
        
        return create_dialog
    
    async def create_field(**kwargs):
        ui.notify(f'Request: {kwargs}')
        client = app.storage.tab['custom_field_management_api']
        response = await run.io_bound(create_custom_field, client=client, **kwargs)
        if response:
            reload_func = app.storage.client['load_field_storage']
            await reload_func()

    dialog = launch_custom_field_dialog(method, **kwargs)
    result:dict = await dialog

    if method == "post" and result:
        payload = {
            "display_order": result.get('display_order'),
            "name": result.get('name'),
            "displayed": result.get("displayed", False),
            "field_type": result.get('field_type'),
            "required": result.get('required'),
            "parent_type": app.storage.client.get('field_parent_type'),
            "picklist_options": [{'option': name} for name in result.get('added_names', [])],
        }
        print(payload)
        # Remove keys with None values
        payload = {k: v for k, v in payload.items() if v is not None}
        await create_field(**payload)
            
    if method == "patch" and result:
        field_id = kwargs.get('id')
        
        field_data = app.storage.general["customfield_management_storage"]["custom_field_data"].get(field_id)
        if not field_data:
            return
        
        patch_payload = {'id': field_id}

        # === Compare standard fields ===
        for key in ['name', 'field_type', 'required', 'display_order', 'displayed']:
            if result.get(key) != field_data.get(key):
                patch_payload[key] = result.get(key)

        # === Handle picklist option diffs ===
        patch_picklist_options = []

        # Map original picklist options by name → id
        original_options = field_data.get('picklist_options', [])
        original_name_to_id = {opt.get('option'): opt.get('id') for opt in original_options if opt.get('option')}

        # Handle additions
        for name in result.get('added_names', []):
            patch_picklist_options.append({'option': name})

        # Handle removals
        for id in result.get('removed_ids', []):
            patch_picklist_options.append({'id': id, '_deleted': True})

        if patch_picklist_options:
            patch_payload['picklist_options'] = patch_picklist_options

        # ✅ Remove keys with None values
        patch_payload = {k: v for k, v in patch_payload.items() if v is not None}

        # print("📦 PATCH Payload:", patch_payload)
        client = app.storage.tab['custom_field_management_api']
        response = update_custom_field(client=client, **patch_payload).get('data')
        if response:
            app.storage.general["customfield_management_storage"]["custom_field_data"][field_id] = response

    if method == "duplicate" and result:
        payload = {
            "display_order": result.get('display_order'),
            "name": result.get('name'),
            "displayed": result.get("displayed", False),
            "field_type": result.get('field_type'),
            "required": result.get('required'),
            "parent_type": app.storage.client.get('field_parent_type'),
            "picklist_options": [{'option': name} for name in result.get('added_names', [])],
        }
        print(payload)
        # Remove keys with None values
        payload = {k: v for k, v in payload.items() if v is not None}
        await create_field(**payload)
        
async def fix_field_display_order_dialog(parent_type='matter'):
        
    def fix_dialog(parent_type) -> ui.dialog:

        def open_browser(parent_type):
            base_url = "https://app.clio.com/nc/#/settings"
            path = "settings/custom_fields"
            params = {'parent_type': parent_type, 'prefix': 'custom_matter_fields'}
            full_url = f"{base_url}?path={path}%3F{urlencode(params)}"
            
            webbrowser.open(full_url)

        with ui.dialog().classes('w-full max-w-2xl') as dialog, ui.card().classes('w-full p-6 rounded shadow-lg'):
            with ui.column().classes('w-full gap-3 items-center'):
                ui.label('⚠️ Custom Field Order Warning').classes('text-xl font-bold text-red-600 text-center')
                ui.separator()
                ui.label('The display orders of the Custom Fields are not sequential. Please follow these steps to fix it:') \
                    .classes('text-base text-gray-700 text-center')

                steps = [
                    '1) Use the button below to open the Clio Custom Field settings',
                    '2) Click the "Modify Order" button on the settings page',
                    '3) Scroll to the bottom and click "Save Order"',
                    '4) Once complete, return to this page and confirm',
                ]

                for step in steps:
                    ui.label(step).classes('text-sm text-gray-600')

                ui.button('🔗 Open Clio Settings', on_click=lambda: open_browser(parent_type)) \
                    .props('color=primary outline').classes('mt-4 self-center')

            with ui.row().classes('w-full justify-center pt-4'):
                ui.button('Cancel', on_click=lambda: dialog.submit(False)).props('flat')
                ui.button('Confirm', on_click=lambda: dialog.submit(True)).props('color=primary')

        return dialog
        
    fix_field_dialog = fix_dialog(parent_type)
    confirmed = await fix_field_dialog
    # ui.notify(confirmed)
    return confirmed

def loading_dialog() -> ui.dialog:
    with ui.dialog() as loading_dialog, ui.card().classes("flex items-center justify-center"):
        # Centering the label and spinner in a vertical stack
        with ui.column().classes("items-center justify-center"):
            ui.label('Loading Content...')
            ui.spinner()

    loading_dialog.open()
    return loading_dialog