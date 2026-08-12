"""Configuration management for TermTune."""

import logging
import os
from pathlib import Path

try:
    import tomllib
except ImportError:
    import collections as tomllib  # Fallback type stub if ever running Python < 3.11


logger = logging.getLogger(__name__)


class Settings:
    """TermTune user configuration settings."""

    def __init__(self):
        self.volume: int = 80
        self.shuffle: bool = False
        self.repeat: str = "off"  # "off", "all", "track"
        self.theme: str = "dark"
        self.debug: bool = False
        self.config_dir: Path = Path.home() / ".termtune"
        self.config_file: Path = self.config_dir / "config.toml"
        self.load()

    def load(self) -> None:
        """Load settings from ~/.termtune/config.toml if present."""
        if not self.config_file.exists():
            return

        try:
            with open(self.config_file, "rb") as f:
                data = tomllib.load(f)

            self.volume = int(data.get("volume", self.volume))
            self.shuffle = bool(data.get("shuffle", self.shuffle))
            self.repeat = str(data.get("repeat", self.repeat))
            self.theme = str(data.get("theme", self.theme))
            self.debug = bool(data.get("debug", self.debug))
        except Exception as e:
            logger.warning(f"Failed to load config file: {e}")

    def save(self) -> None:
        """Save settings to ~/.termtune/config.toml."""
        try:
            self.config_dir.mkdir(parents=True, exist_ok=True)
            content = (
                f'volume = {self.volume}\n'
                f'shuffle = {"true" if self.shuffle else "false"}\n'
                f'repeat = "{self.repeat}"\n'
                f'theme = "{self.theme}"\n'
                f'debug = {"true" if self.debug else "false"}\n'
            )
            with open(self.config_file, "w", encoding="utf-8") as f:
                f.write(content)
        except Exception as e:
            logger.warning(f"Failed to save config file: {e}")


settings = Settings()
