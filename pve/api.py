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


def dedup(dict, id):
    """Quick and dirty function to dedup the lists of dictionaries based on an
    id to determine whether or not an item has been 'seen'
    """
    seen = set()
    dedup = []

    for d in dict:
        if d[id] not in seen:
            seen.add(d[id])
            dedup.append(d)

    return dedup


def create_vm(host, node, vm, *args, **kwargs):
    """Creates and sets up a VM on the PVE cluster.
    """
    pve = ProxmoxAPI(host, *args, **kwargs)
    pve.nodes(node).qemu.create(**vm)
    return


def get_ha_groups(host, *args, **kwargs):
    """Get and returns all HA groups on the PVE cluster, along with resources.
    """
    pve = ProxmoxAPI(host, *args, **kwargs)
    groups = pve.cluster.ha.groups.get()
    resources = pve.cluster.ha.resources.get()

    for group in groups:
        group_resources = []
        for resource in resources:
            if resource['group'] == group['group']:
                group_resources.append(resource)
        group['resources'] = group_resources

    return groups


def get_nodes(host, *args, **kwargs):
    """Get and returns a list of all nodes on the PVE cluster.
    """
    pve = ProxmoxAPI(host, *args, **kwargs)
    nodes = pve.nodes.get()
    # Add to this list to get more info on node.
    properties = ['network', 'services']

    for node in nodes:
        for p in properties:
            node[p] = pve.nodes(node['node']).get(p)

    return nodes


def get_storage(host, *args, **kwargs):
    """Get and returns a list of all storage active on the PVE cluster.
    """
    pve = ProxmoxAPI(host, *args, **kwargs)
    storage = []
    seen = set()

    for node in pve.nodes.get():
        for ds in pve.nodes(node['node']).get('storage'):
            if ds['shared'] != 1:
                ds['node'] = node['node']
            elif ds['storage'] in seen:
                continue
            else:
                seen.add(ds['storage'])

            ds['contents'] = pve.nodes(
                node['node']).storage(ds['storage']).get('content')
            storage.append(ds)

    return storage


def get_vms_slow(host, *args, **kwargs):
    """Get and returns a list of all VMs on the PVE cluster, including disks.
    DON'T USE!  This is for reference only.  It's slow as hell.  About 10 times
    slower.
    """
    pve = ProxmoxAPI(host, *args, **kwargs)
    vms = []

    for node in pve.nodes.get():
        storage = pve.nodes(node['node']).get('storage', content='images')
        for vm in pve.nodes(node['node']).get('qemu'):
            vmdisks = []
            for ds in storage:
                vmdisks.extend(
                    pve.nodes(node['node']).storage(ds['storage']).get(
                        'content', vmid=vm['vmid']))
            vm['disks'] = vmdisks
            vms.append(vm)

    return vms


def get_vms(host, *args, **kwargs):
    """Get and returns a list of all VMs on the PVE cluster, including disks.
    """
    pve = ProxmoxAPI(host, *args, **kwargs)
    vms = []
    all_disks = []

    for node in pve.nodes.get():
        vms.extend(pve.nodes(node['node']).get('qemu'))
        # Loop through storage with content = images only.
        for ds in pve.nodes(node['node']).get('storage', content='images'):
            all_disks.extend(
                pve.nodes(node['node']).storage(ds['storage']).get('content'))
    all_disks = dedup(all_disks, 'volid')

    for vm in vms:
        vmdisks = []
        for disk in all_disks:
            if int(disk['vmid']) == int(vm['vmid']):
                vmdisks.append(disk)
        vm['disks'] = vmdisks

    return vms

