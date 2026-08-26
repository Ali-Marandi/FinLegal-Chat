/*
* FinLegal-Chat Ultimate - Settings Screen
* Comprehensive settings management with tabs.
*/

import flet as ft
from src.ui.theme import Brand, Styles


class SettingsScreen:
    """Professional settings panel with organized sections."""

    def __init__(
        self,
        page: ft.Page,
        config,
        on_apply_settings: Callable = None,
        on_reset_engine: Callable = None,
    ):
        self.page = page
        self.config = config
        self.on_apply = on_apply_settings
        self.on_reset = on_reset_engine
        self._build_ui()

    def _build_ui(self):
        # === AI ENGINE SECTION ===
        self.mode_switch = ft.Switch(
            label="Local Privacy Mode (Ollama)",
            value=self.config.get("mode") == "local",
            active_color=Brand.GOLD_500,
            on_change=self._on_mode_change,
        )

        self.api_key_field = ft.TextField(
            label="OpenAI API Key",
            password=True,
            can_reveal_password=True,
            value=self.config.get("openai_api_key", ""),
            width=350,
            **Styles.input_field(),
        )

        self.model_field = ft.TextField(
            label="OpenAI Model",
            value=self.config.get("openai_model", "gpt-4o"),
            width=350,
            **Styles.input_field(),
        )

        self.local_url_field = ft.TextField(
            label="Ollama Server URL",
            value=self.config.get("local_url", "http://localhost:11434"),
            width=350,
            **Styles.input_field(),
        )

        self.local_model_field = ft.TextField(
            label="Ollama Model Name",
            value=self.config.get("local_model", "llama3"),
            width=350,
            **Styles.input_field(),
        )

        self.temperature_slider = ft.Slider(
            label="Temperature (Creativity)",
            min=0.0,
            max=1.0,
            divisions=10,
            value=self.config.get("temperature", 0.0),
            active_color=Brand.GOLD_500,
            label_color=Brand.TEXT_SECONDARY,
        )

        # === RETRIEVAL SECTION ===
        self.chunk_size_field = ft.TextField(
            label="Chunk Size",
            value=str(self.config.get("chunk_size", 2000)),
            width=200,
            **Styles.input_field(),
        )

        self.chunk_overlap_field = ft.TextField(
            label="Chunk Overlap",
            value=str(self.config.get("chunk_overlap", 300)),
            width=200,
            **Styles.input_field(),
        )

        self.retrieval_k_field = ft.TextField(
            label="Retrieval Top-K",
            value=str(self.config.get("retrieval_k", 10)),
            width=200,
            **Styles.input_field(),
        )

        # === UI SECTION ===
        self.font_size_slider = ft.Slider(
            label="Font Size",
            min=10,
            max=20,
            divisions=10,
            value=self.config.get("font_size", 14),
            active_color=Brand.GOLD_500,
            label_color=Brand.TEXT_SECONDARY,
        )

        self.timestamps_switch = ft.Switch(
            label="Show Timestamps",
            value=self.config.get("show_timestamps", True),
            active_color=Brand.GOLD_500,
        )

        self.auto_save_switch = ft.Switch(
            label="Auto-save Chat History",
            value=self.config.get("auto_save_chats", True),
            active_color=Brand.GOLD_500,
        )

        self.send_on_enter_switch = ft.Switch(
            label="Send on Enter",
            value=self.config.get("send_on_enter", True),
            active_color=Brand.GOLD_500,
        )

        # === BUILD VIEW ===
        self.view = ft.Column(
            [
                # Header
                ft.Container(
                    content=ft.Row([
                        ft.Icon(ft.icons.SETTINGS_ROUNDED, color=Brand.GOLD_500, size=24),
                        ft.Text("Settings", size=20, weight="bold", color=Brand.TEXT_PRIMARY),
                    ], spacing=12),
                    padding=ft.padding.symmetric(20, 24),
                    border=ft.border.only(bottom=ft.BorderSide(1, Brand.DIVIDER)),
                ),
                # Scrollable settings content
                ft.Column(
                    [
                        self._section("AI ENGINE", [
                            self.mode_switch,
                            ft.Container(height=8),
                            self.api_key_field,
                            self.model_field,
                            GoldDivider(),
                            self.local_url_field,
                            self.local_model_field,
                            GoldDivider(),
                            self.temperature_slider,
                        ]),
                        self._section("RETRIEVAL SETTINGS", [
                            ft.Row([
                                self.chunk_size_field,
                                self.chunk_overlap_field,
                                self.retrieval_k_field,
                            ], spacing=16),
                        ]),
                        self._section("INTERFACE", [
                            self.font_size_slider,
                            self.timestamps_switch,
                            self.auto_save_switch,
                            self.send_on_enter_switch,
                        ]),
                        self._section("ACTIONS", [
                            ft.Row([
                                ft.ElevatedButton(
                                    "Apply Settings",
                                    icon=ft.icons.CHECK_ROUNDED,
                                    on_click=self._apply,
                                    **Styles.gold_button(),
                                ),
                                ft.ElevatedButton(
                                    "Reset Engine",
                                    icon=ft.icons.RESTART_ALT_ROUNDED,
                                    on_click=lambda _: self.on_reset() if self.on_reset else None,
                                    **Styles.ghost_button(),
                                ),
                            ], spacing=12),
                        ]),
                    ],
                    scroll=ft.ScrollMode.ADAPTIVE,
                    expand=True,
                    padding=ft.padding.symmetric(16, 24),
                    spacing=8,
                ),
            ],
            expand=True,
            spacing=0,
        )

    def _section(self, title: str, controls: list) -> ft.Container:
        return ft.Container(
            content=ft.Column(
                [
                    SectionLabel(title),
                    ft.Container(height=8),
                    *controls,
                ],
                spacing=6,
            ),
            padding=16,
            bgcolor=Brand.SURFACE_CARD,
            border_radius=12,
            border=ft.border.all(1, Brand.DIVIDER),
            margin=ft.margin.only(bottom=12),
        )

    def _on_mode_change(self, e):
        is_local = e.control.value
        self.api_key_field.disabled = is_local
        self.model_field.disabled = is_local
        self.local_url_field.disabled = not is_local
        self.local_model_field.disabled = not is_local
        self.page.update()

    def _apply(self, e=None):
        """Gather all settings and call the apply callback."""
        settings = {
            "mode": "local" if self.mode_switch.value else "openai",
            "openai_api_key": self.api_key_field.value or "",
            "openai_model": self.model_field.value or "gpt-4o",
            "local_url": self.local_url_field.value or "http://localhost:11434",
            "local_model": self.local_model_field.value or "llama3",
            "temperature": self.temperature_slider.value,
            "chunk_size": int(self.chunk_size_field.value or 2000),
            "chunk_overlap": int(self.chunk_overlap_field.value or 300),
            "retrieval_k": int(self.retrieval_k_field.value or 10),
            "font_size": int(self.font_size_slider.value),
            "show_timestamps": self.timestamps_switch.value,
            "auto_save_chats": self.auto_save_switch.value,
            "send_on_enter": self.send_on_enter_switch.value,
        }
        if self.on_apply:
            self.on_apply(settings)
        self.page.show_snack_bar(
            ft.SnackBar(
                ft.Text("Settings applied successfully"),
                bgcolor=Brand.SUCCESS,
            )
        )

    def refresh_from_config(self):
        """Reload all fields from config."""
        self.mode_switch.value = self.config.get("mode") == "local"
        self.api_key_field.value = self.config.get("openai_api_key", "")
        self.model_field.value = self.config.get("openai_model", "gpt-4o")
        self.local_url_field.value = self.config.get("local_url", "http://localhost:11434")
        self.local_model_field.value = self.config.get("local_model", "llama3")
        self.temperature_slider.value = self.config.get("temperature", 0.0)
        self.chunk_size_field.value = str(self.config.get("chunk_size", 2000))
        self.chunk_overlap_field.value = str(self.config.get("chunk_overlap", 300))
        self.retrieval_k_field.value = str(self.config.get("retrieval_k", 10))
        self.font_size_slider.value = self.config.get("font_size", 14)
        self.timestamps_switch.value = self.config.get("show_timestamps", True)
        self.auto_save_switch.value = self.config.get("auto_save_chats", True)
        self.send_on_enter_switch.value = self.config.get("send_on_enter", True)
        self._on_mode_change(ft.ControlEvent(data="true" if self.mode_switch.value else "false", page=self.page))
        self.page.update()


from typing import Callable
from src.ui.components import SectionLabel, GoldDivider
from src.ui.theme import Styles
