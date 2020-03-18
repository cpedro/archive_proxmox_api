#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
File: api_calls.py
Description: List VMs running on Proxmox VE cluster.

Author: E. Chris Pedro
Created: 2020-03-17


usage: api_calls.py [-h] -H HOST -u USERNAME [-p PASSWORD] [-r] [-v] [-n] [-s]

Proxmox API Test Program

optional arguments:
  -h, --help            show this help message and exit
  -H HOST, --host HOST  Proxmox Host to connect to.
  -u USERNAME, --username USERNAME
                        Username to use to authenticate.
  -p PASSWORD, --password PASSWORD
                        Password, leave blank to be prompted to enter your
                        password
  -r, --show-raw        Show raw output as JSON instead of formatted output.
  -v, --list-vms        List all virtual machines and their disks.
  -n, --list-nodes      List all nodes.
  -s, --list-storage    List all storage.


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
import json
import sys

from pve import api
from signal import signal, SIGINT


def list_storage(host, username, password, show_raw):
    storage = api.get_storage(
        host, user=username, password=password, verify_ssl=False)
    if show_raw:
        print(json.dumps(storage))
        return

    output = """{}:
    type: {}
    content: {}
    shared: {}
    size: {}
    used: {:.1%}"""

    for ds in storage:
        print(output.format(
            ds['storage'], ds['type'], ds['content'], ds['shared'],
            ds['total'], ds['used_fraction']))


def list_nodes(host, username, password, show_raw):
    nodes = api.get_nodes(
        host, user=username, password=password, verify_ssl=False)

    if show_raw:
        print(json.dumps(nodes))
        return

    output = """{}:
    status: {}
    cpu: {:.1%}
    memory: {:.1%}"""

    for node in nodes:
        print(output.format(
            node['node'], node['status'], node['cpu'],
            node['mem'] / node['maxmem']))


def list_vms(host, username, password, show_raw):
    vms = api.get_vms(
        host, user=username, password=password, verify_ssl=False)

    if show_raw:
        print(json.dumps(vms))
        return

    vmout = """{}:
    name: {}
    status: {}
    cpu: {}
    memory: {}
    disks:"""
    diskout = """        {}:
            size: {}"""

    for vm in vms:
        print(vmout.format(
            vm['vmid'], vm['name'], vm['status'], vm['cpus'], vm['maxmem']))
        for disk in vm['disks']:
            print(diskout.format(disk['volid'], disk['size']))


def parse_args(args):
    """Parse command line arguments.
    """
    parser = argparse.ArgumentParser(
        description='Proxmox API Test Program')
    parser.add_argument(
        '-H', '--host', required=True, help='Proxmox Host to connect to.')
    parser.add_argument(
        '-u', '--username', required=True,
        help='Username to use to authenticate.')
    parser.add_argument(
        '-p', '--password', default='',
        help='Password, leave blank to be prompted to enter your password')
    parser.add_argument(
        '-r', '--show-raw', action='store_true',
        help='Show raw output as JSON instead of formatted output.')
    parser.add_argument(
        '-v', '--list-vms', action='store_true',
        help='List all virtual machines and their disks.')
    parser.add_argument(
        '-n', '--list-nodes', action='store_true', help='List all nodes.')
    parser.add_argument(
        '-s', '--list-storage', action='store_true', help='List all storage.')
    return parser.parse_args(args)


def handler(signal_received, frame):
    """Signal handler.
    """
    sys.exit(0)


def main(args):
    """Main method.
    """
    args = parse_args(args)

    if sys.stdin.isatty() and len(args.password) == 0:
        try:
            password = getpass.getpass('Enter Password: ')
        # Catch Ctrl-D
        except EOFError:
            return 0
    else:
        password = args.password

    if args.list_vms:
        list_vms(args.host, args.username, password, args.show_raw)
    if args.list_nodes:
        list_nodes(args.host, args.username, password, args.show_raw)
    if args.list_storage:
        list_storage(args.host, args.username, password, args.show_raw)


if __name__ == '__main__':
    signal(SIGINT, handler)
    sys.exit(main(sys.argv[1:]))

