import flet as ft
import os
import shutil
import plotly.graph_objects as go
from flet.plotly_chart import PlotlyChart
from src.engine import FinLegalEngine

def main(page: ft.Page):
    page.title = "FinLegal-Chat Pro | Agentic AI Assistant"
    page.theme_mode = ft.ThemeMode.DARK
    page.window_width = 1200
    page.window_height = 900
    page.padding = 0
    page.spacing = 0
    page.fonts = {
        "Inter": "https://github.com/google/fonts/raw/main/ofl/inter/Inter%5Bslnt%2Cwght%5D.ttf"
    }
    page.theme = ft.Theme(font_family="Inter")

    engine = FinLegalEngine()
    
    # UI State
    chat_history = ft.Column(expand=True, scroll=ft.ScrollMode.ALWAYS, spacing=15)
    
    def toggle_mode(e):
        nonlocal engine
        mode = "local" if e.control.value else "openai"
        engine = FinLegalEngine(mode=mode)
        page.show_snack_bar(ft.SnackBar(ft.Text(f"Switched to {mode.upper()} mode")))
        page.update()

    mode_switch = ft.Switch(label="Local Privacy Mode (Ollama)", value=False, on_change=toggle_mode)
    uploaded_files_list = ft.Column(spacing=10)
    
    api_key_input = ft.TextField(
        label="OpenAI API Key",
        password=True,
        can_reveal_password=True,
        width=250,
        border_radius=10,
        text_size=12
    )
    
    def save_api_key(e):
        if api_key_input.value:
            os.environ["OPENAI_API_KEY"] = api_key_input.value
            page.show_snack_bar(ft.SnackBar(ft.Text("✅ API Key configured successfully!"), bgcolor="green"))
            page.update()

    def create_chart(chart_data):
        if not chart_data:
            return None
        
        fig = go.Figure()
        if chart_data["type"] == "bar":
            fig.add_trace(go.Bar(x=chart_data["labels"], y=chart_data["values"], marker_color='rgb(55, 83, 109)'))
        else:
            fig.add_trace(go.Scatter(x=chart_data["labels"], y=chart_data["values"], mode='lines+markers', line=dict(color='rgb(55, 83, 109)', width=3)))
            
        fig.update_layout(
            title=chart_data.get("title", "Data Analysis"),
            template="plotly_dark",
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            margin=dict(l=20, r=20, t=40, b=20),
            height=300
        )
        return PlotlyChart(fig, expand=True)

    def on_upload_result(e: ft.FilePickerResultEvent):
        if e.files:
            for f in e.files:
                dest_path = os.path.join("uploads", f.name)
                os.makedirs("uploads", exist_ok=True)
                shutil.copy(f.path, dest_path)
                
                try:
                    engine.ingest_document(dest_path)
                    uploaded_files_list.controls.append(
                        ft.Container(
                            content=ft.Row([
                                ft.Icon(ft.icons.DESCRIPTION_ROUNDED, color=ft.colors.BLUE_400),
                                ft.Text(f.name, size=13, weight="w500")
                            ]),
                            padding=10,
                            border=ft.border.all(1, ft.colors.WHITE24),
                            border_radius=8
                        )
                    )
                    page.show_snack_bar(ft.SnackBar(ft.Text(f"Successfully indexed: {f.name}")))
                except Exception as ex:
                    page.show_snack_bar(ft.SnackBar(ft.Text(f"Indexing Error: {str(ex)}"), bgcolor="red"))
            page.update()

    file_picker = ft.FilePicker(on_result=on_upload_result)
    page.overlay.append(file_picker)

    def send_message(e):
        if not chat_input.value:
            return
        
        user_msg = chat_input.value
        chat_history.controls.append(
            ft.Row([
                ft.Container(
                    content=ft.Text(user_msg, color="white"),
                    bgcolor=ft.colors.BLUE_700,
                    padding=15,
                    border_radius=ft.border_radius.only(top_left=15, top_right=15, bottom_left=15),
                    max_width=600
                )
            ], alignment=ft.MainAxisAlignment.END)
        )
        chat_input.value = ""
        loading_indicator.visible = True
        page.update()

        # Get AI Response
        try:
            result = engine.query(user_msg)
            answer = result["answer"]
            chart_data = result["chart"]

            msg_content = ft.Column([
                ft.Text(answer, color="white", selectable=True)
            ])
            
            if chart_data:
                chart_widget = create_chart(chart_data)
                if chart_widget:
                    msg_content.controls.append(ft.Divider())
                    msg_content.controls.append(chart_widget)

            chat_history.controls.append(
                ft.Row([
                    ft.Container(
                        content=msg_content,
                        bgcolor="#2D2D39",
                        padding=15,
                        border_radius=ft.border_radius.only(top_left=15, top_right=15, bottom_right=15),
                        max_width=700
                    )
                ], alignment=ft.MainAxisAlignment.START)
            )
        except Exception as ex:
            chat_history.controls.append(ft.Text(f"Error: {str(ex)}", color="red"))
        
        loading_indicator.visible = False
        page.update()

    chat_input = ft.TextField(
        hint_text="Ask a complex legal or financial question...",
        expand=True,
        border_radius=25,
        border_color=ft.colors.WHITE24,
        content_padding=20,
        on_submit=send_message
    )
    
    loading_indicator = ft.ProgressBar(visible=False, color="blue")

    # Sidebar
    sidebar = ft.Container(
        content=ft.Column([
            ft.Row([
                ft.Icon(ft.icons.ACCOUNT_BALANCE_WALLET, color="blue", size=30),
                ft.Text("FinLegal Pro", size=22, weight="bold")
            ]),
            ft.Divider(height=40, color="white10"),
            ft.Text("CONFIGURATION", size=12, weight="bold", color="white38"),
            mode_switch,
            api_key_input,
            ft.ElevatedButton(
                "Configure Key", 
                on_click=save_api_key, 
                icon=ft.icons.KEY_ROUNDED,
                style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10))
            ),
            ft.Divider(height=40, color="white10"),
            ft.Text("DOCUMENT HUB", size=12, weight="bold", color="white38"),
            ft.ElevatedButton(
                "Upload & Index",
                icon=ft.icons.ADD_BOX_ROUNDED,
                on_click=lambda _: file_picker.pick_files(allow_multiple=True),
                style=ft.ButtonStyle(bgcolor=ft.colors.BLUE_800, color="white", shape=ft.RoundedRectangleBorder(radius=10))
            ),
            ft.Container(content=uploaded_files_list, margin=ft.margin.only(top=10)),
            ft.Spacer(),
            ft.TextButton(
                "Clear Session", 
                icon=ft.icons.DELETE_SWEEP_ROUNDED, 
                on_click=lambda _: engine.reset() or uploaded_files_list.controls.clear() or chat_history.controls.clear() or page.update(),
                style=ft.ButtonStyle(color=ft.colors.RED_400)
            )
        ], spacing=15),
        width=300,
        bgcolor="#1A1B23",
        padding=25
    )

    # Main Chat Area
    chat_area = ft.Container(
        content=ft.Column([
            ft.Container(
                content=ft.Column([
                    ft.Text("Agentic Analysis Environment", size=14, color="white38"),
                    loading_indicator
                ]),
                padding=ft.padding.only(left=20, right=20, top=10)
            ),
            ft.Container(content=chat_history, expand=True, padding=20),
            ft.Container(
                content=ft.Row([
                    chat_input,
                    ft.IconButton(
                        ft.icons.SEND_ROUNDED, 
                        on_click=send_message, 
                        icon_color="blue",
                        icon_size=30
                    )
                ]),
                padding=25,
                bgcolor="#1A1B23"
            )
        ]),
        expand=True,
        bgcolor="#13141A"
    )

    page.add(
        ft.Row([
            sidebar,
            chat_area
        ], expand=True)
    )

if __name__ == "__main__":
    ft.app(target=main)
