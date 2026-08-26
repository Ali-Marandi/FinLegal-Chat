    """
    FinLegal-Chat Ultimate - Professional Theme System
    A luxurious dark theme inspired by premium fintech applications.
    """

    import flet as ft


    # === Brand Colors ===
    class Brand:
        """Core brand color palette."""
        GOLD_50 = "#FFF9E6"
        GOLD_100 = "#FFF0BF"
        GOLD_200 = "#FFE699"
        GOLD_300 = "#FFD966"
        GOLD_400 = "#F0C75E"
        GOLD_500 = "#D4A843"
        GOLD_600 = "#B8892E"
        GOLD_700 = "#8B6914"

        NAVY_900 = "#050816"
        NAVY_800 = "#0A0E27"
        NAVY_700 = "#0F1535"
        NAVY_600 = "#12183B"
        NAVY_500 = "#1A2147"
        NAVY_400 = "#242E5A"

        SURFACE_DARK = "#0B0F1A"
        SURFACE_CARD = "#111827"
        SURFACE_ELEVATED = "#1F2937"
        SURFACE_HOVER = "#374151"

        TEXT_PRIMARY = "#F9FAFB"
        TEXT_SECONDARY = "#9CA3AF"
        TEXT_MUTED = "#6B7280"
        TEXT_DARK = "#1F2937"

        SUCCESS = "#10B981"
        WARNING = "#F59E0B"
        ERROR = "#EF4444"
        INFO = "#3B82F6"

        DIVIDER = "#1F2937"
        BORDER = "#374151"


    def get_dark_theme() -> ft.Theme:
        """Build the professional dark theme for Flet."""
        theme = ft.Theme(
            color_scheme_seed=Brand.GOLD_500,
            color_scheme=ft.ColorScheme(
                primary=Brand.GOLD_500,
                on_primary=Brand.NAVY_900,
                primary_container=Brand.NAVY_600,
                on_primary_container=Brand.GOLD_300,
                secondary=Brand.NAVY_400,
                on_secondary=Brand.TEXT_PRIMARY,
                surface=Brand.SURFACE_DARK,
                on_surface=Brand.TEXT_PRIMARY,
                surface_variant=Brand.SURFACE_CARD,
                error=Brand.ERROR,
                on_error=Brand.TEXT_PRIMARY,
            ),
            font_family="Segoe UI",
        )
        return theme


    # === Reusable Styles ===
    class Styles:
        """Pre-built style dictionaries for common UI patterns."""

        @staticmethod
        def sidebar_container() -> dict:
            return {
                "bgcolor": Brand.NAVY_800,
                "border": ft.border.only(right=ft.BorderSide(1, Brand.DIVIDER)),
            }

        @staticmethod
        def card_container() -> dict:
            return {
                "bgcolor": Brand.SURFACE_CARD,
                "border_radius": 12,
                "border": ft.border.all(1, Brand.BORDER),
                "padding": 16,
            }

        @staticmethod
        def gold_button() -> dict:
            return {
                "bgcolor": Brand.GOLD_500,
                "color": Brand.NAVY_900,
                "shape": ft.RoundedRectangleBorder(radius=10),
                "style": ft.ButtonStyle(
                    bgcolor={ft.ControlState.HOVERED: Brand.GOLD_400},
                    padding=12,
                ),
            }

        @staticmethod
        def ghost_button() -> dict:
            return {
                "color": Brand.TEXT_SECONDARY,
                "style": ft.ButtonStyle(
                    bgcolor={ft.ControlState.HOVERED: Brand.SURFACE_HOVER},
                    padding=10,
                ),
            }

        @staticmethod
        def input_field() -> dict:
            return {
                "border_color": Brand.BORDER,
                "border_radius": 10,
                "bgcolor": Brand.SURFACE_CARD,
                "text_style": ft.TextStyle(color=Brand.TEXT_PRIMARY, size=14),
                "hint_text_style": ft.TextStyle(color=Brand.TEXT_MUTED),
                "focused_border_color": Brand.GOLD_500,
                "cursor_color": Brand.GOLD_500,
                "content_padding": ft.padding.symmetric(16, 12),
            }

        @staticmethod
        def section_title() -> dict:
            return {
                "size": 11,
                "weight": "bold",
                "color": Brand.TEXT_MUTED,
                "letter_spacing": 1.5,
            }

        @staticmethod
        def chat_input_field() -> dict:
            return {
                "border_color": Brand.BORDER,
                "border_radius": 24,
                "bgcolor": Brand.SURFACE_CARD,
                "text_style": ft.TextStyle(color=Brand.TEXT_PRIMARY, size=14),
                "hint_text_style": ft.TextStyle(color=Brand.TEXT_MUTED),
                "focused_border_color": Brand.GOLD_500,
                "cursor_color": Brand.GOLD_500,
                "content_padding": ft.padding.symmetric(20, 16),
                "multiline": True,
                "min_lines": 1,
                "max_lines": 6,
            }
