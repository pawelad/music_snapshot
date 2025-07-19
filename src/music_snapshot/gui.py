"""NiceGUI based  for `music_snapshot` GUI."""
from nicegui import ui

# Font Awesome
ui.add_head_html('<link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.7.1/css/all.min.css" rel="stylesheet" />')

# Header
with ui.header(elevated=True).classes('flex justify-between text-h4'):
    ui.label('Music Snapshot').classes('bold')

    # Settings modal
    with ui.dialog() as dialog, ui.card():
        # Spotify config
        with ui.card().classes('w-[500px]'):
            with ui.element('q-item').classes('text-h5'):
                with ui.element('q-item-section').props('avatar'):
                    ui.avatar('fa fa-brands fa-spotify', color="green")

                with ui.element('q-item-section'):
                    ui.label('Spotify')

            with ui.card_section().classes('w-full pt-0'):
                spotify_client_id = ui.input(label='Spotify Client ID')
                spotify_client_secret = ui.input(label='Spotify Client Secret', password=True)

        # Last.fm config
        with ui.card().classes('w-[500px]'):
            with ui.element('q-item').classes('text-h5'):
                with ui.element('q-item-section').props('avatar'):
                    ui.avatar('fa fa-brands fa-lastfm', color="pink")

                with ui.element('q-item-section'):
                    ui.label('Last.fm')
            with ui.card_section().classes('w-full pt-0'):
                lastfm_api_key = ui.input(label='Last.fm API Key')
                lastfm_api_secret = ui.input(label='Last.fm API Secret', password=True)
                lastfm_username = ui.input(label='Last.fm username')

        ui.button('Close', on_click=dialog.close)

    ui.button(icon='settings', color='secondary', on_click=dialog.open).props('round')

with ui.row().classes("w-[600px] self-center"):
    with ui.card().classes('w-full'):
        ui.label("Select start date and time").classes('text-h5')

        # Start date
        # https://nicegui.io/documentation/date#input_element_with_date_picker
        with ui.input('Start date').classes("w-full") as date:
            with ui.menu().props('no-parent-event') as menu:
                with ui.date().bind_value(date):
                    with ui.row().classes('justify-end'):
                        ui.button('Close', on_click=menu.close).props('flat')
            with date.add_slot('append'):
                ui.icon('edit_calendar').on('click', menu.open).classes('cursor-pointer')

        # Start time
        # https://nicegui.io/documentation/time#input_element_with_time_picker
        with ui.input('Start time').classes("w-full") as time:
            with ui.menu().props('no-parent-event') as menu:
                with ui.time().bind_value(time):
                    with ui.row().classes('justify-end'):
                        ui.button('Close', on_click=menu.close).props('flat')
            with time.add_slot('append'):
                ui.icon('access_time').on('click', menu.open).classes('cursor-pointer')

        with ui.row().classes('w-full justify-end'):
            ui.button('Load tracks')

    with ui.card().classes('w-full'):
        ui.label("Select first track").classes('text-h5')

        # https://github.com/zauberzeug/nicegui/discussions/774#discussioncomment-7271282
        columns = [
            {'name': 'name', 'label': 'Name', 'field': 'name'},
            {'name': 'age', 'label': 'Age', 'field': 'age'},
        ]
        rows = [
            {'id': 1, 'name': 'Alice', 'age': 18},
            {'id': 2, 'name': 'Bob', 'age': 21},
            {'id': 3, 'name': 'Carol', 'age': 22},
        ]


        def handle_row_click(e):
            """
            Source: https://quasar.dev/vue-components/table
            Quasar Table: QTable API: Events: @row-click
            """
            evt: dict = e.args[0]  # JS event object
            row: dict = e.args[1]  # The row upon which user has clicked/tapped
            row_index: int = e.args[2]  # Index of the row in the current page

            table.selected.clear()
            table.selected.append(row)

            table.update()


        table = ui.table(columns=columns, rows=rows).classes('w-72')
        table.on('rowClick', handle_row_click)

        ui.label('').bind_text_from(table, 'selected', lambda val: f'Current selection: {val}')

if __name__ in {"__main__", "__mp_main__"}:
    ui.run(title='My App', dark=True, native=True , window_size=(700, 900), fullscreen=False)
    # ui.run(dark=True)
