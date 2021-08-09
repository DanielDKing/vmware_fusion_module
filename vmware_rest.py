#!/usr/bin/python

from __future__ import absolute_import, division, print_function
from ansible.module_utils.basic import AnsibleModule
import requests
import logging
import json
import os
import shutil
import time
import re
import subprocess

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
- requests
'''

EXAMPLES = r'''
# create vm
- name: "Create vm"
  vmware_rest:
    hostname: "{{ fusion_hostname }}"
    username: "{{ fusion_username }}"
    password: "{{ fusion_password }}"
    name: "{{ vm_name }}"
    template: "{{ template }}"
    state: "{{ state }}"
    
- name: "Create vm"
  vmware_rest:
    hostname: "{{ fusion_hostname }}"
    username: "{{ fusion_username }}"
    password: "{{ fusion_password }}"
    name: "{{ vm_name }}"
    template: "{{ template }}"
    state: "{{ state }}"
    export:
      hostname: "{{ vcenter_hostname }}"
      username: "{{ vcenter_username }}"
      password: "{{ vcenter_password }}"
      datacenter: "{{ vcenter_datacenter }}"
      cluster: "{{ vcenter_cluster }}"
      datastore: "{{ datastore }}"
      network: "{{ network }}"
      
'''

VALID_STATES = ["present", "absent", "poweredoff", "poweredon"]
POWER_STATES = ["poweredoff", "poweredon"]


class VMwareFusion:
    def __init__(self, hostname, username, password):
        self.__host = f"http://{hostname}:8697/api"
        self.__username = username
        self.__password = password

    def create_vm(self, name, template):
        logging.info(f"Creating VM {name}")
        parent_id = self.name_to_id(template)

        if parent_id:
            try:
                res = requests.post(f"{self.__host}/vms", json={"name": name, "parentId": parent_id},
                                    headers={"Content-Type": "application/vnd.vmware.vmw.rest-v1+json"},
                                    auth=(self.__username, self.__password))
                if res.status_code == 201:
                    return res.json()["id"]
                else:
                    raise Exception(res.text)
            except Exception as e:
                logging.error(f"Failed to create VM {name}.", e)
        return None

    def get_ip(self, name, vm_id=None):
        if not vm_id:
            vm_id = self.name_to_id(name=name)

        if vm_id:
            try:
                for i in range(30):
                    res = requests.get(f"{self.__host}/vms/{vm_id}/ip", headers={"Content-Type":
                                       "application/vnd.vmware.vmw.rest-v1+json"},
                                       auth=(self.__username, self.__password))
                    try:
                        if re.match("\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$", res.json()["ip"]):
                            break
                    except:
                        time.sleep(10)

                return res.json()["ip"]
            except Exception as e:
                logging.error(f"Failed to retrieve ip from {name}.", res.text, e)

        return None

    def get_all_vms(self):
        try:
            res = requests.get(f"{self.__host}/vms", auth=(self.__username, self.__password))
            vms = json.loads(res.content)
        except Exception as e:
            logging.error('Error while getting vms list.', e)
            return None

        return vms

    def name_to_id(self, name):
        vms = self.get_all_vms()

        if vms:
            vm_id = [i["id"] for i in vms if name in i["path"]]
        else:
            logging.error("Failed to find VM")
            return None

        return None if not vm_id else vm_id[0]

    def name_to_path(self, name):
        vms = self.get_all_vms()

        if vms:
            vm_path = [i["path"] for i in vms if name in i["path"]]
        else:
            logging.error("Failed to find VM")
            return None

        return vm_path[0]

    def delete_vm(self, name, vm_id=None):
        if not vm_id:
            vm_id = self.name_to_id(name)

        if vm_id:
            try:
                vm_path = self.name_to_path(name)
                res = requests.delete(f"{self.__host}/vms/{vm_id}", headers={"Content-Type":
                                      "application/vnd.vmware.vmw.rest-v1+json"},
                                      auth=(self.__username, self.__password))
                if res.status_code == 204:
                    logging.info("VM DELETED:", name)
                    vm_folder = os.path.join("/", *vm_path.split("/")[1:-1])
                    try:
                        shutil.rmtree(vm_folder)
                    except FileNotFoundError as e:
                        logging.info("VM's directory already deleted", e)
                    except Exception as e:
                        logging.error("Error while deleting VM's directory", e)
                        return None

                    return "OK"
                else:
                    logging.error("")
                    return None
            except Exception as e:
                logging.error("Failed to delete vm.", name, e)
                return None
        else:
            logging.error("Failed to achieve vm id.", name)
            return None

    def vm_power_state(self, name, state, vm_id=None):
        if not vm_id:
            vm_id = self.name_to_id()

        if vm_id:
            try:
                print(state)
                print(f"{self.__host}/vms/{vm_id}/power")
                res = requests.put(f"{self.__host}/vms/{vm_id}/power", data=state, headers={"Content-Type":
                                   "application/vnd.vmware.vmw.rest-v1+json"}, auth=(self.__username, self.__password))
                power_state = json.loads(res.content)
            except Exception as e:
                logging.error("Failed to change vm power state.", name, e)
                return None
        else:
            logging.error("Failed to achieve vm id.", name)
            return None

        return power_state

    def restart_vm(self, name, vm_id=None):
        if self.vm_power_state(name, "off", vm_id):
            if self.vm_power_state(name, "on", vm_id):
                return "Restarted"
        else:
            logging.error("Failed to restart VM")
            return None

    def export(self, name, vc_user, vc_pass, vc_host, datastore, network, vm_id=None):
        pass


def manage_vmware_fusion(name, hostname, username, password, template, state):
    fusion_api = VMwareFusion(hostname=hostname, username=username, password=password)

    vm_id = fusion_api.name_to_id(name)

    if state in POWER_STATES + ["present"]:
        if not vm_id:
            vm_id = fusion_api.create_vm(name=name, template=template)
        if state in POWER_STATES:
            new_state = fusion_api.vm_power_state(name=name, state=state.split("powered")[-1], vm_id=vm_id)

            if not new_state:
                logging.error("Failed to change power state of VM,", name)
                return None
        if state == "poweredon":
            vm_ip = fusion_api.get_ip(name=name, vm_id=vm_id)
            if not vm_ip:
                fusion_api.restart_vm(name=name, vm_id=vm_id)
                vm_ip = fusion_api.get_ip(name=name, vm_id=vm_id)
            return {"ip": vm_ip}
        else:
            return {"msg": "200 OK"}
    else:  # state == absent
        new_state = fusion_api.vm_power_state(name=name, state="off", vm_id=vm_id)

        if not new_state:
            logging.error(f"Failed to change power state of VM= {name}")
            return None

        time.sleep(10)
        delete_result = fusion_api.delete_vm(name=name, vm_id=vm_id)

        if not delete_result:
            logging.error(f"Failed to delete VM={name}")
            return None
        return {"msg": f"Deleted VM={name} successfully"}


def main():
    module = AnsibleModule(
        argument_spec=dict(
            name=dict(required=True, default=None),
            hostname=dict(required=True),
            username=dict(required=True),
            password=dict(required=True),
            template=dict(required=True),
            state=dict(choices=VALID_STATES, default="present", required=False),
            export=dict(type=dict, default={"default": "None"}, required=False),
        )  # ,
        # add_file_common_args=True,
        # supports_check_mode=True
    )

    params = module.params
    name = params["name"]
    hostname = params["hostname"]
    username = params["username"]
    password = params["password"]
    template = params["template"]
    state = params["state"]
    export = params["export"]

    result = manage_vmware_fusion(name, hostname, username, password, template, state, export)

    if result:
        module.exit_json(**result)
    else:
        module.fail_json(msg="Failed")


if __name__ == '__main__':
    main()
