import os
from pathlib import Path
import re
import subprocess
from typing import List, Optional

from adb_shell.adb_device import AdbDeviceTcp
from adb_shell.auth.sign_pythonrsa import PythonRSASigner
import click

from .port_checker import PortChecker

class Device:
    ARP_EXTRACTOR = re.compile(r"^\? \((\d+.\d+.\d+.\d+)\) .*")
    @classmethod
    def _get_arp_hosts_from_cache(cls) -> List[str]:
        proc = subprocess.run(["/usr/sbin/arp", "-n", "-a"], shell=False, capture_output=True, encoding="utf8")
        output = proc.stdout
        ret = []
        for line in output.split("\n"):
            matches = cls.ARP_EXTRACTOR.match(line)
            if matches is not None:
                ret.append(matches.group(1))
        return ret

    @classmethod
    def scan(cls, use_cache: bool = True) -> List["Device"]:
        # Collect a bunch of hosts.
        if use_cache:
            hosts = cls._get_arp_hosts_from_cache()
        else:
            from .scanner import full_scan
            hosts = full_scan()

        available = PortChecker().filter(hosts)
        ret = []
        for host in available:
            device = cls._create(host)
            if device is not None:
                ret.append(device)

        return ret
    
    ADB_PORT = 5555
    SOCKET_TIMEOUT = 2

    _signer: Optional[PythonRSASigner] = None
    @classmethod
    def _get_signer(cls) -> PythonRSASigner:
        if cls._signer is None:
            android_dir = Path.home() / ".android"
            adbkey_path = android_dir / "adbkey"
            adbkey_pub_path = android_dir / "adbkey.pub"
            if not os.path.isfile(adbkey_path) or not os.path.isfile(adbkey_pub_path):
                raise click.UsageError("adb key not found. Please ensure you have used adb before.")
            with open(adbkey_path, "rb") as f:
                priv = f.read()
            with open(adbkey_pub_path, "rb") as f:
                pub = f.read()
            cls._signer = PythonRSASigner(pub, priv)
        return cls._signer

    @classmethod
    def _create(cls, ip: str) -> Optional["Device"]:
        try:
            dev = AdbDeviceTcp(ip, cls.ADB_PORT, default_transport_timeout_s=9.)
            dev.connect(rsa_keys=[cls._get_signer()], auth_timeout_s=0.1)
            serial_num = dev.shell("getprop ro.serialno").strip()
            fingerprint = dev.shell("getprop ro.build.fingerprint").strip()
            return cls(ip, serial_num, fingerprint)
        except Exception as ex:
            print(ex)
            return None
    
    @classmethod
    def create(cls, ip: str) -> Optional["Device"]:
        if not PortChecker.check(ip, cls.ADB_PORT):
            return None
        return cls._create(ip)

    def __init__(self, ip: str, serial_num: str, fingerprint: str):
        self._ip = ip
        self._serial_num = serial_num
        self._fingerprint = fingerprint
        self._dev: AdbDeviceTcp = None


    def close(self):
        if self._dev is not None:
            self._dev.close()
            self._dev = None


    @property
    def ip(self):
        return self._ip
    
    @property
    def serial_num(self):
        return self._serial_num
    
    @property
    def fingerprint(self):
        return self._fingerprint
    
    def _get_dev(self) -> AdbDeviceTcp:
        if self._dev is None:
            dev = self._dev = AdbDeviceTcp(self._ip, self.ADB_PORT, default_transport_timeout_s=9.)
            dev.connect(rsa_keys=[self._get_signer()], auth_timeout_s=0.1)
        return self._dev
    
    def start(self, package_name: str):
        dev = self._get_dev()
        dev.shell(f"monkey -p {package_name} 1")

    def kill(self, package_name: str):
        dev = self._get_dev()
        dev.shell(f"am force-stop {package_name}")
