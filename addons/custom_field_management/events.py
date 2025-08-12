from __future__ import annotations

from nicegui import ui, app
from nicegui.events import GenericEventArguments, KeyEventArguments

from .elements import FieldCard
from .dialogs import launch_field_dialog

async def handle_key_event(e: KeyEventArguments):
    last_clicked: FieldCard = app.storage.client.get('last_clicked')
    
    if e.action.keydown:
        if last_clicked and e.key.name == 'F2':
            await last_clicked.edit()

        elif last_clicked and e.key.name == 'Escape':
            selected_field: list[FieldCard] = app.storage.client['selected_fields'].copy()
            for field in selected_field:
                field.deselect()
            last_clicked = None  # this line should be outside the for-loop if you want it set only once

        elif e.modifiers.ctrl and e.key.name == 'n':
            await launch_field_dialog(method="post")
            
#         # WARNING field will show as "deleted" in Clio's "modify order" tool
#         if e.key == 'Delete' and e.action.keydown:
#             await self.field_container.delete_custom_fields()

