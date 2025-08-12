import os
from nicegui import ui, app
from layout.page import load_layout

import addons

@ui.page('/')
@ui.page('/app')
@ui.page('/app/{_:path}')  # NOTE: our page should catch all paths
async def index():
    
    await ui.context.client.connected()
    user = os.getlogin()

    app.storage.user['current_user'] = user
    app.storage.client['subpages'] = ui.sub_pages(
        {'/': main}, 
        root_path='/app/').classes('page-container')
    
    load_layout()
    addons.init()

    last_page = app.storage.user.get('last_page', '/')
    if last_page != '/':
        ui.navigate.to(f'/app{last_page}')

def main():
    ui.label('Available pages can be found under the Tools menu')

    
app.native.start_args['private_mode'] = False
app.native.start_args['storage_path'] = '.nicegui'

if __name__ == "__main__":
    ui.run(port=8080, storage_secret="CHANGEME", title= 'Custom Field Management', uvicorn_logging_level="debug", reload=False, native=True , window_size=(1440,900), reconnect_timeout=10)
