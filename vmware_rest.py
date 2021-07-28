#!/usr/bin/python

from __future__ import absolute_import, division, print_function
from ansible.module_utils.basic import AnsibleModule
import requests
import logging
import json

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

    def create_vm(self):
        pass

    def get_ip(self):
        pass

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
            pass

        return vm_id[0]

    def delete_vm(self):
        pass

    def vm_power_state(self, state):
        pass

    # ?
    def export(self): # ?
        pass # ?
    # ?


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
