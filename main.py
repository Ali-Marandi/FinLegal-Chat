import flet as ft
import os
import shutil
import plotly.graph_objects as go
from flet.plotly_chart import PlotlyChart
from src.engine import FinLegalUltimateEngine as FinLegalEngine

DISCLAIMER = (
    "This app is an AI prototype. It is not a lawyer and does not give legal advice. "
    "A licensed lawyer must review every output before you rely on it.\n\n"
    "این خروجی هوش مصنوعی است، مشاوره حقوقی نیست، و باید توسط وکیل دارای پروانه بررسی شود."
)

def main(page: ft.Page):
    page.title = "FinLegal-Chat"
    page.theme_mode = ft.ThemeMode.DARK
    page.window_width = 1500
    page.window_height = 1000
    page.padding = 0
    page.spacing = 0
    page.fonts = {
        "Inter": "https://github.com/google/fonts/raw/main/ofl/inter/Inter%5Bslnt%2Cwght%5D.ttf"
    }
    page.theme = ft.Theme(font_family="Inter")

    engine = FinLegalEngine()

    chat_history = ft.Column(expand=True, scroll=ft.ScrollMode.ALWAYS, spacing=15)
    uploaded_files_list = ft.Column(spacing=10)
    automation_files_list = ft.Column(spacing=10)

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
            page.show_snack_bar(ft.SnackBar(ft.Text("API key saved"), bgcolor="green"))
            page.update()

    def create_chart(chart_data):
        if not chart_data:
            return None
        fig = go.Figure()
        if chart_data["type"] == "bar":
            fig.add_trace(go.Bar(x=chart_data["labels"], y=chart_data["values"], marker_color='rgb(255, 215, 0)'))
        else:
            fig.add_trace(go.Scatter(x=chart_data["labels"], y=chart_data["values"], mode='lines+markers', line=dict(color='rgb(255, 215, 0)', width=3)))
        fig.update_layout(
            title=chart_data.get("title", "Chart"),
            template="plotly_dark",
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            margin=dict(l=20, r=20, t=40, b=20),
            height=350
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
                                ft.Icon(ft.icons.AUTO_AWESOME_MOTION_ROUNDED, color=ft.colors.AMBER_400),
                                ft.Text(f.name, size=13, weight="w500")
                            ]),
                            padding=10,
                            border=ft.border.all(1, ft.colors.AMBER_700),
                            border_radius=8
                        )
                    )
                except Exception as ex:
                    page.show_snack_bar(ft.SnackBar(ft.Text(f"Error: {str(ex)}"), bgcolor="red"))
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
                    content=ft.Text(user_msg, color="black", weight="bold"),
                    bgcolor=ft.colors.AMBER_400,
                    padding=15,
                    border_radius=ft.border_radius.only(top_left=15, top_right=15, bottom_left=15),
                    max_width=600
                )
            ], alignment=ft.MainAxisAlignment.END)
        )
        chat_input.value = ""
        loading_indicator.visible = True
        page.update()

        try:
            result = engine.query(user_msg)
            answer = result["answer"]
            chart_data = result["chart"]
            reports = result.get("reports", {})

            msg_content = ft.Column([
                ft.Markdown(answer, selectable=True, extension_set="gitHubWeb")
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
                        bgcolor="#1E1E2E",
                        padding=20,
                        border_radius=ft.border_radius.only(top_left=15, top_right=15, bottom_right=15),
                        max_width=900,
                        border=ft.border.all(1, ft.colors.WHITE10)
                    )
                ], alignment=ft.MainAxisAlignment.START)
            )

            automation_files_list.controls.clear()
            for fmt, path in reports.items():
                if path:
                    automation_files_list.controls.append(
                        ft.Row([
                            ft.Icon(ft.icons.FILE_DOWNLOAD_ROUNDED, color=ft.colors.GREEN_400),
                            ft.Text(os.path.basename(path), size=12, color="white70")
                        ])
                    )

        except Exception as ex:
            chat_history.controls.append(ft.Text(f"Error: {str(ex)}", color="red"))

        loading_indicator.visible = False
        page.update()

    chat_input = ft.TextField(
        hint_text="Ask about your uploaded documents...",
        expand=True,
        border_radius=30,
        border_color=ft.colors.AMBER_700,
        content_padding=20,
        on_submit=send_message,
        bgcolor="#1E1E2E"
    )

    loading_indicator = ft.ProgressBar(visible=False, color="amber")

    sidebar = ft.Container(
        content=ft.Column([
            ft.Row([
                ft.Icon(ft.icons.DESCRIPTION_ROUNDED, color=ft.colors.AMBER_400, size=40),
                ft.Text("FinLegal-Chat", size=22, weight="bold", color=ft.colors.AMBER_400)
            ]),
            ft.Divider(height=40, color="white10"),
            ft.Text("SETTINGS", size=12, weight="bold", color="white38"),
            ft.Switch(label="Local mode (Ollama)", value=False, on_change=lambda e: engine.__init__(mode="local" if e.control.value else "openai")),
            api_key_input,
            ft.ElevatedButton("Save API key", on_click=save_api_key, icon=ft.icons.SETTINGS_INPUT_COMPONENT_ROUNDED),
            ft.Divider(height=40, color="white10"),
            ft.Text("DOCUMENTS", size=12, weight="bold", color="white38"),
            ft.ElevatedButton(
                "Upload documents",
                icon=ft.icons.CLOUD_UPLOAD_ROUNDED,
                on_click=lambda _: file_picker.pick_files(allow_multiple=True),
                style=ft.ButtonStyle(bgcolor=ft.colors.AMBER_700, color="black", shape=ft.RoundedRectangleBorder(radius=10))
            ),
            ft.Container(content=uploaded_files_list, margin=ft.margin.only(top=10)),
            ft.Divider(height=40, color="white10"),
            ft.Text("EXPORTS", size=12, weight="bold", color="white38"),
            automation_files_list,
            ft.Spacer(),
            ft.TextButton("Reset", icon=ft.icons.RESTART_ALT_ROUNDED, on_click=lambda _: engine.reset() or uploaded_files_list.controls.clear() or chat_history.controls.clear() or automation_files_list.controls.clear() or page.update())
        ], spacing=15),
        width=350,
        bgcolor="#0F0F1A",
        padding=30
    )

    main_area = ft.Container(
        content=ft.Column([
            ft.Container(
                content=ft.Text(DISCLAIMER, size=12, color=ft.colors.AMBER_200),
                padding=ft.padding.only(left=20, right=20, top=15, bottom=10)
            ),
            loading_indicator,
            ft.Container(content=chat_history, expand=True, padding=25),
            ft.Container(
                content=ft.Row([
                    chat_input,
                    ft.IconButton(ft.icons.SEND_ROUNDED, on_click=send_message, icon_color="amber", icon_size=35)
                ]),
                padding=30,
                bgcolor="#0F0F1A"
            )
        ]),
        expand=True,
        bgcolor="#08080F"
    )

    def close_disclaimer(e):
        dialog.open = False
        page.update()

    dialog = ft.AlertDialog(
        modal=True,
        title=ft.Text("Not legal advice"),
        content=ft.Text(DISCLAIMER),
        actions=[ft.TextButton("I understand", on_click=close_disclaimer)],
    )
    page.dialog = dialog
    dialog.open = True

    page.add(ft.Row([sidebar, main_area], expand=True))
    page.update()

if __name__ == "__main__":
    ft.app(target=main)
