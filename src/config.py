"""
FinLegal-Chat Ultimate - Configuration Manager
Secure settings storage with JSON persistence.
"""

import os
import json
import base64
import hashlib
import threading
from typing import Any, Optional, Dict
from pathlib import Path


class ConfigManager:
    """Manages application configuration with secure credential storage."""

    DEFAULT_CONFIG = {
        "app_version": "5.0.0",
        "mode": "openai",  # "openai" or "local"
        "openai_api_key": "",
        "openai_model": "gpt-4o",
        "local_url": "http://localhost:11434",
        "local_model": "llama3",
        "theme": "dark",  # "dark" or "light"
        "language": "fa",  # "fa" (Persian), "en", "ar"
        "font_size": 14,
        "send_on_enter": True,
        "show_timestamps": True,
        "auto_save_chats": True,
        "max_history_sessions": 100,
        "chunk_size": 2000,
        "chunk_overlap": 300,
        "retrieval_k": 10,
        "temperature": 0.0,
        "window_width": 1500,
        "window_height": 950,
        "sidebar_width": 300,
        "right_panel_visible": True,
        "recent_files": [],
        "last_active_session": None,
    }

    def __init__(self, config_dir: Optional[str] = None):
        self._config_dir = Path(config_dir or self._get_default_config_dir())
        self._config_dir.mkdir(parents=True, exist_ok=True)
        self._config_file = self._config_dir / "config.json"
        self._secrets_file = self._config_dir / ".secrets"
        self._lock = threading.Lock()
        self._cache: Dict[str, Any] = {}
        self._load()

    @staticmethod
    def _get_default_config_dir() -> str:
        if os.name == "nt":
            base = os.environ.get("APPDATA", os.path.expanduser("~"))
            return os.path.join(base, "FinLegal-Chat", "config")
        elif os.name == "darwin":
            return os.path.expanduser("~/Library/Application Support/FinLegal-Chat/config")
        else:
            return os.path.expanduser("~/.config/FinLegal-Chat/config")

    def _get_encryption_key(self) -> bytes:
        """Derive a local machine-specific key for light obfuscation."""
        machine_id = os.name + str(os.getlogin()) + os.path.expanduser("~")
        return hashlib.sha256(machine_id.encode()).digest()[:32]

    def _encrypt_value(self, value: str) -> str:
        """Simple XOR-based obfuscation for local storage (not cryptographic security)."""
        if not value:
            return ""
        key = self._get_encryption_key()
        data = value.encode("utf-8")
        encrypted = bytes([b ^ key[i % len(key)] for i, b in enumerate(data)])
        return base64.b64encode(encrypted).decode("utf-8")

    def _decrypt_value(self, value: str) -> str:
        """Decrypt obfuscated value."""
        if not value:
            return ""
        try:
            key = self._get_encryption_key()
            data = base64.b64decode(value.encode("utf-8"))
            decrypted = bytes([b ^ key[i % len(key)] for i, b in enumerate(data)])
            return decrypted.decode("utf-8")
        except Exception:
            return value

    def _load(self):
        """Load configuration from disk."""
        with self._lock:
            self._cache = dict(self.DEFAULT_CONFIG)
            if self._config_file.exists():
                try:
                    with open(self._config_file, "r", encoding="utf-8") as f:
                        stored = json.load(f)
                    self._cache.update(stored)
                except (json.JSONDecodeError, IOError):
                    pass

            # Load secrets
            if self._secrets_file.exists():
                try:
                    with open(self._secrets_file, "r", encoding="utf-8") as f:
                        secrets = json.load(f)
                    if "openai_api_key" in secrets:
                        self._cache["openai_api_key"] = self._decrypt_value(secrets["openai_api_key"])
                except (json.JSONDecodeError, IOError):
                    pass

    def save(self):
        """Persist configuration to disk."""
        with self._lock:
            safe_config = {k: v for k, v in self._cache.items() if k != "openai_api_key"}
            try:
                with open(self._config_file, "w", encoding="utf-8") as f:
                    json.dump(safe_config, f, indent=2, ensure_ascii=False)

                # Save secrets separately
                secrets = {}
                if self._cache.get("openai_api_key"):
                    secrets["openai_api_key"] = self._encrypt_value(self._cache["openai_api_key"])
                with open(self._secrets_file, "w", encoding="utf-8") as f:
                    json.dump(secrets, f, indent=2)
            except IOError as e:
                print(f"Warning: Could not save config: {e}")

    def get(self, key: str, default: Any = None) -> Any:
        """Get a configuration value."""
        return self._cache.get(key, default)

    def set(self, key: str, value: Any):
        """Set a configuration value and auto-save."""
        with self._lock:
            self._cache[key] = value
        self.save()

    def get_api_key(self) -> str:
        """Get the decrypted API key."""
        return self._cache.get("openai_api_key", "")

    def set_api_key(self, key: str):
        """Set and encrypt the API key."""
        self.set("openai_api_key", key)

    def reset_to_defaults(self):
        """Reset all settings to defaults."""
        with self._lock:
            self._cache = dict(self.DEFAULT_CONFIG)
        self.save()

    def add_recent_file(self, file_path: str, max_files: int = 10):
        """Add a file to the recent files list."""
        recent = list(self._cache.get("recent_files", []))
        if file_path in recent:
            recent.remove(file_path)
        recent.insert(0, file_path)
        self._cache["recent_files"] = recent[:max_files]
        self.save()

    @property
    def is_local_mode(self) -> bool:
        return self._cache.get("mode", "openai") == "local"

    @property
    def uploads_dir(self) -> Path:
        uploads = self._config_dir.parent / "uploads"
        uploads.mkdir(parents=True, exist_ok=True)
        return uploads

    @property
    def reports_dir(self) -> Path:
        reports = self._config_dir.parent / "reports"
        reports.mkdir(parents=True, exist_ok=True)
        return reports

    @property
    def db_path(self) -> Path:
        return self._config_dir.parent / "data" / "finlegal.db"
