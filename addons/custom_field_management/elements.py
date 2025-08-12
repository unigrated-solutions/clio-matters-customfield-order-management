# from __future__ import annotations
from typing import TYPE_CHECKING
from collections import OrderedDict

import logging

from nicegui import ui, app, run

from .api import *
from .dialogs import confirm_dialog, fix_field_display_order_dialog, launch_field_dialog
from .helper import get_matters_containing_field
logging.basicConfig(level=logging.DEBUG)
    
def api_input(user, callback) -> ui.input:
    key_storage = app.storage.general.setdefault('customfield_management_storage', {}).setdefault('clio_api_keys', {})
    current_user = user
    
    async def copy_token(selected_token):
        ui.run_javascript(f'navigator.clipboard.writeText({json.dumps(selected_token)})')
        ui.notify('Copied to clipboard')
    
    access_token = ui.input(
        placeholder="Enter Access Token...",
        password=True,
        password_toggle_button=True
    ).props('v-model="text" dense="dense" size=48').style(
        'width: 250px; border-radius: 5px; '
        'background-color: white; color: #333; padding-left: 12px;'
    ).bind_value(key_storage, user)
    
    # Using to update the API client
    if callback:
        access_token.on('change', lambda: callback(access_token.value))
        if access_token.value:
            callback(access_token.value)
            
            
    copy_button = ui.button(icon="content_copy").classes('header-button')
    copy_button.on('click', lambda: copy_token(access_token.value))
    ui.button(icon='help_center').classes('header-button').disable()
    return access_token
        
async def toggle_deleted_fields(value: bool):
    """Toggle visibility of all deleted custom fields."""

    def get_deleted_custom_field_ids() -> list[str]:
        """Return a list of custom field IDs where 'deleted' is True."""
        storage = app.storage.general.get('customfield_management_storage', {})
        custom_field_data = storage.get('custom_field_data', {})

        return [
            field_id
            for field_id, data in custom_field_data.items()
            if isinstance(data, dict) and data.get('deleted') is True
        ]

    def toggle_visibility(field_id: str, visible: bool):
        try:
            field_card: FieldCard = app.storage.client['fields'].get(int(field_id))
            if field_card:
                field_card.set_visibility(visible)
            # else:
            #     ui.notify(f'FieldCard not found for ID: {field_id}')
        except Exception as e:
            ui.notify(f'Error updating field {field_id}: {e}')

    deleted_fields = get_deleted_custom_field_ids()
    for field_id in deleted_fields:
        toggle_visibility(field_id, value)

class FieldLabel(ui.label):
    def __init__(self, clio_id) -> None:
        super().__init__()
        self.clio_id = str(clio_id)
        self.name: str = None
        self.deleted: bool = False
        
        self.style('font-size: 1.3em; font-weight: bold; color: #333;')
        self.data = app.storage.general["customfield_management_storage"]["custom_field_data"][self.clio_id]
        self.refresh()

    def update_label(self, name):
        try:
            self.set_text(name)
        except Exception:
            self.set_text(f"ERROR{self.clio_id}")
        
    def refresh(self):
        try:
            self.name = self.data.get('name')
            self.deleted = self.data.get('deleted')
            label_name = f'{self.name} (Deleted)' if self.deleted else self.name
            self.set_text(label_name)
        except Exception:
            self.set_text(f"ERROR{self.clio_id}")
    
class FieldCard(ui.card):
    
    def __init__(self, clio_id: str) -> None:
        super().__init__()
        
        self.field_list: list = app.storage.client.setdefault('field_list', [])
        self.field_list.append(self)

        self.field_dict: dict = app.storage.client.setdefault('field_dict', {})
        self.field_dict[clio_id] = self
        
        self.selected_fields:list = app.storage.client['selected_fields']
        
        self.clio_id = str(clio_id)
        self.tight().classes('field-card').props('draggable')
        self.last_click = 0
        self.selected = False
        self.content = None
        self.updating_name=False
        
        self.reload_content()
        
        self.on('click', self.click)
        self.on('dblclick', self.edit)
        self.on('contextmenu', lambda: ui.notify(self.clio_id))
        # self.on('dragstart', lambda e: ui.notify(e))
        # self.on('dragend', lambda e: ui.notify(e))
        # self.on('dragover.prevent', lambda e: ui.notify(e))
        # self.on('dragenter.prevent', lambda e: ui.notify(e))

    def get_parent(self):
        field_container:FieldContainer = app.storage.client.get('field_container')
        field_container.move_selected_cards(self.clio_id, position="before")
            
    def reload_content(self):
        self.clear()
        with self:
            self.content = FieldLabel(self.clio_id)
            duplicate_menu = None
            with ui.context_menu().props('auto-close'):

                # Only show these when more than one field is selected
                ui.menu_item("Insert Above", lambda: app.storage.client['field_container'].move_selected_cards(self.clio_id, "before"))
                ui.menu_item("Insert Below", lambda: app.storage.client['field_container'].move_selected_cards(self.clio_id, "after"))   
            
                # Only show these when less than two field is selected
                duplicate_menu = ui.menu_item("Duplicate") \
                    .bind_visibility_from(
                        app.storage.client,
                        'selected_fields',
                        backward=lambda v: (len(v) == 1 and self.selected) or (len(v) == 0 and not self.selected)
                        )
                
                duplicate_menu.on('click', self.duplicate_field)
                ui.menu_item('Get Containing matters', on_click= lambda: get_matters_containing_field(self.clio_id))
                # ui.menu_item("Copy", on_click=lambda: ui.notify(self.to_dict())) \
                #     .bind_visibility_from(self.event_handler, 'fields_selected_count', backward=lambda v: (v == 1 and self.selected) or (v == 0 and not self.selected)
                #     )
                    
                # ui.menu_item("Create Field Above", on_click=lambda: self.field_handler.show_field_creation_dialog(display_order=self.display_order -1)) \
                #     .bind_visibility_from(self.event_handler, 'fields_selected_count', backward=lambda v: (v == 1 and self.selected) or (v == 0 and not self.selected) )
                
                # ui.menu_item("Create Field Below", on_click=lambda: self.field_handler.show_field_creation_dialog(display_order=self.display_order +1)) \
                #     .bind_visibility_from(self.event_handler, 'fields_selected_count', backward=lambda v: (v == 1 and self.selected) or (v == 0 and not self.selected) )
                           
    async def edit(self):
        try:
            kwargs = app.storage.general['customfield_management_storage']["custom_field_data"][self.clio_id]
            kwargs['id'] = self.clio_id

            await launch_field_dialog(method='patch', **kwargs)
            self.reload_content()
            await self.update()
        except Exception as e:
            logging.debug(e)
        finally:
            return
        
    def update_content(self, e):
        ui.notify(e.sender.value)
        
    def refresh(self):
        self.content.refresh()

    def update_visibility(self, search_text):
        if search_text not in self.content.text.lower():
            self.set_visibility(False)
            
        if search_text in self.content.text.lower() and not self.visible:
            self.set_visibility(True)
            
        if search_text == "" and not self.visible:
            self.set_visibility(True)
            
    async def click(self, e):
        app.storage.client['last_clicked'] = self
        
        if self.updating_name:
            return
        
        alt_pressed = e.args.get('altKey')
        shift_pressed = e.args.get('shiftKey')
        ctrl_pressed = e.args.get('ctrlKey')
        click_type = e.args.get('type')

        if not any([ctrl_pressed, shift_pressed, alt_pressed]):
            selected_fields = self.selected_fields.copy()
            for field in selected_fields:
                field.deselect()

        if shift_pressed and self.selected_fields:
            try:
                current_index = self.field_list.index(self)
                last_selected = self.selected_fields[-1]
                last_index = self.field_list.index(last_selected)

                start = min(current_index, last_index)
                end = max(current_index, last_index)

                for i in range(start, end + 1):
                    if self.field_list[i].visible:
                        self.field_list[i].select()
            except ValueError:
                # Safety fallback if items are missing
                self.select()
        else:
            if self.selected:
                self.deselect()
            else:
                self.select()
                
    def select(self):
        """Select this card and update its background color."""
        self.selected_fields.append(self)
        self.selected = True
        self.style('background-color: lightblue;')
        
    def deselect(self):
        """Deselect this card and remove highlight."""
        self.selected = False
        self.style('background-color: white;')  # Remove highlight
        if time.time() > self.last_click + .2:
            self.updating_name= False
            self.reload_content()
        if self in self.selected_fields:
            self.selected_fields.remove(self)

    async def duplicate_field(self):
        data = app.storage.general["customfield_management_storage"]["custom_field_data"][self.clio_id].copy()
        data['display_order'] += 1
        with self:
            await launch_field_dialog(method='duplicate', **data)
        
class FieldSetCard(ui.card):
    def __init__(self, clio_id: str) -> None:
        super().__init__()
        self.clio_id = clio_id

        self.tight().classes('justify-center border border-gray-200 rounded-md').style('width: 100%; padding: 5px;')
        with self:
            # UI Elements
            self.title = ui.label().classes(
                'text-xl font-bold w-full text-center border border-gray-300 rounded px-2 py-1'
            ).style('background-color: #d1d5db; cursor: pointer')
            self.card_table = ui.grid(columns=2).classes('w-full gap-3')

            # Data containers
            self.field_labels: dict[int, ui.label] = {}  # {field_id: label_element}
            self.field_data_lookup = {}
            self.field_set_data = {}

            self.load()

    def load(self):
        """Generate field labels once and store their elements."""
        storage = app.storage.general.get('customfield_management_storage', {})
        self.field_set_data = storage.get('custom_field_set_data', {}).get(self.clio_id, {})
        self.field_data_lookup = storage.get('custom_field_data', {})

        if not self.field_set_data:
            ui.notify(f"⚠️ No field set found for ID {self.clio_id}", color='red')
            return

        self.title.set_text(self.field_set_data.get('name', f"Field Set {self.clio_id}"))

        custom_fields = self.field_set_data.get('custom_fields', [])

        # Sort by display_order at creation time
        sorted_fields = sorted(
            custom_fields,
            key=lambda f: self.field_data_lookup.get(str(f['id']), {}).get('display_order', float('inf'))
        )

        with self.card_table:
            for index, field in enumerate(sorted_fields):
                field_id = int(field.get('id'))
                field_info = self.field_data_lookup.get(str(field_id), {})
                field_name = field_info.get('name', f"Field {field_id}")

                label = ui.label(field_name).classes('field-label')

                self.field_labels[field_id] = label

    def refresh(self):
        """Reorder existing field labels based on updated display_order."""
        storage = app.storage.general.get('customfield_management_storage', {})
        field_data = storage.get('custom_field_data', {})

        # Sort field IDs by new display_order
        sorted_field_ids = sorted(
            self.field_labels.keys(),
            key=lambda fid: field_data.get(str(fid), {}).get('display_order', float('inf'))
        )

        # Move UI elements in-place
        for index, fid in enumerate(sorted_field_ids):
            label = self.field_labels.get(fid)
            if label:
                print(f"Moving Label: {label.text}")
                label.move(target_index=index)

class FieldSetContainer(ui.column):
    def __init__(self, parent_type: str = 'matter'):
        super().__init__()
        self.style('width: 100%; gap: 1rem;')  # Full width with spacing between cards
        self.parent_type = parent_type.lower()

        # self.load()

    def refresh(self):
        """Clear and reload the field set cards."""
        self.clear()

        with self:
            self.load()

    def load(self):
        try:
            field_set_ids = app.storage.general['customfield_management_storage'][self.parent_type.lower()]['custom_field_set_id_list']

            for id in field_set_ids:
                app.storage.client['field_set_cards'][id] = FieldSetCard(str(id))
                
        except Exception as e:
            ui.notify(f"❌ Failed to load field sets: {e}", color='red')
                
    async def load_from_api(self):
        client = app.storage.tab['custom_field_management_api']
        response = await run.io_bound(get_custom_field_sets, client, self.parent_type)
        data = response.get('data', [])

        def transform_to_dict(data: list[dict]) -> dict[str, dict]:
            """Convert list of dicts into a dict using 'id' (as str) as key."""
            return {str(item['id']): {k: v for k, v in item.items() if k != 'id'} for item in data}

        def split_ids_by_parent_type(data: list[dict]) -> dict[str, list[int]]:
            from collections import defaultdict

            parent_groups: dict[str, list[tuple[str, int]]] = defaultdict(list)
            for item in data:
                parent_type = item.get('parent_type', 'Matter')
                name = item.get('name', '')
                parent_groups[parent_type].append((name.lower(), item['id']))

            return {
                parent: [fid for name, fid in sorted(items)]
                for parent, items in parent_groups.items()
            }

        def build_custom_field_map(data: list[dict]) -> dict[int, list[int]]:
            field_map: dict[int, list[int]] = {}
            for field_set in data:
                field_set_id = field_set['id']
                for cf in field_set.get('custom_fields', []):
                    field_map.setdefault(cf['id'], []).append(field_set_id)
            return field_map

        def build_custom_field_set_map(data: list[dict]) -> dict[int, list[int]]:
            set_map: dict[int, list[int]] = {}
            for field_set in data:
                field_set_id = field_set['id']
                custom_field_ids = [cf['id'] for cf in field_set.get('custom_fields', []) if 'id' in cf]
                set_map[field_set_id] = custom_field_ids
            return set_map

        def store_results(
            dict_data: dict,
            id_lists: dict[str, list[int]],
            field_map: dict[int, list[int]],
            field_set_map: dict[int, list[int]]
        ) -> None:
            storage = app.storage.general.get('customfield_management_storage')
            storage['custom_field_set_data'] = dict_data
            storage['custom_field_map'] = field_map
            storage['custom_field_set_map'] = field_set_map
            for parent_type, ids in id_lists.items():
                section = storage.get(parent_type.lower())
                section['custom_field_set_id_list'] = ids  # already sorted

        custom_field_set_dict = transform_to_dict(data)
        id_lists_by_type = split_ids_by_parent_type(data)
        custom_field_map = build_custom_field_map(data)
        custom_field_set_map = build_custom_field_set_map(data)

        store_results(
            custom_field_set_dict,
            id_lists_by_type,
            custom_field_map,
            custom_field_set_map
        )

        self.refresh()
        
class FieldContainer(ui.column):

    def __init__(self, parent_type: str = None, global_storage=None):
        super().__init__()  # ✅ correct super call
        self.parent_type = parent_type
        self.classes('scroll-content')
        app.storage.client['field_container'] = self
        self.global_storage = global_storage

    def refresh(self):
        self.clear()
        with self:
            for id in self.global_storage[self.parent_type]["custom_field_id_list"]:
                app.storage.client['fields'][id] = FieldCard(clio_id=id)
        
    async def load_from_api(self, api_client = None):
        if not api_client:
            api_client = app.storage.tab.get('custom_field_management_api')
        
        if not api_client:
            ui.notify('No client started')
            return

        response = await run.io_bound(get_custom_fields, api_client, self.parent_type)
        data = response.get('data', [])

        def build_data_map(items: list[dict]) -> OrderedDict:
            result = OrderedDict()
            for item in items:
                item_id = str(item['id'])  # to match your example structure
                item_copy = item.copy()
                del item_copy['id']
                result[item_id] = item_copy
            return result

        def build_sorted_id_lists(items: list[dict]) -> tuple[dict[str, list[int]], bool]:
            from collections import defaultdict

            sorted_ids = defaultdict(list)
            inconsistencies_found = False

            grouped = defaultdict(list)
            for item in items:
                grouped[item['parent_type'].lower()].append((item['display_order'], item['id']))

            for parent_type, pairs in grouped.items():
                seen_orders = set()
                display_orders = []

                for order, item_id in pairs:
                    if order in seen_orders:
                        inconsistencies_found = True
                    seen_orders.add(order)
                    display_orders.append(order)

                sorted_ids[parent_type] = [item_id for _, item_id in sorted(pairs)]

                if display_orders:
                    min_order = min(display_orders)
                    max_order = max(display_orders)
                    expected = set(range(min_order, max_order + 1))
                    if expected != seen_orders:
                        inconsistencies_found = True

            return dict(sorted_ids), inconsistencies_found

        storage = app.storage.general.setdefault('customfield_management_storage', {})

        custom_field_id_lists, has_inconsistencies = build_sorted_id_lists(data)
        if has_inconsistencies:
            reload = await fix_field_display_order_dialog(parent_type=self.parent_type)
            if reload:
                await self.load_from_api()
            return
    
            
        for parent_type, id_list in custom_field_id_lists.items():
            storage.setdefault(parent_type, {})['custom_field_id_list'] = id_list

        custom_field_data = build_data_map(data)
        storage['custom_field_data'] = custom_field_data
        
        self.refresh()

    def move_selected_cards(self, target_id: str, position: str) -> None:

        selected_cards = app.storage.client.get('selected_fields', [])
        if not selected_cards:
            ui.notify("No cards selected!", color="red")
            return
        
        card_lookup = {card.clio_id: card for card in selected_cards}
        moving_ids = [card.clio_id for card in selected_cards]

        # Sort selected IDs by display_order
        field_data = app.storage.general['customfield_management_storage']['custom_field_data']
        sorted_ids = sorted(
            moving_ids,
            key=lambda fid: field_data.get(fid, {}).get('display_order', float('inf'))
        )

        field_order_list: list[int] = self.global_storage.get(self.parent_type.lower(), {}) \
            .get("custom_field_id_list", []).copy()

        try:
            target_index = field_order_list.index(int(target_id))
        except ValueError:
            ui.notify(f"Target ID {target_id} not found.", color="red")
            return

        moved_so_far: list[int] = []

        for i, fid in enumerate(sorted_ids):
            fid_int = int(fid)

            # Determine insert index
            if not moved_so_far:
                if position == "before":
                    insert_index = max(target_index, 0)
                elif position == "after":
                    insert_index = target_index + 1
                else:
                    insert_index = target_index
            else:
                last_inserted = moved_so_far[-1]
                insert_index = field_order_list.index(last_inserted) + 1

            # Locate current position before mutation
            try:
                current_index = field_order_list.index(fid_int)
            except ValueError:
                ui.notify(f"Field ID {fid_int} not found in current list.", color="red")
                continue

            # Always pop before insert, regardless of direction
            field_order_list.pop(current_index)
            adjusted_index = insert_index - 1 if current_index < insert_index else insert_index
            field_order_list.insert(adjusted_index, fid_int)

            # Call API and move UI only if API call succeeded
            if update_custom_field_display_order(fid_int, adjusted_index):
                if fid in card_lookup:
                    card_lookup[fid].move(target_index=adjusted_index)
                moved_so_far.append(fid_int)
            else:
                print(f"Move for {fid} failed — reverting insert")
                field_order_list.pop(adjusted_index)
                field_order_list.insert(current_index, fid_int)  # revert change

        # Final step: persist new order
        self.global_storage[self.parent_type.lower()]["custom_field_id_list"] = field_order_list

        # Update target_id's display_order in storage
        try:
            new_target_index = field_order_list.index(int(target_id))
            target_id_str = str(target_id)
            if target_id_str in field_data:
                field_data[target_id_str]['display_order'] = new_target_index
            else:
                logging.debug(f"Target ID {target_id} not found in custom_field_data")
        except ValueError:
            logging.debug(f"Target ID {target_id} missing from final field_order_list")
            
        # Refresh all affected cards
        affected_ids = moved_so_far + [int(target_id)]
        refreshed_card_ids = set()

        for field_id in affected_ids:
            field_set_ids = app.storage.general['customfield_management_storage']['custom_field_map'].get(field_id, [])
            for set_id in field_set_ids:
                if set_id in refreshed_card_ids:
                    continue
                field_set_card: FieldSetCard = app.storage.client['field_set_cards'].get(set_id)
                if field_set_card:
                    field_set_card.refresh()
                    refreshed_card_ids.add(set_id)
            
    async def delete_custom_fields(self):
        names = []
        ids = []
        
        for card in app.storage.client['fields']:
            if card.selected:
                names.append(card.name)
                ids.append(card.id)
        message = f'You are about to delete the following fields:\n{names}'
        
        if await confirm_dialog(message):
            for id in ids:
                # delete_custom_field(self.event_handler.api_client, id) #Needs updating
                ui.notify(f'Deleted: {id}')

            
