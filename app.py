#!/usr/bin/env python3
import time
import logging
import secrets
from urllib.parse import urlencode

from nicegui import ui

# from addons.custom_field_management.page import customfield_management_page
from addons import field_management

logging.basicConfig(level=logging.DEBUG)
        
@ui.page("/")
async def new_tab():
    ui.navigate.to(field_management)
    
    
ui.run(port=8080, storage_secret="CHANGEME", title= 'Custom Field Management', uvicorn_logging_level="debug", reload=False, native=True , window_size=(1440,900))