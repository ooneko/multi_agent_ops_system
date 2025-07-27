"""数据模型测试"""
import unittest
from datetime import datetime
from cz_agent_simple.models import (
    ServerStatus, ConnectivityStatus, HardwareInfo, LocationInfo,
    NetworkPath, ConnectivityInfo, ServerDetails, TopologyInfo,
    PortInfo, SwitchInfo, LogEntry, InstallationLog
)


class TestModels(unittest.TestCase):
    
    def test_server_status_enum(self):
        """测试服务器状态枚举"""
        self.assertEqual(ServerStatus.ONLINE.value, "online")
        self.assertEqual(ServerStatus.OFFLINE.value, "offline")
        self.assertEqual(ServerStatus.INSTALL_FAILED.value, "install_failed")
    
    def test_hardware_info(self):
        """测试硬件信息模型"""
        hardware = HardwareInfo(
            cpu_model="Intel Xeon E5-2680",
            cpu_cores=32,
            memory_gb=128,
            disk_gb=1000,
            network_cards=["eth0", "eth1"]
        )
        self.assertEqual(hardware.cpu_cores, 32)
        self.assertEqual(hardware.memory_gb, 128)
        self.assertEqual(len(hardware.network_cards), 2)
    
    def test_location_info(self):
        """测试位置信息模型"""
        location = LocationInfo(
            region="cn-north",
            availability_zone="az1",
            room="room-01",
            rack_id="rack-A01",
            rack_position=15
        )
        self.assertEqual(location.region, "cn-north")
        self.assertEqual(location.rack_position, 15)
    
    def test_server_details(self):
        """测试服务器详情模型"""
        hardware = HardwareInfo(
            cpu_model="Intel Xeon",
            cpu_cores=32,
            memory_gb=128,
            disk_gb=1000,
            network_cards=["eth0"]
        )
        location = LocationInfo(
            region="cn-north",
            availability_zone="az1",
            room="room-01",
            rack_id="rack-A01",
            rack_position=15
        )
        server = ServerDetails(
            server_id="srv-001",
            hostname="server-001",
            status=ServerStatus.ONLINE,
            ip_address="192.168.1.100",
            hardware=hardware,
            location=location,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        self.assertEqual(server.server_id, "srv-001")
        self.assertEqual(server.status, ServerStatus.ONLINE)
        self.assertIsInstance(server.tags, dict)
    
    def test_topology_info(self):
        """测试拓扑信息模型"""
        in_band = NetworkPath(
            path=["server-001", "switch-tor-01", "switch-agg-01", "switch-core-01"],
            status=ConnectivityStatus.CONNECTED
        )
        out_band = NetworkPath(
            path=["server-001-bmc", "switch-oob-01", "switch-oob-agg-01"],
            status=ConnectivityStatus.DISCONNECTED,
            last_hop_reachable="switch-oob-01"
        )
        connectivity = ConnectivityInfo(
            is_connected=True,
            last_check_time=datetime.now()
        )
        topology = TopologyInfo(
            server_id="srv-001",
            region="cn-north",
            availability_zone="az1",
            room="room-01",
            rack_id="rack-A01",
            rack_position=15,
            in_band_network=in_band,
            out_of_band_network=out_band,
            uplink_switches=["switch-tor-01"],
            in_band_connectivity=connectivity,
            out_of_band_connectivity=connectivity
        )
        self.assertEqual(topology.in_band_network.status, ConnectivityStatus.CONNECTED)
        self.assertEqual(topology.out_of_band_network.status, ConnectivityStatus.DISCONNECTED)
    
    def test_switch_info(self):
        """测试交换机信息模型"""
        port = PortInfo(
            port_id="port-01",
            port_number=1,
            status="up",
            connected_device="server-001",
            speed_gbps=10,
            vlan_id=100
        )
        location = LocationInfo(
            region="cn-north",
            availability_zone="az1",
            room="room-01",
            rack_id="rack-A01",
            rack_position=1
        )
        switch = SwitchInfo(
            switch_id="sw-001",
            name="switch-tor-01",
            model="Cisco Nexus 9000",
            status="active",
            location=location,
            ports=[port],
            connected_servers=["server-001"],
            uplink_switch="switch-agg-01"
        )
        self.assertEqual(switch.switch_id, "sw-001")
        self.assertEqual(len(switch.ports), 1)
        self.assertEqual(switch.ports[0].connected_device, "server-001")
    
    def test_installation_log(self):
        """测试安装日志模型"""
        log_entry = LogEntry(
            timestamp=datetime.now(),
            level="ERROR",
            message="Network configuration failed",
            component="network-setup",
            details={"interface": "eth0", "error": "No DHCP response"}
        )
        install_log = InstallationLog(
            server_id="srv-001",
            start_time=datetime.now(),
            end_time=None,
            status="failed",
            logs=[log_entry],
            error_summary="Network configuration failed during installation"
        )
        self.assertEqual(install_log.status, "failed")
        self.assertEqual(len(install_log.logs), 1)
        self.assertEqual(install_log.logs[0].level, "ERROR")


if __name__ == "__main__":
    unittest.main()