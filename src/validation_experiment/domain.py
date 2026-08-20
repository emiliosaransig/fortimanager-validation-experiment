"""Canonical domain model for the experiment."""

from ipaddress import IPv4Address
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class CanonicalDeviceRecord(BaseModel):
    """Minimal normalized device representation used by the experiment."""

    model_config = ConfigDict(strict=True, extra="forbid")

    name: str
    hostname: str | None = None
    serial_number: str
    hardware_model: str
    management_ip: IPv4Address
    ha_state: Literal["standalone", "clustered"]
    ha_group_name: str | None = None
    ha_members: list[str] = Field(default_factory=list)
