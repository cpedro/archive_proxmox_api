#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
File: list_pve_vms.py
Description: List VMs running on Proxmox VE cluster.

Author: E. Chris Pedro
Created: 2020-03-13


usage: list_pve_vms.py [-h] -H HOST -u USERNAME [-p PASSWORD]

Proxmox List VMs

optional arguments:
  -h, --help            show this help message and exit
  -H HOST, --host HOST
  -u USERNAME, --username USERNAME
  -p PASSWORD, --password PASSWORD


This is free and unencumbered software released into the public domain.

Anyone is free to copy, modify, publish, use, compile, sell, or
distribute this software, either in source code form or as a compiled
binary, for any purpose, commercial or non-commercial, and by any
means.

In jurisdictions that recognize copyright laws, the author or authors
of this software dedicate any and all copyright interest in the
software to the public domain. We make this dedication for the benefit
of the public at large and to the detriment of our heirs and
successors. We intend this dedication to be an overt act of
relinquishment in perpetuity of all present and future rights to this
software under copyright law.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
IN NO EVENT SHALL THE AUTHORS BE LIABLE FOR ANY CLAIM, DAMAGES OR
OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE,
ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
OTHER DEALINGS IN THE SOFTWARE.

For more information, please refer to <http://unlicense.org>
"""


import argparse
import getpass
import sys

from proxmoxer import ProxmoxAPI
from signal import signal, SIGINT


def getvms_slow(host, *args, **kwargs):
    """Get and returns a list of all VMs on the PVE cluster, including disks.
    This is for history only.  It's slow as hell.  About 10 times slower.
    """
    pve = ProxmoxAPI(host, *args, **kwargs)
    vms = []

    for node in pve.nodes.get():
        datastores = pve.nodes(node['node']).get('storage', content='images')
        for vm in pve.nodes(node['node']).get('qemu'):
            vmdisks = []
            for ds in datastores:
                vmdisks.extend(
                    pve.nodes(node['node']).storage(ds['storage']).get(
                        'content', vmid=vm['vmid']))
            vm['disks'] = vmdisks
            vms.append(vm)
    return vms


def getvms(host, *args, **kwargs):
    """Get and returns a list of all VMs on the PVE cluster, including disks.
    """
    pve = ProxmoxAPI(host, *args, **kwargs)
    vms = []
    all_disks = []

    first = True
    for node in pve.nodes.get():
        vms.extend(pve.nodes(node['node']).get('qemu'))
        # Bit of a hack, only get the disk information if it's the first run
        if not first:
            continue
        first = False
        # Loop through storage with content = images only.
        for ds in pve.nodes(node['node']).get('storage', content='images'):
            all_disks.extend(
                pve.nodes(node['node']).storage(ds['storage']).get('content'))

    for vm in vms:
        vmdisks = []
        for disk in all_disks:
            if int(disk['vmid']) == int(vm['vmid']):
                vmdisks.append(disk)
        vm['disks'] = vmdisks

    return vms


def parse_args(args):
    """Parse command line arguments.
    """
    parser = argparse.ArgumentParser(description='Proxmox List VMs')
    parser.add_argument('-H', '--host', dest='host', required=True)
    parser.add_argument('-u', '--username', dest='username', required=True)
    parser.add_argument('-p', '--password', dest='password', default='')
    return parser.parse_args(args)


def handler(signal_received, frame):
    """Signal handler.
    """
    sys.exit(0)


def main(args):
    """Main method.
    """
    args = parse_args(args)

    vmout = """{0}:
    name: {1}
    status: {2}
    cpu: {3}
    memory: {4}
    disks:"""
    diskout = """        {0}:
            size: {1}"""

    if sys.stdin.isatty() and len(args.password) == 0:
        try:
            password = getpass.getpass('Enter Password: ')
        # Catch Ctrl-D
        except EOFError:
            return 0
    else:
        password = args.password

    for vm in getvms(args.host, user=args.username, password=password,
                     verify_ssl=False):
        print(vmout.format(vm['vmid'], vm['name'], vm['status'], vm['cpus'],
                           vm['maxmem']))
        for disk in vm['disks']:
            print(diskout.format(disk['volid'], disk['size']))


if __name__ == '__main__':
    signal(SIGINT, handler)
    sys.exit(main(sys.argv[1:]))

