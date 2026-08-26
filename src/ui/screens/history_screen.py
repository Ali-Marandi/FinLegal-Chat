/*
* FinLegal-Chat Ultimate - History Screen
* Browse and manage past chat sessions.
*/

import flet as ft
from typing import Callable, List, Dict, Optional
from src.ui.theme import Brand, Styles
from src.ui.components import (
    SectionLabel,
    GoldDivider,
    EmptyState,
    SessionListItem,
)


class HistoryScreen:
    """Chat history browser with search, pin, and delete."""

    def __init__(
        self,
        page: ft.Page,
        on_select_session: Callable = None,
        on_delete_session: Callable = None,
        on_pin_session: Callable = None,
        on_new_chat: Callable = None,
    ):
        self.page = page
        self.on_select = on_select_session
        self.on_delete = on_delete_session
        self.on_pin = on_pin_session
        self.on_new = on_new_chat

        self.sessions_list = ft.Column(spacing=6)
        self.empty_state = EmptyState(
            icon=ft.icons.HISTORY_ROUNDED,
            title="No chat history",
            subtitle="Your conversations will appear here",
        )

        self.search_field = ft.TextField(
            hint_text="Search conversations...",
            prefix_icon=ft.icons.SEARCH_ROUNDED,
            on_change=self._on_search,
            width=300,
            **Styles.input_field(),
        )

        self._build_ui()

    def _build_ui(self):
        self.view = ft.Column(
            [
                # Header
                ft.Container(
                    content=ft.Row([
                        ft.Icon(ft.icons.HISTORY_ROUNDED, color=Brand.GOLD_500, size=24),
                        ft.Text("Chat History", size=20, weight="bold", color=Brand.TEXT_PRIMARY),
                        ft.Spacer(),
                        ft.ElevatedButton(
                            "New Chat",
                            icon=ft.icons.ADD_ROUNDED,
                            on_click=lambda _: self.on_new() if self.on_new else None,
                            **Styles.gold_button(),
                        ),
                    ], spacing=12),
                    padding=ft.padding.symmetric(20, 24),
                    border=ft.border.only(bottom=ft.BorderSide(1, Brand.DIVIDER)),
                ),
                # Search
                ft.Container(
                    content=self.search_field,
                    padding=ft.padding.only(16, 24, 8),
                ),
                # Sessions list
                ft.Container(
                    content=ft.Column([
                        self.sessions_list,
                        self.empty_state,
                    ], expand=True),
                    expand=True,
                    padding=ft.padding.symmetric(0, 24),
                ),
            ],
            expand=True,
            spacing=0,
        )

    def _on_search(self, e):
        # Trigger search externally via callback if needed
        pass

    def refresh_sessions(self, sessions: List[Dict], active_session_id: str = None):
        self.sessions_list.controls.clear()
        if not sessions:
            self.empty_state.visible = True
        else:
            self.empty_state.visible = False
            for s in sessions:
                sid = s.get("id", "")
                title = s.get("title", "Untitled")
                updated = s.get("updated_at", "")
                # Format time
                time_str = self._format_time(updated)
                is_active = sid == active_session_id
                is_pinned = bool(s.get("is_pinned", 0))

                self.sessions_list.controls.append(
                    SessionListItem(
                        title=title,
                        time_str=time_str,
                        is_active=is_active,
                        is_pinned=is_pinned,
                        on_click=lambda s=s: self.on_select(s) if self.on_select else None,
                        on_delete=lambda s=s: self.on_delete(s) if self.on_delete else None,
                        on_pin=lambda s=s: self.on_pin(s) if self.on_pin else None,
                    )
                )
        self.page.update()

    @staticmethod
    def _format_time(iso_str: str) -> str:
        if not iso_str:
            return ""
        try:
            from datetime import datetime
            dt = datetime.fromisoformat(iso_str)
            now = datetime.now()
            diff = now - dt
            if diff.days == 0:
                return dt.strftime("%H:%M")
            elif diff.days == 1:
                return "Yesterday"
            elif diff.days < 7:
                return dt.strftime("%A")
            else:
                return dt.strftime("%b %d")
        except Exception:
            return iso_str[:10]
