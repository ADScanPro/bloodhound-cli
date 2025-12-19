"""Configuration models using pydantic-settings."""

from __future__ import annotations

import configparser
import os
from pathlib import Path
from typing import Optional

from pydantic import AnyHttpUrl, Field
from pydantic_settings import BaseSettings, SettingsConfigDict

try:
    import pwd  # type: ignore[attr-defined]
except ImportError:  # pragma: no cover
    pwd = None

def _get_effective_user_home() -> Path:
    """Return the home directory that should own BloodHound CLI config/state.

    If running under sudo, prefer the invoking user's home directory so we don't
    split configuration between `/root` and the normal user's home.
    """
    sudo_user = os.environ.get("SUDO_USER")
    if sudo_user:
        if pwd is not None:
            try:
                return Path(pwd.getpwnam(sudo_user).pw_dir)
            except KeyError:
                pass
    return Path.home()


CONFIG_FILE = _get_effective_user_home() / ".bloodhound_config"


class CEConfig(BaseSettings):
    """Settings for BloodHound CE edition."""

    base_url: AnyHttpUrl = Field(default="http://localhost:8080")
    api_token: Optional[str] = None
    username: str = "admin"
    password: Optional[str] = None
    verify: bool = True

    model_config = SettingsConfigDict(env_prefix="ce_", env_file=".env", extra="ignore")


class LegacyConfig(BaseSettings):
    """Settings for BloodHound legacy (Neo4j)."""

    uri: str = Field(default="bolt://localhost:7687")
    user: str = "neo4j"
    password: str = "neo4j"

    model_config = SettingsConfigDict(env_prefix="legacy_", env_file=".env", extra="ignore")


def load_ce_config() -> CEConfig:
    """Load CE config from env vars, .env y ~/.bloodhound_config."""
    defaults = {}
    if CONFIG_FILE.exists():
        parser = configparser.ConfigParser()
        parser.read(CONFIG_FILE)
        if parser.has_section("CE"):
            defaults.update(parser["CE"])  # type: ignore[arg-type]
    return CEConfig(**defaults)


def load_legacy_config() -> LegacyConfig:
    """Load legacy config from env vars, .env y ~/.bloodhound_config."""
    defaults = {}
    if CONFIG_FILE.exists():
        parser = configparser.ConfigParser()
        parser.read(CONFIG_FILE)
        if parser.has_section("LEGACY"):
            defaults.update(parser["LEGACY"])  # type: ignore[arg-type]
    return LegacyConfig(**defaults)
