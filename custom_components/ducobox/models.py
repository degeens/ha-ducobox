"""Data models for DucoBox."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class DucoBoxInfo:
    """Information about the DucoBox."""

    model: str
    api_version: str
    serial_number: str
    mac_address: str


@dataclass
class DucoNode:
    """A Duco node."""

    node_id: int
    node_type: str
    parent_node_id: int


@dataclass
class DucoBoxNode(DucoNode):
    """A Duco Box node."""

    state: str | None = None
    time_state_remain: int | None = None
    time_state_end: int | None = None
    mode: str | None = None
    flow_lvl_tgt: int | None = None


@dataclass
class DucoBsrhNode(DucoNode):
    """A Duco BSRH (A relative humidity box sensor) node."""

    rh: int | None = None
    iaq_rh: int | None = None


@dataclass
class DucoUcbatNode(DucoNode):
    """A Duco UCBAT (A battery-powered user control) node."""
