#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
File: pve/api.py
Description: Wrapper around proxmoxer library to do common Proxmox tasks.

Author: E. Chris Pedro
Created: 2020-03-17


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


from proxmoxer import ProxmoxAPI


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

