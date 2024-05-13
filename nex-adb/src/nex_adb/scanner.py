# This is a full scanner using scapy.
# Normally, we would be delegating to using the arp cache.

import os
from typing import Dict, List

import click

import logging

scapy_logger = logging.getLogger("scapy.runtime")
scapy_logger.level = logging.ERROR
from scapy.all import conf, Ether, ARP, srp

scapy_logger.level = logging.WARNING


def _get_broadcast_addresses() -> Dict[str, str]:
    conf.route.resync()
    best = {}
    for t in conf.route.routes:
        if t[4] == "127.0.0.1":  # Skip all localhost loopback.
            continue
        net = t[0]
        mask = t[1]
        if net == 0 or mask == 0:
            continue
        ip_addr = sum(
            int(com) * (256 ** (3 - idx)) for idx, com in enumerate(t[4].split("."))
        )
        if (ip_addr & mask) != (net & mask):
            continue
        # Find the one that has minimum mask.
        iface = t[3]
        if iface not in best or best[iface][1] > mask:
            best[iface] = (net, mask)
    addresses = {}
    for iface, (net, mask) in best.items():
        chunks = [0] * 4
        for i in range(4):
            chunks[3 - i] = str(net % 256)
            net //= 256
        addresses[iface] = f"{'.'.join(chunks)}/{mask.bit_count()}"
    return addresses


def _arp_scan(address) -> List[str]:
    # Prepare the ARP request.
    packet = Ether(dst="ff:ff:ff:ff:ff:ff") / ARP(pdst=address)

    template_prefix = bytes(packet)[:-4]

    def fast_bytes(self):
        return template_prefix + bytes(int(v) for v in self.payload.pdst.split("."))

    backup = Ether.__bytes__
    Ether.__bytes__ = fast_bytes

    # Send the packet and receive the answer.
    answered, unanswered = srp(packet, timeout=4, verbose=0, retry=2, inter=0.002)

    Ether.__bytes__ = backup

    # List to hold the live hosts.
    live_hosts = []

    for sent, received in answered:
        # For each response, append IP and MAC address to the list
        live_hosts.append(received.psrc)

    return live_hosts


BROADCAST_ENDPOINT = "/dev/bpf0"


def full_scan() -> List[str]:
    # First check if /dev/bpf0 is accessible or not.
    if not os.access(BROADCAST_ENDPOINT, os.R_OK | os.W_OK):
        click.echo("Enable to access broadcast device for auto-discovery.", err=True)
        click.echo(
            f"Please consider running sudo chown {os.getlogin()}:staff {BROADCAST_ENDPOINT}"
        )
        raise click.UsageError("Permission error to broadcast devices.")
    addresses = _get_broadcast_addresses()
    ret = []
    for iface, address in addresses.items():
        click.echo(f"Scanning {iface} {address}")
        hosts = _arp_scan(address)
        for host in hosts:
            ret.append(host)
    click.echo(f"Collected {len(ret)} hosts.")
    return ret
