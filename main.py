import flet as ft
import os
import shutil
from src.engine import FinLegalEngine

def main(page: ft.Page):
    page.title = "FinLegal-Chat | Advanced AI Assistant"
    page.theme_mode = ft.ThemeMode.DARK
    page.window_width = 1100
    page.window_height = 800
    page.padding = 0
    page.spacing = 0

    engine = FinLegalEngine()
    
    # UI State
    chat_history = ft.Column(expand=True, scroll=ft.ScrollMode.ALWAYS, spacing=10)
    api_key_input = ft.TextField(
        label="OpenAI API Key",
        password=True,
        can_reveal_password=True,
        width=200,
        size=12
    )
    
    def save_api_key(e):
        if api_key_input.value:
            os.environ["OPENAI_API_KEY"] = api_key_input.value
            page.show_snack_bar(ft.SnackBar(ft.Text("API Key saved for this session")))
            page.update()
    uploaded_files_list = ft.Column(spacing=5)
    
    def on_upload_result(e: ft.FilePickerResultEvent):
        if e.files:
            for f in e.files:
                # In a real app, we'd copy to a local temp dir
                dest_path = os.path.join("uploads", f.name)
                os.makedirs("uploads", exist_ok=True)
                shutil.copy(f.path, dest_path)
                
                # Ingest into engine
                try:
                    engine.ingest_document(dest_path)
                    uploaded_files_list.controls.append(
                        ft.Row([
                            ft.Icon(ft.icons.INSERT_DRIVE_FILE, color="blue"),
                            ft.Text(f.name, size=12)
                        ])
                    )
                    page.show_snack_bar(ft.SnackBar(ft.Text(f"Successfully analyzed {f.name}")))
                except Exception as ex:
                    page.show_snack_bar(ft.SnackBar(ft.Text(f"Error: {str(ex)}")))
            page.update()

    file_picker = ft.FilePicker(on_result=on_upload_result)
    page.overlay.append(file_picker)

    def send_message(e):
        if not chat_input.value:
            return
        
        user_msg = chat_input.value
        chat_history.controls.append(
            ft.Container(
                content=ft.Text(f"You: {user_msg}", color="white"),
                bgcolor="#343541",
                padding=10,
                border_radius=10,
                alignment=ft.alignment.center_right
            )
        )
        chat_input.value = ""
        page.update()

        # Get AI Response
        response = engine.query(user_msg)
        chat_history.controls.append(
            ft.Container(
                content=ft.Text(f"FinLegal AI: {response}", color="white"),
                bgcolor="#444654",
                padding=10,
                border_radius=10,
                alignment=ft.alignment.center_left
            )
        )
        page.update()

    chat_input = ft.TextField(
        hint_text="Ask anything about your documents...",
        expand=True,
        border_color="#565869",
        on_submit=send_message
    )

    # Sidebar
    sidebar = ft.Container(
        content=ft.Column([
            ft.Text("FinLegal-Chat", size=24, weight="bold", color="blue"),
            ft.Divider(),
            api_key_input,
            ft.ElevatedButton("Save Key", on_click=save_api_key, icon=ft.icons.SAVE),
            ft.Divider(),
            ft.ElevatedButton(
                "Upload Documents",
                icon=ft.icons.UPLOAD_FILE,
                on_click=lambda _: file_picker.pick_files(allow_multiple=True)
            ),
            ft.Text("Analyzed Documents:", size=14, weight="bold"),
            uploaded_files_list,
            ft.Spacer(),
            ft.TextButton("Reset Session", icon=ft.icons.REFRESH, on_click=lambda _: engine.reset() or uploaded_files_list.controls.clear() or chat_history.controls.clear() or page.update())
        ], spacing=20),
        width=250,
        bgcolor="#202123",
        padding=20
    )

    # Main Chat Area
    chat_area = ft.Container(
        content=ft.Column([
            ft.Container(content=chat_history, expand=True, padding=20),
            ft.Container(
                content=ft.Row([
                    chat_input,
                    ft.IconButton(ft.icons.SEND, on_click=send_message, icon_color="blue")
                ]),
                padding=20,
                bgcolor="#343541"
            )
        ]),
        expand=True,
        bgcolor="#343541"
    )

    page.add(
        ft.Row([
            sidebar,
            chat_area
        ], expand=True)
    )

if __name__ == "__main__":
    ft.app(target=main)
