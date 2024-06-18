#!/usr/bin/python

from ansible.module_utils.basic import AnsibleModule
import os
import yaml
import glob

BASE_PATH="/opt/configuration"
def gather_keys() -> list[dict[str,str]]:
    try:
        os.chdir(BASE_PATH)
    except Exception as e:
        print(f"Error: {e}")
        exit(1)

    found_keys: dict[str,str] = {}
    for file_path in sorted(glob.iglob('**/ceph.*.keyring', recursive=True)):
        with open(file_path, 'r') as f_in:
            found_keys[file_path] =  f_in.read()
    return [ { "path": x, "content" : y } for x,y in sorted(found_keys.items()) ]


def run_module():
    module_args = dict(
        target=dict(type='str', required=True),
        state=dict(type='str', required=False, default='present', choices=['present', 'absent'])
    )

    result = dict(
        changed=False,
        original_message='',
        message=''
    )

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True
    )

    target = module.params['target']
    state = module.params['state']

    if state == 'present':
        content = yaml.dump({ "collected_ceph_keys": gather_keys() })
        if not os.path.exists(target) or open(target).read() != content:
            result['changed'] = True
            if not module.check_mode:
                previous_umask = os.umask(0o077)
                with open(target, 'w') as f:
                    f.write(content)
                os.umask(previous_umask)
            result['message'] = f"File {target} created with content."
        else:
            result['message'] = f"File {target} already exists with the same content."
    elif state == 'absent':
        if os.path.exists(target):
            result['changed'] = True
            if not module.check_mode:
                os.remove(target)
            result['message'] = f"File {target} removed."
        else:
            result['message'] = f"File {target} does not exist."

    if module.check_mode:
        module.exit_json(**result)

    module.exit_json(**result)

def main():
    run_module()

if __name__ == '__main__':
    main()

