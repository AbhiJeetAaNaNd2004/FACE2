"""
Camera Discovery Utility
Provides ONVIF-based network scanning to automatically detect IP cameras
"""

import asyncio
import socket
import struct
import xml.etree.ElementTree as ET
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from ipaddress import IPv4Network, IPv4Address
import requests
from requests.auth import HTTPDigestAuth
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
import time

logger = logging.getLogger(__name__)

@dataclass
class CameraInfo:
    """Camera information discovered via ONVIF"""
    ip_address: str
    port: int
    manufacturer: str
    model: str
    firmware_version: str
    stream_urls: List[str]
    onvif_supported: bool
    device_service_url: str
    media_service_url: str
    username: Optional[str] = None
    password: Optional[str] = None

class ONVIFCameraDiscovery:
    """
    ONVIF-based camera discovery system
    """
    
    # WS-Discovery probe message for ONVIF devices
    ONVIF_PROBE_MESSAGE = """<?xml version="1.0" encoding="UTF-8"?>
<soap:Envelope xmlns:soap="http://www.w3.org/2003/05/soap-envelope" 
               xmlns:wsa="http://schemas.xmlsoap.org/ws/2004/08/addressing" 
               xmlns:tns="http://schemas.xmlsoap.org/ws/2005/04/discovery">
    <soap:Header>
        <wsa:Action>http://schemas.xmlsoap.org/ws/2005/04/discovery/Probe</wsa:Action>
        <wsa:MessageID>uuid:12345678-1234-1234-1234-123456789012</wsa:MessageID>
        <wsa:To>urn:schemas-xmlsoap-org:ws:2005:04:discovery</wsa:To>
    </soap:Header>
    <soap:Body>
        <tns:Probe>
            <tns:Types>tns:NetworkVideoTransmitter</tns:Types>
        </tns:Probe>
    </soap:Body>
</soap:Envelope>"""

    def __init__(self, timeout: int = 5):
        self.timeout = timeout
        self.discovered_cameras: List[CameraInfo] = []

    async def discover_cameras(self, network_range: str = "192.168.1.0/24") -> List[CameraInfo]:
        """
        Discover cameras on the network using ONVIF WS-Discovery
        
        Args:
            network_range: Network range to scan (CIDR notation)
            
        Returns:
            List of discovered camera information
        """
        logger.info(f"Starting camera discovery on network: {network_range}")
        
        # First try ONVIF WS-Discovery
        onvif_cameras = await self._discover_onvif_cameras()
        
        # Then try port scanning for common camera ports
        port_scan_cameras = await self._discover_via_port_scan(network_range)
        
        # Combine and deduplicate results
        all_cameras = self._merge_camera_lists(onvif_cameras, port_scan_cameras)
        
        # Get detailed information for each camera
        detailed_cameras = await self._get_camera_details(all_cameras)
        
        self.discovered_cameras = detailed_cameras
        logger.info(f"Discovery complete. Found {len(detailed_cameras)} cameras")
        
        return detailed_cameras

    async def _discover_onvif_cameras(self) -> List[CameraInfo]:
        """Discover cameras using ONVIF WS-Discovery multicast"""
        cameras = []
        
        try:
            # Create UDP socket for multicast
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            sock.settimeout(self.timeout)
            
            # Enable broadcast
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            
            # Send WS-Discovery probe
            multicast_addr = ('239.255.255.250', 3702)
            sock.sendto(self.ONVIF_PROBE_MESSAGE.encode('utf-8'), multicast_addr)
            
            # Listen for responses
            start_time = time.time()
            while time.time() - start_time < self.timeout:
                try:
                    data, addr = sock.recvfrom(4096)
                    camera_info = self._parse_onvif_response(data.decode('utf-8'), addr[0])
                    if camera_info:
                        cameras.append(camera_info)
                except socket.timeout:
                    break
                except Exception as e:
                    logger.debug(f"Error parsing ONVIF response: {e}")
                    
            sock.close()
            
        except Exception as e:
            logger.error(f"ONVIF discovery failed: {e}")
            
        return cameras

    async def _discover_via_port_scan(self, network_range: str) -> List[CameraInfo]:
        """Discover cameras by scanning common camera ports"""
        cameras = []
        common_ports = [80, 554, 8080, 8081, 8000, 8888, 9000]
        
        try:
            network = IPv4Network(network_range, strict=False)
            
            # Use ThreadPoolExecutor for parallel scanning
            with ThreadPoolExecutor(max_workers=50) as executor:
                futures = []
                
                for ip in network.hosts():
                    for port in common_ports:
                        future = executor.submit(self._check_camera_port, str(ip), port)
                        futures.append(future)
                
                for future in as_completed(futures, timeout=self.timeout * 2):
                    try:
                        result = future.result()
                        if result:
                            cameras.append(result)
                    except Exception as e:
                        logger.debug(f"Port scan error: {e}")
                        
        except Exception as e:
            logger.error(f"Port scan discovery failed: {e}")
            
        return cameras

    def _check_camera_port(self, ip: str, port: int) -> Optional[CameraInfo]:
        """Check if a specific IP:port combination is a camera"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(2)
            result = sock.connect_ex((ip, port))
            sock.close()
            
            if result == 0:
                # Port is open, try to identify if it's a camera
                if self._is_camera_service(ip, port):
                    return CameraInfo(
                        ip_address=ip,
                        port=port,
                        manufacturer="Unknown",
                        model="Unknown",
                        firmware_version="Unknown",
                        stream_urls=[],
                        onvif_supported=False,
                        device_service_url="",
                        media_service_url=""
                    )
        except Exception:
            pass
        
        return None

    def _is_camera_service(self, ip: str, port: int) -> bool:
        """Check if the service at IP:port is likely a camera"""
        try:
            # Try common camera endpoints
            camera_endpoints = [
                f"http://{ip}:{port}/",
                f"http://{ip}:{port}/web/",
                f"http://{ip}:{port}/cgi-bin/",
                f"http://{ip}:{port}/onvif/device_service"
            ]
            
            for endpoint in camera_endpoints:
                try:
                    response = requests.get(endpoint, timeout=3)
                    content = response.text.lower()
                    
                    # Look for camera-related keywords
                    camera_keywords = [
                        'camera', 'video', 'stream', 'onvif', 'rtsp',
                        'surveillance', 'security', 'axis', 'hikvision',
                        'dahua', 'bosch', 'sony', 'panasonic'
                    ]
                    
                    if any(keyword in content for keyword in camera_keywords):
                        return True
                        
                except requests.RequestException:
                    continue
                    
        except Exception:
            pass
        
        return False

    def _parse_onvif_response(self, response: str, ip: str) -> Optional[CameraInfo]:
        """Parse ONVIF WS-Discovery response"""
        try:
            root = ET.fromstring(response)
            
            # Extract device service URL
            device_service_url = ""
            for elem in root.iter():
                if 'XAddrs' in elem.tag:
                    device_service_url = elem.text
                    break
            
            if device_service_url:
                return CameraInfo(
                    ip_address=ip,
                    port=80,  # Default HTTP port
                    manufacturer="Unknown",
                    model="Unknown",
                    firmware_version="Unknown",
                    stream_urls=[],
                    onvif_supported=True,
                    device_service_url=device_service_url,
                    media_service_url=""
                )
                
        except Exception as e:
            logger.debug(f"Failed to parse ONVIF response: {e}")
        
        return None

    def _merge_camera_lists(self, onvif_cameras: List[CameraInfo], port_scan_cameras: List[CameraInfo]) -> List[CameraInfo]:
        """Merge and deduplicate camera lists"""
        merged = {}
        
        # Add ONVIF cameras (higher priority)
        for camera in onvif_cameras:
            merged[camera.ip_address] = camera
        
        # Add port scan cameras if not already found
        for camera in port_scan_cameras:
            if camera.ip_address not in merged:
                merged[camera.ip_address] = camera
        
        return list(merged.values())

    async def _get_camera_details(self, cameras: List[CameraInfo]) -> List[CameraInfo]:
        """Get detailed information for discovered cameras"""
        detailed_cameras = []
        
        for camera in cameras:
            try:
                if camera.onvif_supported:
                    detailed_camera = await self._get_onvif_details(camera)
                else:
                    detailed_camera = await self._get_http_details(camera)
                
                detailed_cameras.append(detailed_camera)
                
            except Exception as e:
                logger.debug(f"Failed to get details for camera {camera.ip_address}: {e}")
                # Add camera with basic info
                detailed_cameras.append(camera)
        
        return detailed_cameras

    async def _get_onvif_details(self, camera: CameraInfo) -> CameraInfo:
        """Get detailed information via ONVIF"""
        try:
            # Get device information
            device_info = await self._get_onvif_device_info(camera)
            if device_info:
                camera.manufacturer = device_info.get('manufacturer', 'Unknown')
                camera.model = device_info.get('model', 'Unknown')
                camera.firmware_version = device_info.get('firmware', 'Unknown')
            
            # Get media profiles and stream URLs
            stream_urls = await self._get_onvif_stream_urls(camera)
            camera.stream_urls = stream_urls
            
        except Exception as e:
            logger.debug(f"Failed to get ONVIF details for {camera.ip_address}: {e}")
        
        return camera

    async def _get_onvif_device_info(self, camera: CameraInfo) -> Optional[Dict]:
        """Get device information via ONVIF GetDeviceInformation"""
        try:
            # This is a simplified implementation
            # In a real implementation, you would use proper ONVIF SOAP calls
            device_info_url = f"{camera.device_service_url}/GetDeviceInformation"
            
            soap_body = """<?xml version="1.0" encoding="UTF-8"?>
<soap:Envelope xmlns:soap="http://www.w3.org/2003/05/soap-envelope">
    <soap:Body>
        <tds:GetDeviceInformation xmlns:tds="http://www.onvif.org/ver10/device/wsdl"/>
    </soap:Body>
</soap:Envelope>"""
            
            response = requests.post(
                device_info_url,
                data=soap_body,
                headers={'Content-Type': 'application/soap+xml'},
                timeout=5
            )
            
            if response.status_code == 200:
                # Parse response (simplified)
                return {
                    'manufacturer': 'ONVIF Camera',
                    'model': 'Unknown Model',
                    'firmware': 'Unknown Version'
                }
                
        except Exception as e:
            logger.debug(f"Failed to get ONVIF device info: {e}")
        
        return None

    async def _get_onvif_stream_urls(self, camera: CameraInfo) -> List[str]:
        """Get stream URLs via ONVIF GetProfiles"""
        try:
            # Simplified implementation
            # In reality, you would get media profiles and extract stream URIs
            return [
                f"rtsp://{camera.ip_address}:554/stream1",
                f"rtsp://{camera.ip_address}:554/stream2"
            ]
        except Exception:
            return []

    async def _get_http_details(self, camera: CameraInfo) -> CameraInfo:
        """Get camera details via HTTP requests"""
        try:
            # Try to get camera information from common endpoints
            base_url = f"http://{camera.ip_address}:{camera.port}"
            
            # Try different manufacturer-specific endpoints
            endpoints = [
                "/cgi-bin/param.cgi?action=list&group=System",  # Dahua
                "/ISAPI/System/deviceInfo",  # Hikvision
                "/axis-cgi/param.cgi?action=list&group=root.Brand",  # Axis
            ]
            
            for endpoint in endpoints:
                try:
                    response = requests.get(f"{base_url}{endpoint}", timeout=3)
                    if response.status_code == 200:
                        # Parse manufacturer-specific response
                        # This is simplified - real implementation would parse each format
                        camera.manufacturer = "HTTP Camera"
                        camera.model = "Unknown Model"
                        break
                except requests.RequestException:
                    continue
            
            # Try to discover stream URLs
            camera.stream_urls = await self._discover_stream_urls(camera)
            
        except Exception as e:
            logger.debug(f"Failed to get HTTP details for {camera.ip_address}: {e}")
        
        return camera

    async def _discover_stream_urls(self, camera: CameraInfo) -> List[str]:
        """Discover stream URLs for the camera"""
        stream_urls = []
        
        # Common RTSP stream paths
        rtsp_paths = [
            "/stream1", "/stream2", "/live", "/ch01", "/ch02",
            "/av0_0", "/av0_1", "/h264", "/mjpeg"
        ]
        
        for path in rtsp_paths:
            stream_url = f"rtsp://{camera.ip_address}:554{path}"
            stream_urls.append(stream_url)
        
        # HTTP stream URLs
        http_paths = [
            "/video.cgi", "/mjpeg", "/stream.mjpeg", "/videostream.cgi"
        ]
        
        for path in http_paths:
            stream_url = f"http://{camera.ip_address}:{camera.port}{path}"
            stream_urls.append(stream_url)
        
        return stream_urls

    def get_discovered_cameras(self) -> List[CameraInfo]:
        """Get list of discovered cameras"""
        return self.discovered_cameras

# Convenience function for quick discovery
async def discover_cameras_on_network(network_range: str = "192.168.1.0/24", timeout: int = 5) -> List[CameraInfo]:
    """
    Convenience function to discover cameras on the network
    
    Args:
        network_range: Network range to scan (CIDR notation)
        timeout: Discovery timeout in seconds
        
    Returns:
        List of discovered camera information
    """
    discovery = ONVIFCameraDiscovery(timeout=timeout)
    return await discovery.discover_cameras(network_range)