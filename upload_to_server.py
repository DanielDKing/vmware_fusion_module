#!/usr/bin/python

from __future__ import absolute_import, division, print_function
from ansible.module_utils.basic import AnsibleModule
import logging
import subprocess
import time
from vmware_rest import VMwareFusion

__metaclass__ = type

DOCUMENTATION = r'''
---
module: vmware_rest
short_description: Manages virtual machines in VMware Fusion
description: >
   This module can be used to create new virtual machines fromother virtual machines,
   manage power state of virtual machine such as power on, power off, reboot,etc.,
   remove a virtual machine with associated components.
requirements:
- python >= 2.6
- ovftool
'''

EXAMPLES = r'''
# Export VM to vcenter

- name: "upload vm to server"
  upload_to_server:
    hostname: "{{ vcenter_hostname }}"
    username: "{{ vcenter_username }}"
    password: "{{ vcenter_password }}"
    fusion_hostname: "{{ fusion_hostname }}"
    fusion_username: "{{ fusion_username }}"
    fusion_password: "{{ fusion_password }}"
    name: "{{ name }}"
    datacenter: "{{ vcenter_datacenter }}"
    cluster: "{{ vcenter_cluster }}"
    datastore: "{{ datastore }}"
    network: "{{ network }}"
    disk_mode: "{{ disk_mode }}"
'''


def export(name, vc_user, vc_pass, vc_host, datacenter, cluster, datastore, network, disk_mode, port, fusion_host,
           fusion_user, fusion_pass):
    fusion_api = VMwareFusion(hostname=fusion_host, password=fusion_pass, username=fusion_user)
    vmx_path = fusion_api.name_to_path(name)
    output = subprocess.run(["ovftool", "--acceptAllEulas", f"--datastore={datastore}", f"--net:'bridged'={network}",
                       "--X:logFile=/tmp/ovftool-log.txt", "--X:logLevel=verbose", f"diskMode={disk_mode}",
                       f"--name={name}", vmx_path, f"vi://{vc_user}:{vc_pass}@{vc_host}:{port}/{datacenter}/{cluster}"],
                       capture_output=True, shell=True)
    print(output)
    return 0


def main():
    module = AnsibleModule(
        argument_spec=dict(
            name=dict(required=True, default=None, type=str),
            fusion_hostname=dict(required=True, type=str),
            fusion_username=dict(required=True, type=str),
            fusion_password=dict(required=True, type=str),
            hostname=dict(required=True, type=str),
            username=dict(required=True, type=str),
            password=dict(required=True, type=str),
            datacenter=dict(required=True, type=str),
            cluster=dict(required=True, type=str),
            datastore=dict(required=True, type=str),
            network=dict(required=True, type=str),
            disk_mode=dict(default="thin", required=False, type=str),
            port=dict(defaukt=443, required=False, type=int),
        )
    )

    params = module.params
    name = params["name"]
    hostname = params["hostname"]
    username = params["username"]
    password = params["password"]
    fusion_hostname = params["fusion_hostname"]
    fusion_username = params["fusion_username"]
    fusion_password = params["fusion_password"]
    datacenter = params["datacenter"]
    cluster = params["cluster"]
    datastore = params["datastore"]
    network = params["network"]
    disk_mode = params["disk_mode"]
    port = params["port"]

    result = export(name=name, vc_user=username, vc_pass=password, vc_host=hostname, datacenter=datacenter,
                    cluster=cluster, datastore=datastore, network=network, disk_mode=disk_mode, port=str(port),
                    fusion_host=fusion_hostname, fusion_pass=fusion_password, fusion_user=fusion_username)

    if result:
        module.exit_json(**result)
    else:
        module.fail_json(msg="Failed")


if __name__ == '__main__':
    main()
