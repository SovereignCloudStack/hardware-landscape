import requests

# URL of the .ini file
url = "https://raw.githubusercontent.com/sonic-net/sonic-buildimage/master/device/accton/x86_64-accton_as4630_54te-r0/Accton-AS4630-54TE/port_config.ini"

response = requests.get(url)
response.raise_for_status()
ini_content = response.text

ports = {}

lines = ini_content.strip().split('\n')
for line in lines:
    # Skip comment or empty lines
    if line.startswith('#') or not line.strip():
        continue

    # Split the line into components and skip lines that don't have enough parts
    parts = line.split()
    if len(parts) < 6:
        continue

    # Extract port details
    name, lanes, alias, index, speed, autoneg = parts[:6]

    ports[name] = {
        "admin_status": "up",  # Assuming default admin_status as "up"
        "alias": alias,
        "autoneg": autoneg,
        "index": index,
        "lanes": lanes,
        "mtu": "9100",  # Assuming default MTU
        "parent_port": name,  # Assuming parent port is the same
        "speed": speed
    }

result = {
    "ports": ports
}

import pprint
pprint.pprint(result)
