"""数据模型定义"""
from typing import List, Optional, Dict, Any
from datetime import datetime
from dataclasses import dataclass, field
from enum import Enum


class ServerStatus(Enum):
    ONLINE = "online"
    OFFLINE = "offline"
    MAINTENANCE = "maintenance"
    INSTALLING = "installing"
    INSTALL_FAILED = "install_failed"


class ConnectivityStatus(Enum):
    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    PARTIAL = "partial"


@dataclass
class HardwareInfo:
    cpu_model: str
    cpu_cores: int
    memory_gb: int
    disk_gb: int
    network_cards: List[str]


@dataclass
class LocationInfo:
    region: str
    availability_zone: str
    room: str
    rack_id: str
    rack_position: int


@dataclass
class NetworkPath:
    path: List[str]
    status: ConnectivityStatus
    last_hop_reachable: Optional[str] = None


@dataclass
class ConnectivityInfo:
    is_connected: bool
    last_check_time: datetime
    failure_reason: Optional[str] = None


@dataclass
class ServerDetails:
    server_id: str
    hostname: str
    status: ServerStatus
    ip_address: str
    hardware: HardwareInfo
    location: LocationInfo
    created_at: datetime
    updated_at: datetime
    tags: Dict[str, str] = field(default_factory=dict)


@dataclass
class TopologyInfo:
    server_id: str
    region: str
    availability_zone: str
    room: str
    rack_id: str
    rack_position: int
    in_band_network: NetworkPath
    out_of_band_network: NetworkPath
    uplink_switches: List[str]
    in_band_connectivity: ConnectivityInfo
    out_of_band_connectivity: ConnectivityInfo


@dataclass
class PortInfo:
    port_id: str
    port_number: int
    status: str
    connected_device: Optional[str] = None
    speed_gbps: int = 10
    vlan_id: Optional[int] = None


@dataclass
class SwitchInfo:
    switch_id: str
    name: str
    model: str
    status: str
    location: LocationInfo
    ports: List[PortInfo]
    connected_servers: List[str]
    uplink_switch: Optional[str] = None


@dataclass
class LogEntry:
    timestamp: datetime
    level: str
    message: str
    component: str
    details: Optional[Dict[str, Any]] = None


@dataclass
class InstallationLog:
    server_id: str
    start_time: datetime
    end_time: Optional[datetime]
    status: str
    logs: List[LogEntry]
    error_summary: Optional[str] = None