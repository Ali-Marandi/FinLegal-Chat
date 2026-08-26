/*
* FinLegal-Chat Ultimate - Documents Screen
* Manage uploaded documents and generated reports.
*/

import os
import flet as ft
from typing import Callable, List, Dict, Optional
from src.ui.theme import Brand, Styles
from src.ui.components import (
    DocumentListItem,
    SectionLabel,
    GoldDivider,
    EmptyState,
)


class DocumentsScreen:
    """Document management screen with upload, list, and generated reports."""

    def __init__(
        self,
        page: ft.Page,
        on_upload_files: Callable = None,
        on_remove_document: Callable = None,
        on_open_file: Callable = None,
    ):
        self.page = page
        self.on_upload = on_upload_files
        self.on_remove = on_remove_document
        self.on_open = on_open_file

        self.uploaded_docs_list = ft.Column(spacing=8)
        self.reports_list = ft.Column(spacing=8)

        self._build_ui()

    def _build_ui(self):
        self.upload_empty = EmptyState(
            icon=ft.icons.CLOUD_UPLOAD_OUTLINED,
            title="No documents uploaded",
            subtitle="Upload PDF, DOCX, or TXT files to build your knowledge base",
        )

        self.reports_empty = EmptyState(
            icon=ft.icons.DESCRIPTION_OUTLINED,
            title="No reports generated yet",
            subtitle="Reports are automatically generated when you query the AI",
        )

        self.file_picker = ft.FilePicker(
            on_result=self._on_files_picked,
            allowed_extensions=["pdf", "docx", "doc", "txt", "md", "csv"],
        )
        self.page.overlay.append(self.file_picker)

        self.doc_count_text = ft.Text(
            "0 documents", size=12, color=Brand.TEXT_MUTED
        )

        self.report_count_text = ft.Text(
            "0 reports", size=12, color=Brand.TEXT_MUTED
        )

        self.view = ft.Column(
            [
                # Header
                ft.Container(
                    content=ft.Row([
                        ft.Icon(ft.icons.FOLDER_OPEN_ROUNDED, color=Brand.GOLD_500, size=24),
                        ft.Text("Documents", size=20, weight="bold", color=Brand.TEXT_PRIMARY),
                        ft.Spacer(),
                        ft.ElevatedButton(
                            "Upload Files",
                            icon=ft.icons.CLOUD_UPLOAD_ROUNDED,
                            on_click=lambda _: self.file_picker.pick_files(allow_multiple=True),
                            **Styles.gold_button(),
                        ),
                    ], spacing=12),
                    padding=ft.padding.symmetric(20, 24),
                    border=ft.border.only(bottom=ft.BorderSide(1, Brand.DIVIDER)),
                ),
                # Scrollable content
                ft.Column(
                    [
                        # Uploaded Documents Section
                        ft.Container(
                            content=ft.Column([
                                ft.Row([
                                    SectionLabel("UPLOADED DOCUMENTS"),
                                    self.doc_count_text,
                                ]),
                                ft.Container(height=8),
                                self.uploaded_docs_list,
                                self.upload_empty,
                            ], spacing=8),
                            padding=16,
                            bgcolor=Brand.SURFACE_CARD,
                            border_radius=12,
                            border=ft.border.all(1, Brand.DIVIDER),
                            margin=ft.margin.only(bottom=16),
                        ),

                        # Generated Reports Section
                        ft.Container(
                            content=ft.Column([
                                ft.Row([
                                    SectionLabel("GENERATED REPORTS"),
                                    self.report_count_text,
                                ]),
                                ft.Container(height=8),
                                self.reports_list,
                                self.reports_empty,
                            ], spacing=8),
                            padding=16,
                            bgcolor=Brand.SURFACE_CARD,
                            border_radius=12,
                            border=ft.border.all(1, Brand.DIVIDER),
                            margin=ft.margin.only(bottom=16),
                        ),
                    ],
                    scroll=ft.ScrollMode.ADAPTIVE,
                    expand=True,
                    padding=ft.padding.symmetric(16, 24),
                ),
            ],
            expand=True,
            spacing=0,
        )

    def _on_files_picked(self, e: ft.FilePickerResultEvent):
        if e.files and self.on_upload:
            for f in e.files:
                self.on_upload(f)

    def refresh_documents(self, documents: List[Dict]):
        self.uploaded_docs_list.controls.clear()
        if not documents:
            self.upload_empty.visible = True
        else:
            self.upload_empty.visible = False
            for doc in documents:
                filename = doc.get("filename", "unknown")
                size_str = self._format_size(doc.get("file_size", 0))
                self.uploaded_docs_list.controls.append(
                    DocumentListItem(
                        filename=filename,
                        file_size=size_str,
                        on_remove=lambda d=doc: self.on_remove(d) if self.on_remove else None,
                    )
                )
        self.doc_count_text.text = f"{len(documents)} document{'s' if len(documents) != 1 else ''}"
        self.page.update()

    def refresh_reports(self, reports: List[Dict]):
        self.reports_list.controls.clear()
        if not reports:
            self.reports_empty.visible = True
        else:
            self.reports_empty.visible = False
            for rpt in reports:
                filename = rpt.get("filename", "report")
                ext = os.path.splitext(filename)[1].lower()
                icon = ft.icons.PICTURE_AS_PDF_ROUNDED if ext == ".pdf" \
                    else ft.icons.TABLE_CHART_ROUNDED if ext == ".xlsx" \
                    else ft.icons.DESCRIPTION_ROUNDED
                self.reports_list.controls.append(
                    ft.Container(
                        content=ft.Row([
                            ft.Container(
                                content=ft.Icon(icon, size=20, color=Brand.SUCCESS),
                                padding=8,
                                bgcolor=ft.colors.with_opacity(0.1, Brand.SUCCESS),
                                border_radius=8,
                            ),
                            ft.Column([
                                ft.Text(filename, size=13, weight="w500", color=Brand.TEXT_PRIMARY),
                                ft.Text(rpt.get("created_at", ""), size=11, color=Brand.TEXT_MUTED),
                            ], spacing=2, expand=True),
                            ft.IconButton(
                                icon=ft.icons.FOLDER_OPEN_ROUNDED,
                                icon_size=18,
                                icon_color=Brand.TEXT_SECONDARY,
                                tooltip="Open",
                                on_click=lambda r=rpt: self.on_open(r) if self.on_open else None,
                            ),
                        ], spacing=10),
                        padding=ft.padding.symmetric(8, 12),
                        border_radius=8,
                        bgcolor=Brand.SURFACE_CARD,
                        border=ft.border.all(1, Brand.DIVIDER),
                    )
                )
        self.report_count_text.text = f"{len(reports)} report{'s' if len(reports) != 1 else ''}"
        self.page.update()

    @staticmethod
    def _format_size(size_bytes: int) -> str:
        if size_bytes == 0:
            return "0 B"
        for unit in ["B", "KB", "MB", "GB"]:
            if size_bytes < 1024:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024
        return f"{size_bytes:.1f} TB"
