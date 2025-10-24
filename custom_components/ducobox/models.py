"""Data models for DucoBox."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class DucoBoxDeviceInfo:
    """Device information from DucoBox."""

    model: str
    api_version: str
    serial_number: str
    mac_address: str


@dataclass
class DucoBoxData:
    """Data from DucoBox."""

    state: str | None = None
    time_state_remain: int | None = None
    time_state_end: int | None = None
    mode: str | None = None
    flow_lvl_tgt: int | None = None
    rh: int | None = None
    iaq_rh: int | None = None
