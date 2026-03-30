"""Data models for the DucoBox integration."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class DucoBoxInfo:
    """Information about the DucoBox."""

    model: str
    serial_number: str
    mac_address: str


@dataclass
class DucoBoxNode:
    """A Duco node."""

    node_id: int
    node_type: str
    parent_node_id: int
    name: str | None = None

    state: str | None = None
    time_state_remain: int | None = None
    time_state_end: int | None = None
    mode: str | None = None
    flow_lvl_tgt: int | None = None

    rh: int | None = None
    iaq_rh: int | None = None

    co2: int | None = None
    iaq_co2: int | None = None
