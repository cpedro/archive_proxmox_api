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

from pve import api
from signal import signal, SIGINT


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

    for vm in api.getvms(args.host, user=args.username, password=password,
                         verify_ssl=False):
        print(vmout.format(vm['vmid'], vm['name'], vm['status'], vm['cpus'],
                           vm['maxmem']))
        for disk in vm['disks']:
            print(diskout.format(disk['volid'], disk['size']))


if __name__ == '__main__':
    signal(SIGINT, handler)
    sys.exit(main(sys.argv[1:]))

