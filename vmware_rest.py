#!/usr/bin/python

from __future__ import absolute_import, division, print_function
from ansible.module_utils.basic import AnsibleModule
import requests
import logging
import json
import os
import shutil
import time

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
'''

VALID_STATES = ["present", "absent", "poweredoff", "poweredon"]


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
                res = requests.post(f"{self.__host}/vms", data={"name": name, "parentId": parent_id},
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
                for i in range(60):
                    res = requests.get(f"{self.__host}/vms/{vm_id}", headers={"Content-Type":
                                       "application/vnd.vmware.vmw.rest-v1+json"},
                                       auth=(self.__username, self.__password))
                    time.sleep(5)

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
            vm_id = [i.id for i in vms if name in i.path]
        else:
            logging.error("Failed to find VM")
            return None

        return vm_id[0]

    def name_to_path(self, name):
        vms = self.get_all_vms()

        if vms:
            vm_path = [i.path for i in vms if name in i.path]
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

    # ?
    def export(self): # ?
        pass # ?
    # ?


def manage_vmware_fusion():
    pass


def main():
    module_args = dict(
        name=dict(type='str', required=True),
        hostname=dict(type='str', required=True),
        username=dict(type='str', required=True),
        password=dict(type='str', required=True),
        template=dict(type='str', required=True),
        state=dict(type='str', required=True),
    )

    result = dict(
        changed=False,
        original_message='',
        message='',
        my_useful_info={},
    )

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True
    )

    result['original_message'] = module.params['name']
    result['message'] = 'goodbye'
    result['my_useful_info'] = {
        'foo': 'bar',
        'answer': 42,
    }

    module.exit_json(**result)


if __name__ == '__main__':
    main()
