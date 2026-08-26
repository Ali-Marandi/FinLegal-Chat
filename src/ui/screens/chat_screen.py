/*
* FinLegal-Chat Ultimate - Main Chat Screen
* The primary interaction surface with professional messaging UI.
*/

import os
import shutil
import flet as ft
from typing import Optional, Callable, Dict, List, Any
from src.ui.theme import Brand, Styles
from src.ui.components import (
    ChatBubble,
    GoldDivider,
    AgentStepIndicator,
    EmptyState,
    ProgressBar,
    DocumentListItem,
)


class ChatScreen:
    """Professional chat interface with markdown rendering, agent pipeline visualization,
    document upload, and inline charts."""

    def __init__(
        self,
        page: ft.Page,
        on_send_message: Callable,
        on_upload_file: Callable,
        on_toggle_right_panel: Callable = None,
    ):
        self.page = page
        self.on_send = on_send_message
        self.on_upload = on_upload_file
        self.on_toggle_right = on_toggle_right_panel
        self.messages: List[ft.Control] = []
        self._current_progress: Optional[ProgressBar] = None
        self._agent_steps: Optional[AgentStepIndicator] = None

        self._build_ui()

    def _build_ui(self):
        # --- Header Bar ---
        self.header = ft.Container(
            content=ft.Row(
                [
                    ft.Text(
                        "FinLegal-Chat Ultimate",
                        size=16,
                        weight="bold",
                        color=Brand.TEXT_PRIMARY,
                    ),
                    ft.Container(width=8),
                    StatusBadge(
                        "AI Engine Ready", color=Brand.SUCCESS, size=9
                    ) if hasattr(self, 'status_badge') else ft.Text(
                        "AI Engine Ready",
                        size=11,
                        color=Brand.SUCCESS,
                    ),
                    ft.VerticalDivider(width=1, color=Brand.DIVIDER, opacity=0.5),
                    ft.Text(
                        "v5.0.0",
                        size=11,
                        color=Brand.TEXT_MUTED,
                    ),
                    ft.Spacer(),
                    ft.IconButton(
                        icon=ft.icons.PANELSIDEBAR_CLOSE_ROUNDED
                        if hasattr(self, '_right_panel_visible')
                        else ft.icons.PANELSIDEBAR_RIGHT_ROUNDED,
                        icon_size=20,
                        icon_color=Brand.TEXT_SECONDARY,
                        tooltip="Toggle Panel",
                        on_click=lambda _: self.on_toggle_right() if self.on_toggle_right else None,
                    ),
                ],
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            padding=ft.padding.symmetric(20, 16),
            bgcolor=Brand.NAVY_800,
            border=ft.border.only(bottom=ft.BorderSide(1, Brand.DIVIDER)),
        )

        # --- Chat Messages Area ---
        self.chat_column = ft.Column(
            expand=True,
            scroll=ft.ScrollMode.ADAPTIVE,
            spacing=6,
            padding=ft.padding.symmetric(20, 24),
            auto_scroll=True,
        )

        # --- Empty State ---
        self.empty_state = EmptyState(
            icon=ft.icons.AUTO_AWESOME_MOTION_ROUNDED,
            title="Welcome to FinLegal-Chat Ultimate",
            subtitle="Upload documents and ask your legal, financial, or market questions.\n"
            "The multi-agent AI system will analyze them comprehensively.",
        )

        # --- Progress Bar ---
        self.progress_bar = ProgressBar()

        # --- Agent Steps ---
        self.agent_steps_widget = AgentStepIndicator([])
        self.agent_steps_widget.visible = False

        # --- Input Area ---
        self.chat_input = ft.TextField(
            hint_text="Ask about legal, financial, or market analysis...",
            expand=True,
            **Styles.chat_input_field(),
            on_submit=self._handle_send,
        )

        self.send_button = ft.Container(
            content=ft.Icon(
                ft.icons.SEND_ROUNDED,
                size=22,
                color=Brand.NAVY_900,
            ),
            width=44,
            height=44,
            bgcolor=Brand.GOLD_500,
            border_radius=22,
            alignment=ft.alignment.center,
            on_click=self._handle_send,
            tooltip="Send (Enter)",
        )

        self.upload_button = ft.IconButton(
            icon=ft.icons.ATTACH_FILE_ROUNDED,
            icon_size=22,
            icon_color=Brand.TEXT_SECONDARY,
            tooltip="Upload Document",
            on_click=lambda _: self._pick_files(),
        )

        self.input_area = ft.Container(
            content=ft.Row(
                [
                    self.upload_button,
                    self.chat_input,
                    self.send_button,
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                spacing=8,
            ),
            padding=ft.padding.symmetric(16, 20),
            bgcolor=Brand.NAVY_800,
            border=ft.border.only(top=ft.BorderSide(1, Brand.DIVIDER)),
        )

        # --- File Picker ---
        self.file_picker = ft.FilePicker(
            on_result=self._on_file_picked,
            allowed_extensions=["pdf", "docx", "doc", "txt", "md", "csv"],
        )
        self.page.overlay.append(self.file_picker)

        # --- Main Layout ---
        self.view = ft.Column(
            [
                self.header,
                ft.Container(
                    content=ft.Column(
                        [
                            self.empty_state,
                            self.chat_column,
                        ],
                        expand=True,
                    ),
                    expand=True,
                ),
                self.progress_bar,
                self.agent_steps_widget,
                self.input_area,
            ],
            expand=True,
            spacing=0,
        )

    def _pick_files(self):
        self.file_picker.pick_files(allow_multiple=True)

    def _on_file_picked(self, e: ft.FilePickerResultEvent):
        if e.files:
            for f in e.files:
                self.on_upload(f)

    def _handle_send(self, e=None):
        text = self.chat_input.value
        if not text or not text.strip():
            return
        self.chat_input.value = ""
        self.chat_input.update()
        self.on_send(text.strip())

    # --- Public API ---

    def set_status(self, text: str, color: str = Brand.SUCCESS):
        """Update the status badge in the header."""
        # Rebuild header status
        self.header.content.controls[1] = ft.Text(
            text, size=11, color=color
        )
        self.header.update()

    def show_empty_state(self, show: bool = True):
        self.empty_state.visible = show
        self.empty_state.update()

    def show_progress(self, label: str, value: float):
        self.progress_bar.update_progress(label, value)

    def hide_progress(self):
        self.progress_bar.hide()

    def show_agent_steps(self, completed: List[str]):
        self.agent_steps_widget = AgentStepIndicator(completed)
        self.agent_steps_widget.visible = True
        # We need to replace in parent
        parent = self.view.controls[1].content
        if len(parent.controls) < 3:
            parent.controls.append(self.agent_steps_widget)
        else:
            parent.controls[2] = self.agent_steps_widget
        parent.update()

    def hide_agent_steps(self):
        self.agent_steps_widget.visible = False
        self.agent_steps_widget.update()

    def add_user_message(self, text: str, timestamp: str = ""):
        """Add a user message bubble to the chat."""
        self.show_empty_state(False)
        bubble = ChatBubble(
            content=ft.Text(
                text,
                color=Brand.NAVY_900,
                weight="w600",
                size=14,
                selectable=True,
            ),
            is_user=True,
            timestamp=timestamp,
        )
        self.chat_column.controls.append(bubble)
        self.page.update()

    def add_assistant_message(self, content: str, chart_data: Dict = None, timestamp: str = ""):
        """Add an AI response with optional chart to the chat."""
        self.show_empty_state(False)
        inner = ft.Column(spacing=10, expand=True)

        # Main content as Markdown
        inner.controls.append(
            ft.Markdown(
                content,
                selectable=True,
                extension_set="gitHubWeb",
                markdown_style_sheet=ft.MarkdownStyleSheet(
                    h1=ft.TextStyle(size=20, weight="bold", color=Brand.GOLD_400),
                    h2=ft.TextStyle(size=17, weight="bold", color=Brand.GOLD_300),
                    h3=ft.TextStyle(size=15, weight="bold", color=Brand.TEXT_PRIMARY),
                    p=ft.TextStyle(size=14, color=Brand.TEXT_PRIMARY, height=1.6),
                    code=ft.TextStyle(
                        size=13, font_family="Consolas", color=Brand.GOLD_300
                    ),
                    a=ft.TextStyle(color=Brand.GOLD_500, decoration=ft.TextDecoration.UNDERLINE),
                ),
            )
        )

        # Chart
        if chart_data:
            inner.controls.append(GoldDivider())
            inner.controls.append(self._create_chart_widget(chart_data))

        bubble = ChatBubble(content=inner, is_user=False, timestamp=timestamp)
        self.chat_column.controls.append(bubble)
        self.page.update()

    def _create_chart_widget(self, chart_data: Dict) -> ft.Control:
        """Create a simple text-based chart visualization."""
        chart_type = chart_data.get("type", "bar")
        labels = chart_data.get("labels", [])
        values = chart_data.get("values", [])
        title = chart_data.get("title", "Data Visualization")

        if not labels or not values:
            return ft.Container()

        # Build a visual bar chart using containers
        max_val = max(values) if values else 1
        if max_val == 0:
            max_val = 1

        bars = []
        for label, val in zip(labels, values):
            pct = (val / max_val) * 100
            bars.append(
                ft.Column(
                    [
                        ft.Text(
                            f"{val}",
                            size=10,
                            color=Brand.GOLD_400,
                            weight="bold",
                            text_align=ft.TextAlign.RIGHT,
                        ),
                        ft.Container(
                            height=16,
                            width=pct * 2.5,
                            bgcolor=Brand.GOLD_500,
                            border_radius=4,
                            alignment=ft.alignment.center_left,
                        ),
                        ft.Text(
                            str(label)[:15],
                            size=9,
                            color=Brand.TEXT_MUTED,
                            max_lines=1,
                            overflow=ft.TextOverflow.ELLIPSIS,
                            text_align=ft.TextAlign.CENTER,
                        ),
                    ],
                    spacing=2,
                    horizontal_alignment=ft.CrossAxisAlignment.END,
                    alignment=ft.MainAxisAlignment.END,
                )
            )

        return ft.Container(
            content=ft.Column(
                [
                    ft.Text(
                        title,
                        size=13,
                        weight="bold",
                        color=Brand.TEXT_SECONDARY,
                    ),
                    ft.Column(bars, spacing=8, scroll=ft.ScrollMode.AUTO),
                ],
                spacing=10,
            ),
            padding=12,
            bgcolor=ft.colors.with_opacity(0.05, Brand.NAVY_600),
            border_radius=10,
        )

    def add_error_message(self, text: str):
        """Show an error in the chat."""
        self.show_empty_state(False)
        bubble = ft.Container(
            content=ft.Row(
                [
                    ft.Icon(ft.icons.ERROR_OUTLINE_ROUNDED, color=Brand.ERROR, size=20),
                    ft.Text(text, size=13, color=Brand.ERROR),
                ],
                spacing=10,
            ),
            padding=14,
            bgcolor=ft.colors.with_opacity(0.1, Brand.ERROR),
            border_radius=12,
            border=ft.border.all(1, ft.colors.with_opacity(0.3, Brand.ERROR)),
            margin=ft.margin.only(right=60, bottom=4),
        )
        self.chat_column.controls.append(bubble)
        self.page.update()

    def clear_messages(self):
        self.chat_column.controls.clear()
        self.show_empty_state(True)
        self.page.update()

    def focus_input(self):
        self.chat_input.focus()
        self.page.update()

    @property
    def view(self):
        return self._view

    @view.setter
    def view(self, val):
        self._view = val


# Fix circular import for StatusBadge
from src.ui.components import StatusBadge
