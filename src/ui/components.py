"""
FinLegal-Chat Ultimate - Reusable UI Components
Professional, animated, and polished building blocks.
"""

import os
import time
import flet as ft
from typing import Optional, Callable, List, Any
from src.ui.theme import Brand, Styles


class AnimatedContainer(ft.Container):
    """Container with smooth hover/click animation support."""

    def __init__(self, on_click=None, hover_scale=1.01, **kwargs):
        super().__init__(**kwargs)
        self._on_click = on_click
        self._hover_scale = hover_scale
        self.on_hover = self._handle_hover
        if on_click:
            self.on_click = on_click
            self.mouse_cursor = ft.MouseCursor.CLICK

    def _handle_hover(self, e: ft.HoverEvent):
        if e.data == "true":
            self.scale = self._hover_scale
            self.shadow = ft.BoxShadow(blur_radius=8, color=ft.colors.with_opacity(0.15, "#000000"))
        else:
            self.scale = 1.0
            self.shadow = None
        self.update()


class GlassCard(ft.Container):
    """Frosted glass card effect."""

    def __init__(self, content=None, padding=16, border_radius=12, **kwargs):
        super().__init__(
            content=content,
            padding=padding,
            border_radius=border_radius,
            bgcolor=ft.colors.with_opacity(0.6, Brand.SURFACE_CARD),
            border=ft.border.all(1, ft.colors.with_opacity(0.15, Brand.GOLD_500)),
            blur=20,
            **kwargs,
        )


class GoldDivider(ft.Container):
    """A thin gold-accented divider line."""

    def __init__(self, height: int = 1, margin=None):
        super().__init__(
            height=height,
            bgcolor=Brand.GOLD_700,
            opacity=0.3,
            margin=margin or ft.margin.symmetric(vertical=8),
        )


class SectionLabel(ft.Text):
    """Uppercase section label with letter spacing."""

    def __init__(self, text: str, **kwargs):
        super().__init__(
            text,
            size=11,
            weight="bold",
            color=Brand.TEXT_MUTED,
            letter_spacing=1.5,
            **kwargs,
        )


class ChatBubble(ft.Container):
    """A styled chat message bubble."""

    def __init__(
        self,
        content: ft.Control,
        is_user: bool = False,
        timestamp: str = "",
    ):
        if is_user:
            super().__init__(
                content=content,
                bgcolor=Brand.GOLD_500,
                padding=ft.padding.symmetric(14, 18),
                border_radius=ft.border_radius.only(
                    top_left=18, top_right=18, bottom_left=18
                ),
                margin=ft.margin.only(left=60, bottom=4),
            )
        else:
            super().__init__(
                content=content,
                bgcolor=Brand.SURFACE_CARD,
                padding=ft.padding.symmetric(14, 18),
                border_radius=ft.border_radius.only(
                    top_left=18, top_right=18, bottom_right=18
                ),
                border=ft.border.all(1, Brand.BORDER),
                margin=ft.margin.only(right=60, bottom=4),
            )


class StatusBadge(ft.Container):
    """Colored status indicator badge."""

    def __init__(self, text: str, color: str = Brand.SUCCESS, size: int = 9):
        super().__init__(
            content=ft.Row(
                [
                    ft.Container(
                        width=7, height=7, border_radius=10, bgcolor=color
                    ),
                    ft.Text(text, size=size, color=Brand.TEXT_SECONDARY),
                ],
                spacing=6,
                alignment=ft.MainAxisAlignment.START,
            ),
            padding=ft.padding.symmetric(6, 10),
            border_radius=20,
            bgcolor=ft.colors.with_opacity(0.1, color),
        )


class AgentStepIndicator(ft.Container):
    """Shows which agents have completed in the pipeline."""

    AGENTS = [
        ("Retrieve", ft.icons.SEARCH_ROUNDED),
        ("Legal", ft.icons.GAVEL_ROUNDED),
        ("Financial", ft.icons.ATTACH_MONEY_ROUNDED),
        ("Market", ft.icons.PUBLIC_ROUNDED),
        ("Risk", ft.icons.SHIELD_ROUNDED),
        ("Synthesis", ft.icons.AUTO_AWESOME_ROUNDED),
    ]

    def __init__(self, completed_agents: List[str] = None):
        completed = set(completed_agents or [])
        steps = []
        for name, icon in self.AGENTS:
            is_done = name.lower() in completed
            steps.append(
                ft.Container(
                    content=ft.Column(
                        [
                            ft.Icon(
                                icon,
                                size=18,
                                color=Brand.GOLD_500 if is_done else Brand.TEXT_MUTED,
                            ),
                            ft.Text(
                                name,
                                size=8,
                                color=Brand.GOLD_500 if is_done else Brand.TEXT_MUTED,
                                weight="bold",
                            ),
                        ],
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        spacing=2,
                    ),
                    width=48,
                    padding=6,
                    border_radius=8,
                    bgcolor=ft.colors.with_opacity(0.15, Brand.GOLD_500)
                    if is_done
                    else None,
                )
            )
        super().__init__(
            content=ft.Row(steps, alignment=ft.MainAxisAlignment.CENTER, spacing=2),
            padding=8,
            bgcolor=ft.colors.with_opacity(0.05, Brand.NAVY_600),
            border_radius=12,
            border=ft.border.all(1, Brand.DIVIDER),
        )


class EmptyState(ft.Container):
    """Empty state placeholder with icon and message."""

    def __init__(
        self,
        icon: str = ft.icons.CHAT_BUBBLE_OUTLINE_ROUNDED,
        title: str = "No conversations yet",
        subtitle: str = "Start a new chat to begin your analysis",
    ):
        super().__init__(
            content=ft.Column(
                [
                    ft.Icon(icon, size=64, color=Brand.TEXT_MUTED, opacity=0.4),
                    ft.Text(title, size=18, weight="bold", color=Brand.TEXT_SECONDARY),
                    ft.Text(
                        subtitle,
                        size=13,
                        color=Brand.TEXT_MUTED,
                        text_align=ft.TextAlign.CENTER,
                    ),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                alignment=ft.MainAxisAlignment.CENTER,
                spacing=12,
            ),
            expand=True,
            alignment=ft.alignment.center,
        )


class DocumentListItem(ft.Container):
    """A styled document list item with icon and actions."""

    FILE_ICONS = {
        ".pdf": ft.icons.PICTURE_AS_PDF_ROUNDED,
        ".docx": ft.icons.DESCRIPTION_ROUNDED,
        ".doc": ft.icons.DESCRIPTION_ROUNDED,
        ".txt": ft.icons.ARTICLE_ROUNDED,
        ".md": ft.icons.ARTICLE_ROUNDED,
        ".csv": ft.icons.TABLE_CHART_ROUNDED,
    }

    def __init__(
        self,
        filename: str,
        file_size: str = "",
        on_remove: Callable = None,
    ):
        ext = os.path.splitext(filename)[1].lower()
        icon = self.FILE_ICONS.get(ext, ft.icons.INSERT_DRIVE_FILE_ROUNDED)

        super().__init__(
            content=ft.Row(
                [
                    ft.Container(
                        content=ft.Icon(icon, size=20, color=Brand.GOLD_500),
                        padding=8,
                        bgcolor=ft.colors.with_opacity(0.1, Brand.GOLD_500),
                        border_radius=8,
                    ),
                    ft.Column(
                        [
                            ft.Text(
                                filename,
                                size=13,
                                weight="w500",
                                color=Brand.TEXT_PRIMARY,
                                max_lines=1,
                                overflow=ft.TextOverflow.ELLIPSIS,
                            ),
                            ft.Text(file_size, size=11, color=Brand.TEXT_MUTED),
                        ],
                        spacing=2,
                        expand=True,
                    ),
                    ft.IconButton(
                        icon=ft.icons.CLOSE_ROUNDED,
                        icon_size=16,
                        icon_color=Brand.TEXT_MUTED,
                        on_click=on_remove,
                        tooltip="Remove",
                    )
                    if on_remove
                    else ft.Container(),
                ],
                spacing=10,
                alignment=ft.MainAxisAlignment.START,
            ),
            padding=ft.padding.symmetric(8, 12),
            border_radius=8,
            bgcolor=Brand.SURFACE_CARD,
            border=ft.border.all(1, Brand.DIVIDER),
        )


class SessionListItem(AnimatedContainer):
    """A session item in the sidebar history list."""

    def __init__(
        self,
        title: str,
        time_str: str,
        is_active: bool = False,
        is_pinned: bool = False,
        on_click: Callable = None,
        on_delete: Callable = None,
        on_pin: Callable = None,
    ):
        self.title_text = ft.Text(
            title,
            size=13,
            weight="w600" if is_active else "w400",
            color=Brand.GOLD_400 if is_active else Brand.TEXT_PRIMARY,
            max_lines=1,
            overflow=ft.TextOverflow.ELLIPSIS,
        )
        self.time_text = ft.Text(
            time_str, size=11, color=Brand.TEXT_MUTED
        )

        actions = []
        if on_pin:
            actions.append(
                ft.IconButton(
                    icon=ft.icons.PUSH_PIN_ROUNDED
                    if is_pinned
                    else ft.icons.PUSH_PIN_OUTLINED,
                    icon_size=14,
                    icon_color=Brand.GOLD_500 if is_pinned else Brand.TEXT_MUTED,
                    on_click=lambda _: on_pin(),
                    tooltip="Pin",
                )
            )
        if on_delete:
            actions.append(
                ft.IconButton(
                    icon=ft.icons.DELETE_OUTLINE_ROUNDED,
                    icon_size=14,
                    icon_color=Brand.TEXT_MUTED,
                    on_click=lambda _: on_delete(),
                    tooltip="Delete",
                )
            )

        super().__init__(
            content=ft.Column(
                [
                    ft.Row([self.title_text], spacing=0),
                    ft.Row(
                        [self.time_text] + actions,
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    ),
                ],
                spacing=4,
            ),
            padding=ft.padding.symmetric(10, 14),
            border_radius=10,
            bgcolor=ft.colors.with_opacity(0.12, Brand.GOLD_500)
            if is_active
            else ft.colors.TRANSPARENT,
            border=ft.border.all(1, Brand.GOLD_700)
            if is_active
            else ft.border.all(0, ft.colors.TRANSPARENT),
            on_click=on_click,
            hover_scale=1.01,
        )


class ProgressBar(ft.Container):
    """Custom animated progress bar with gold accent."""

    def __init__(self, label: str = "", initial_value: float = 0.0):
        self.label_text = ft.Text(label, size=11, color=Brand.TEXT_SECONDARY)
        self.fill = ft.Container(
            width=0, height=3, bgcolor=Brand.GOLD_500, border_radius=2
        )
        super().__init__(
            content=ft.Column(
                [
                    self.label_text,
                    ft.Container(
                        content=self.fill,
                        bgcolor=ft.colors.with_opacity(0.1, Brand.GOLD_500),
                        border_radius=2,
                        height=3,
                    ),
                ],
                spacing=6,
            ),
            visible=False,
            padding=ft.padding.only(bottom=4),
        )

    def update_progress(self, label: str, value: float):
        self.label_text.text = label
        self.fill.width = max(0, min(1.0, value))
        self.visible = True
        self.update()

    def hide(self):
        self.visible = False
        self.update()
