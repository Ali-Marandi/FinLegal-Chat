/**
* FinLegal-Chat Ultimate - Main Application Controller
* Orchestrates navigation, engine lifecycle, and cross-screen coordination.
*/

import os
import shutil
import flet as ft
from datetime import datetime
from typing import Optional, Dict, List, Any

from src.config import ConfigManager
from src.database import DatabaseManager
from src.engine import FinLegalUltimateEngine
from src.ui.theme import Brand, Styles, get_dark_theme
from src.ui.components import StatusBadge, DocumentListItem, GoldDivider, SectionLabel
from src.ui.screens.chat_screen import ChatScreen
from src.ui.screens.settings_screen import SettingsScreen
from src.ui.screens.documents_screen import DocumentsScreen
from src.ui.screens.history_screen import HistoryScreen


class FinLegalApp:
    """Main application controller - the heart of FinLegal-Chat Ultimate."""

    def __init__(self, page: ft.Page):
        self.page = page
        self.config = ConfigManager()
        self.db = DatabaseManager(str(self.config.db_path))
        self.engine: Optional[FinLegalUltimateEngine] = None
        self.current_session_id: Optional[str] = None
        self._right_panel_visible = True
        self._uploaded_files: List[Dict] = []  # {filename, file_path, file_size, doc_id}
        self._generated_reports: List[Dict] = []  # {filename, path, created_at}
        self._processing_query = False

        # Initialize the page
        self._init_page()
        # Build the engine
        self._init_engine()
        # Build UI
        self._build_ui()
        # Load state
        self._restore_state()

    def _init_page(self):
        """Configure the Flet page with professional settings."""
        p = self.page
        p.title = "FinLegal-Chat Ultimate | AI-Powered Legal & Financial Intelligence"
        p.theme_mode = ft.ThemeMode.DARK
        p.theme = get_dark_theme()
        p.window_width = self.config.get("window_width", 1500)
        p.window_height = self.config.get("window_height", 950)
        p.window_min_width = 1000
        p.window_min_height = 650
        p.padding = 0
        p.spacing = 0
        p.bgcolor = Brand.SURFACE_DARK
        # Prevent context menu
        p.on_resize = self._on_window_resize

    def _on_window_resize(self, e):
        self.config.set("window_width", self.page.window_width)
        self.config.set("window_height", self.page.window_height)

    def _init_engine(self):
        """Initialize the AI engine based on config."""
        try:
            self.engine = FinLegalUltimateEngine(
                mode=self.config.get("mode", "openai"),
                api_key=self.config.get_api_key(),
                openai_model=self.config.get("openai_model", "gpt-4o"),
                local_url=self.config.get("local_url", "http://localhost:11434"),
                local_model=self.config.get("local_model", "llama3"),
                chunk_size=self.config.get("chunk_size", 2000),
                chunk_overlap=self.config.get("chunk_overlap", 300),
                retrieval_k=self.config.get("retrieval_k", 10),
                temperature=self.config.get("temperature", 0.0),
                on_progress=self._on_engine_progress,
            )
            # If there were API keys set previously, set env var
            if self.config.get_api_key():
                os.environ["OPENAI_API_KEY"] = self.config.get_api_key()
        except ValueError as e:
            self.engine = None
            print(f"Engine init warning: {e}")

    def _build_ui(self):
        """Build the complete application layout."""
        # --- Screens ---
        self.chat_screen = ChatScreen(
            page=self.page,
            on_send_message=self._handle_send_message,
            on_upload_file=self._handle_upload_file,
            on_toggle_right_panel=self._toggle_right_panel,
        )

        self.documents_screen = DocumentsScreen(
            page=self.page,
            on_upload_files=self._handle_upload_file,
            on_remove_document=self._handle_remove_document,
            on_open_file=self._handle_open_file,
        )

        self.history_screen = HistoryScreen(
            page=self.page,
            on_select_session=self._handle_select_session,
            on_delete_session=self._handle_delete_session,
            on_pin_session=self._handle_pin_session,
            on_new_chat=self._handle_new_chat,
        )

        self.settings_screen = SettingsScreen(
            page=self.page,
            config=self.config,
            on_apply_settings=self._handle_apply_settings,
            on_reset_engine=self._handle_reset_engine,
        )

        self._active_screen = "chat"
        self._screen_container = ft.Container(
            content=self.chat_screen.view,
            expand=True,
        )

        # --- Sidebar ---
        self._build_sidebar()

        # --- Right Panel ---
        self._build_right_panel()

        # --- Main Layout ---
        self.main_layout = ft.Row(
            [
                self.sidebar,
                ft.Container(
                    content=self._screen_container,
                    expand=True,
                ),
                self.right_panel,
            ],
            expand=True,
            spacing=0,
        )

        self.page.add(self.main_layout)

    def _build_sidebar(self):
        """Build the left navigation sidebar with session list."""
        # New Chat button
        new_chat_btn = ft.Container(
            content=ft.Row(
                [
                    ft.Icon(ft.icons.ADD_ROUNDED, color=Brand.NAVY_900, size=20),
                    ft.Text("New Chat", size=13, weight="bold", color=Brand.NAVY_900),
                ],
                spacing=8,
                alignment=ft.MainAxisAlignment.CENTER,
            ),
            bgcolor=Brand.GOLD_500,
            padding=ft.padding.symmetric(12, 0),
            border_radius=10,
            on_click=lambda _: self._handle_new_chat(),
        )

        # Session list in sidebar
        self.sidebar_sessions_list = ft.Column(spacing=4, expand=True, scroll=ft.ScrollMode.ADAPTIVE)

        # Nav items
        nav_items = []
        for icon, label, screen_id in [
            (ft.icons.CHAT_ROUNDED, "Chat", "chat"),
            (ft.icons.FOLDER_OPEN_ROUNDED, "Documents", "documents"),
            (ft.icons.HISTORY_ROUNDED, "History", "history"),
            (ft.icons.SETTINGS_ROUNDED, "Settings", "settings"),
        ]:
            nav_items.append(
                ft.Container(
                    content=ft.Row(
                        [
                            ft.Icon(icon, size=18, color=Brand.GOLD_500),
                            ft.Text(label, size=13, color=Brand.TEXT_PRIMARY, weight="w500"),
                        ],
                        spacing=10,
                    ),
                    padding=ft.padding.symmetric(10, 14),
                    border_radius=8,
                    on_click=lambda s=screen_id: self._navigate_to(s),
                )
            )

        # Stats
        self.stats_text = ft.Text(
            "", size=10, color=Brand.TEXT_MUTED
        )

        self.sidebar = ft.Container(
            content=ft.Column(
                [
                    # Brand
                    ft.Container(
                        content=ft.Row(
                            [
                                ft.Container(
                                    content=ft.Icon(
                                        ft.icons.ALL_INCLUSIVE_ROUNDED,
                                        color=Brand.GOLD_500,
                                        size=28,
                                    ),
                                    width=40,
                                    height=40,
                                    bgcolor=ft.colors.with_opacity(0.15, Brand.GOLD_500),
                                    border_radius=10,
                                    alignment=ft.alignment.center,
                                ),
                                ft.Column(
                                    [
                                        ft.Text(
                                            "FinLegal",
                                            size=16,
                                            weight="bold",
                                            color=Brand.GOLD_400,
                                        ),
                                        ft.Text(
                                            "Ultimate AI",
                                            size=11,
                                            color=Brand.TEXT_MUTED,
                                        ),
                                    ],
                                    spacing=0,
                                ),
                            ],
                            spacing=10,
                        ),
                        padding=20,
                    ),
                    GoldDivider(),
                    # New chat button
                    ft.Container(content=new_chat_btn, padding=ft.padding.symmetric(0, 16), margin=ft.margin.only(bottom=8)),
                    # Session list header
                    ft.Container(
                        content=SectionLabel("RECENT CHATS"),
                        padding=ft.padding.only(left=18, right=16, bottom=4),
                    ),
                    # Sessions list
                    ft.Container(
                        content=self.sidebar_sessions_list,
                        expand=True,
                        padding=ft.padding.only(left=8, right=8),
                    ),
                    GoldDivider(),
                    # Navigation
                    ft.Container(
                        content=ft.Column(nav_items, spacing=2),
                        padding=ft.padding.symmetric(8, 12),
                    ),
                    GoldDivider(),
                    # Stats & Version
                    ft.Container(
                        content=ft.Column(
                            [
                                self.stats_text,
                                ft.Text(
                                    "v5.0.0 Ultimate",
                                    size=10,
                                    color=Brand.TEXT_MUTED,
                                    opacity=0.5,
                                ),
                            ],
                            spacing=2,
                        ),
                        padding=ft.padding.symmetric(12, 18),
                    ),
                ],
                spacing=0,
            ),
            width=280,
            bgcolor=Brand.NAVY_800,
            border=ft.border.only(right=ft.BorderSide(1, Brand.DIVIDER)),
        )

    def _build_right_panel(self):
        """Build the right side panel for document info and quick actions."""
        self.right_panel_docs = ft.Column(spacing=6)
        self.right_panel_reports = ft.Column(spacing=6)

        self.right_panel = ft.Container(
            content=ft.Column(
                [
                    ft.Container(
                        content=ft.Text(
                            "Knowledge Base",
                            size=14,
                            weight="bold",
                            color=Brand.TEXT_PRIMARY,
                        ),
                        padding=ft.padding.symmetric(16, 18),
                        border=ft.border.only(bottom=ft.BorderSide(1, Brand.DIVIDER)),
                    ),
                    ft.Container(
                        content=ft.Column(
                            [
                                ft.Row([
                                    SectionLabel("LOADED DOCUMENTS"),
                                    ft.IconButton(
                                        ft.icons.ADD_ROUNDED,
                                        icon_size=16,
                                        icon_color=Brand.TEXT_MUTED,
                                        tooltip="Add document",
                                        on_click=lambda _: self._pick_files_for_upload(),
                                    ),
                                ]),
                                self.right_panel_docs,
                            ],
                            spacing=8,
                        ),
                        expand=True,
                        padding=16,
                    ),
                    GoldDivider(),
                    ft.Container(
                        content=ft.Column(
                            [
                                SectionLabel("GENERATED REPORTS"),
                                self.right_panel_reports,
                            ],
                            spacing=8,
                        ),
                        padding=16,
                        expand=True,
                    ),
                ],
                spacing=0,
            ),
            width=280,
            bgcolor=Brand.NAVY_800,
            border=ft.border.only(left=ft.BorderSide(1, Brand.DIVIDER)),
            visible=self._right_panel_visible,
        )

        self.file_picker = ft.FilePicker(
            on_result=self._on_files_picked,
            allowed_extensions=["pdf", "docx", "doc", "txt", "md", "csv"],
        )
        self.page.overlay.append(self.file_picker)

    # --- Navigation ---

    def _navigate_to(self, screen_id: str):
        self._active_screen = screen_id
        screen_map = {
            "chat": self.chat_screen.view,
            "documents": self.documents_screen.view,
            "history": self.history_screen.view,
            "settings": self.settings_screen.view,
        }
        self._screen_container.content = screen_map.get(screen_id, self.chat_screen.view)

        # Refresh screen data
        if screen_id == "documents":
            self.documents_screen.refresh_documents(self._uploaded_files)
            self.documents_screen.refresh_reports(self._generated_reports)
        elif screen_id == "history":
            self._refresh_history()
        elif screen_id == "settings":
            self.settings_screen.refresh_from_config()

        self.page.update()

    def _toggle_right_panel(self):
        self._right_panel_visible = not self._right_panel_visible
        self.right_panel.visible = self._right_panel_visible
        self.config.set("right_panel_visible", self._right_panel_visible)
        self.page.update()

    # --- File Upload ---

    def _pick_files_for_upload(self):
        self.file_picker.pick_files(allow_multiple=True)

    def _on_files_picked(self, e: ft.FilePickerResultEvent):
        if e.files:
            for f in e.files:
                self._handle_upload_file(f)

    def _handle_upload_file(self, file_info):
        """Handle file upload from any source."""
        if not file_info or not file_info.path:
            return

        dest = str(self.config.uploads_dir / file_info.name)
        try:
            os.makedirs(os.path.dirname(dest), exist_ok=True)
            shutil.copy(file_info.path, dest)
        except Exception as e:
            self.page.show_snack_bar(
                ft.SnackBar(ft.Text(f"Upload failed: {e}"), bgcolor=Brand.ERROR)
            )
            return

        # Ingest into engine
        try:
            if self.engine:
                result = self.engine.ingest_document(dest)
                doc_id = self.db.add_document(
                    filename=file_info.name,
                    file_path=dest,
                    file_size=result.get("chunks", 0),
                    file_type=os.path.splitext(file_info.name)[1],
                    chunk_count=result.get("chunks", 0),
                    session_id=self.current_session_id,
                )
                self._uploaded_files.append({
                    "id": doc_id,
                    "filename": file_info.name,
                    "file_path": dest,
                    "file_size": os.path.getsize(dest),
                })
                self._refresh_right_panel()
                self.chat_screen.set_status(
                    f"{len(self._uploaded_files)} docs loaded",
                    Brand.SUCCESS,
                )
                self.page.show_snack_bar(
                    ft.SnackBar(
                        ft.Text(f"Document ingested: {file_info.name}"),
                        bgcolor=Brand.SUCCESS,
                    )
                )
        except Exception as e:
            self.page.show_snack_bar(
                ft.SnackBar(ft.Text(f"Ingestion error: {e}"), bgcolor=Brand.ERROR)
            )

    def _handle_remove_document(self, doc: Dict):
        """Remove a document from the knowledge base."""
        file_path = doc.get("file_path", "")
        if self.engine:
            self.engine.remove_document(file_path)
        self._uploaded_files = [d for d in self._uploaded_files if d.get("file_path") != file_path]
        self._refresh_right_panel()
        self.page.update()

    def _handle_open_file(self, report: Dict):
        """Open a generated report file."""
        path = report.get("path", "")
        if path and os.path.exists(path):
            os.startfile(path) if os.name == "nt" else os.system(f"xdg-open '{path}' &")

    def _refresh_right_panel(self):
        """Refresh the right panel document list."""
        self.right_panel_docs.controls.clear()
        for doc in self._uploaded_files:
            self.right_panel_docs.controls.append(
                DocumentListItem(
                    filename=doc["filename"],
                    file_size=self._format_size(doc.get("file_size", 0)),
                    on_remove=lambda d=doc: self._handle_remove_document(d),
                )
            )
        self.right_panel_docs.update()

    # --- Chat / Messaging ---

    def _handle_send_message(self, text: str):
        """Process a user message through the AI pipeline."""
        if self._processing_query:
            return
        if not self.engine:
            self.chat_screen.add_error_message(
                "Engine not initialized. Please configure your API key in Settings."
            )
            return

        # Ensure we have a session
        if not self.current_session_id:
            self._create_new_session(text[:50])

        # Show user message
        now = datetime.now().strftime("%H:%M")
        self.chat_screen.add_user_message(text, now)

        # Save user message to DB
        self.db.add_message(self.current_session_id, "user", text)

        # Auto-title session on first message
        if self.db.get_session(self.current_session_id)["title"] == "New Chat":
            self.db.update_session_title(self.current_session_id, text[:60])
            self._refresh_sidebar_sessions()

        # Show processing state
        self._processing_query = True
        self.chat_screen.set_status("Analyzing...", Brand.WARNING)
        self.chat_screen.show_progress("Initializing pipeline...", 0.0)

        def run_query():
            try:
                result = self.engine.query(
                    text,
                    session_id=self.current_session_id,
                    reports_dir=str(self.config.reports_dir),
                )

                # Update UI on main thread
                def on_done():
                    self.chat_screen.hide_progress()
                    self.chat_screen.hide_agent_steps()
                    self._processing_query = False

                    if result.get("errors") and not result.get("answer").startswith("Please upload"):
                        # Show any non-critical errors as warnings
                        pass

                    self.chat_screen.add_assistant_message(
                        result.get("answer", "No response generated."),
                        chart_data=result.get("chart"),
                        timestamp=datetime.now().strftime("%H:%M"),
                    )

                    # Save assistant message
                    self.db.add_message(
                        self.current_session_id,
                        "assistant",
                        result.get("answer", ""),
                        chart_data=result.get("chart"),
                        reports=result.get("reports"),
                    )

                    # Track reports
                    for fmt, path in result.get("reports", {}).items():
                        if path and os.path.exists(path):
                            self._generated_reports.append({
                                "filename": os.path.basename(path),
                                "path": path,
                                "created_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
                            })
                    self._refresh_right_panel_reports()

                    status = "AI Engine Ready"
                    self.chat_screen.set_status(status, Brand.SUCCESS)
                    self._refresh_sidebar_sessions()
                    self._update_stats()

                self.page.run_task(on_done)

            except Exception as e:
                def on_error():
                    self.chat_screen.hide_progress()
                    self.chat_screen.hide_agent_steps()
                    self._processing_query = False
                    self.chat_screen.add_error_message(str(e))
                    self.chat_screen.set_status("Error occurred", Brand.ERROR)

                self.page.run_task(on_error)

        # Run the query in a background thread to keep UI responsive
        import threading
        threading.Thread(target=run_query, daemon=True).start()

    def _on_engine_progress(self, message: str, pct: float):
        """Callback from the engine to update UI progress."""
        def update():
            self.chat_screen.show_progress(message, pct)
        self.page.run_task(update)

    # --- Session Management ---

    def _create_new_session(self, title: str = "New Chat") -> str:
        session_id = self.db.create_session(title)
        self.current_session_id = session_id
        self.config.set("last_active_session", session_id)
        self._refresh_sidebar_sessions()
        return session_id

    def _handle_new_chat(self):
        """Create and switch to a new chat session."""
        self._create_new_session()
        self.chat_screen.clear_messages()
        self._navigate_to("chat")
        self.chat_screen.focus_input()

    def _handle_select_session(self, session: Dict):
        """Load an existing session."""
        sid = session.get("id")
        if not sid:
            return
        self.current_session_id = sid
        self.config.set("last_active_session", sid)

        # Load messages
        messages = self.db.get_messages(sid)
        self.chat_screen.clear_messages()
        if messages:
            self.chat_screen.show_empty_state(False)
            for msg in messages:
                if msg["role"] == "user":
                    self.chat_screen.add_user_message(msg["content"])
                elif msg["role"] == "assistant":
                    self.chat_screen.add_assistant_message(
                        msg["content"],
                        chart_data=msg.get("chart_data"),
                    )
        self._navigate_to("chat")
        self._refresh_sidebar_sessions()

    def _handle_delete_session(self, session: Dict):
        sid = session.get("id")
        if sid:
            self.db.delete_session(sid)
            if self.current_session_id == sid:
                self._handle_new_chat()
            self._refresh_sidebar_sessions()

    def _handle_pin_session(self, session: Dict):
        sid = session.get("id")
        if sid:
            self.db.toggle_pin_session(sid)
            self._refresh_sidebar_sessions()

    def _refresh_sidebar_sessions(self):
        """Refresh the sidebar session list."""
        sessions = self.db.list_sessions(limit=30)
        self.sidebar_sessions_list.controls.clear()

        if not sessions:
            self.sidebar_sessions_list.controls.append(
                ft.Container(
                    content=ft.Text(
                        "No conversations yet",
                        size=12,
                        color=Brand.TEXT_MUTED,
                        text_align=ft.TextAlign.CENTER,
                    ),
                    padding=20,
                    alignment=ft.alignment.center,
                )
            )
        else:
            for s in sessions:
                sid = s["id"]
                is_active = sid == self.current_session_id
                is_pinned = bool(s.get("is_pinned", 0))
                updated = s.get("updated_at", "")
                title = s.get("title", "Untitled")

                time_str = self._format_time(updated)

                from src.ui.screens.history_screen import HistoryScreen
                time_str = HistoryScreen._format_time(updated)

                item = ft.Container(
                    content=ft.Column(
                        [
                            ft.Text(
                                title,
                                size=12,
                                weight="w600" if is_active else "w400",
                                color=Brand.GOLD_400 if is_active else Brand.TEXT_PRIMARY,
                                max_lines=1,
                                overflow=ft.TextOverflow.ELLIPSIS,
                            ),
                            ft.Row(
                                [
                                    ft.Text(time_str, size=10, color=Brand.TEXT_MUTED),
                                    ft.Icon(
                                        ft.icons.PUSH_PIN_ROUNDED if is_pinned else ft.icons.PUSH_PIN_OUTLINED,
                                        size=10,
                                        color=Brand.GOLD_500 if is_pinned else Brand.TEXT_MUTED,
                                    ),
                                ],
                                spacing=4,
                            ),
                        ],
                        spacing=2,
                    ),
                    padding=ft.padding.symmetric(8, 12),
                    border_radius=8,
                    bgcolor=ft.colors.with_opacity(0.12, Brand.GOLD_500)
                    if is_active
                    else None,
                    on_click=lambda s=s: self._handle_select_session(s),
                )
                self.sidebar_sessions_list.controls.append(item)

        self.sidebar_sessions_list.update()
        self._update_stats()

    def _refresh_history(self):
        """Refresh the history screen."""
        sessions = self.db.list_sessions(include_archived=False, limit=50)
        self.history_screen.refresh_sessions(sessions, self.current_session_id)

    def _refresh_right_panel_reports(self):
        """Update the reports list in the right panel."""
        self.right_panel_reports.controls.clear()
        for rpt in self._generated_reports[-5:]:  # Show last 5
            ext = os.path.splitext(rpt["filename"])[1].lower()
            icon = ft.icons.TABLE_CHART_ROUNDED if ext == ".xlsx" else ft.icons.DESCRIPTION_ROUNDED
            self.right_panel_reports.controls.append(
                ft.Container(
                    content=ft.Row([
                        ft.Icon(icon, size=16, color=Brand.SUCCESS),
                        ft.Text(
                            rpt["filename"],
                            size=11,
                            color=Brand.TEXT_SECONDARY,
                            max_lines=1,
                            overflow=ft.TextOverflow.ELLIPSIS,
                        ),
                    ], spacing=6),
                    padding=ft.padding.symmetric(4, 0),
                )
            )
        self.right_panel_reports.update()

    # --- Settings ---

    def _handle_apply_settings(self, settings: Dict):
        """Apply settings from the settings screen."""
        for key, value in settings.items():
            self.config.set(key, value)

        # Reinitialize engine with new settings
        self._init_engine()

    def _handle_reset_engine(self):
        """Reset the AI engine completely."""
        if self.engine:
            self.engine.reset()
        self._uploaded_files.clear()
        self._generated_reports.clear()
        self._refresh_right_panel()
        self.chat_screen.set_status("Engine Reset", Brand.WARNING)
        self.page.show_snack_bar(
            ft.SnackBar(ft.Text("Engine reset successfully"), bgcolor=Brand.WARNING)
        )

    # --- State Restoration ---

    def _restore_state(self):
        """Restore previous state on app launch."""
        # Restore last session
        last_sid = self.config.get("last_active_session")
        if last_sid:
            session = self.db.get_session(last_sid)
            if session:
                self.current_session_id = last_sid
                messages = self.db.get_messages(last_sid)
                if messages:
                    self.chat_screen.show_empty_state(False)
                    for msg in messages:
                        if msg["role"] == "user":
                            self.chat_screen.add_user_message(msg["content"])
                        elif msg["role"] == "assistant":
                            self.chat_screen.add_assistant_message(
                                msg["content"],
                                chart_data=msg.get("chart_data"),
                            )

        self._refresh_sidebar_sessions()
        self._update_stats()

    def _update_stats(self):
        """Update the stats display."""
        stats = self.db.get_stats()
        doc_count = len(self._uploaded_files)
        self.stats_text.text = (
            f"{stats['sessions']} chats  |  {stats['messages']} msgs  |  {doc_count} docs"
        )
        self.stats_text.update()

    # --- Utilities ---

    @staticmethod
    def _format_size(size_bytes: int) -> str:
        if size_bytes == 0:
            return "0 B"
        for unit in ["B", "KB", "MB", "GB"]:
            if size_bytes < 1024:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024
        return f"{size_bytes:.1f} TB"

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
