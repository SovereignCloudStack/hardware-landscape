#!/bin/bash

# This script is designed for use with Zero Touch Provisioning (ZTP) to automatically apply the initial device configuration.
# The device hostname is used as a key to retrieve the SONiC config file from the given NetBox instance.
# The script expects that the device hostname is set beforehand by the DHCP service.
#
# The SONiC configuration file is then applied using the command `config load <sonic-config-file> -y`.
#
# This script is designed to work with SONiC integrated configuration.
#
# Usage: ./provision.sh --netbox-url NETBOX_URL --netbox-token AUTH_TOKEN
#
CONFIG_DIR="/etc/sonic"

# Parse command-line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -u|--netbox-url)
            NETBOX_API="$2"
            shift # past argument
            shift # past value
            ;;
        -t|--netbox-token)
            AUTH_TOKEN="$2"
            shift # past argument
            shift # past value
            ;;
        *)
            echo "Usage: $0 -u NETBOX_URL -t AUTH_TOKEN"
            exit 1
            ;;
    esac
done

# Ensure both NETBOX_API and AUTH_TOKEN are set
if [ -z "$NETBOX_API" ] || [ -z "$AUTH_TOKEN" ]; then
    echo "Error: Both NETBOX_URL and AUTH_TOKEN must be provided."
    echo "Usage: $0 -u NETBOX_URL -t AUTH_TOKEN"
    exit 1
fi

NETBOX_API="${NETBOX_API%/}/api/dcim/devices/"

validate_commands() {
    for cmd in "$@"; do
        if ! command -v "$cmd" &> /dev/null; then
            echo "Error: $cmd is not installed."
            exit 1
        fi
    done
}

validate_commands jq curl

# Hostname should be set beforehand by the DHCP service
HOSTNAME=$(hostname)

echo "Querying NetBox information for device: $HOSTNAME ..."
DEVICE_INFO=$(curl -s -H "Authorization: Token $AUTH_TOKEN" -H "Content-Type: application/json" "${NETBOX_API}?name=${HOSTNAME}")

DEVICE_ID=$(echo "$DEVICE_INFO" | jq -r '.results[0].id')
if [ -z "$DEVICE_ID" ] || [ "$DEVICE_ID" == "null" ]; then
    echo "Error: Device not found in NetBox with hostname '$HOSTNAME'"
    exit 1
fi

echo "Fetching rendered configuration from NetBox for device ID: $DEVICE_ID ..."
CONFIG_RENDERED=$(curl -X POST -s -H "Authorization: Token $AUTH_TOKEN" -H "Content-Type: application/json" "${NETBOX_API}${DEVICE_ID}/render-config/")

CONFIG_JSON_FILENAME="$(date +'%Y-%m-%d_%H-%M-%S').json"

# Extract and save SONiC config
CONFIG=$(echo "$CONFIG_RENDERED" | jq -r '.content')
if [ -n "$CONFIG" ]; then
    echo "Writing SONiC config to temporary directory..."
    echo "$CONFIG" > "$CONFIG_DIR/$CONFIG_JSON_FILENAME"
else
    echo "Error: SONiC config not found in the rendered configuration."
    exit 1
fi

HWSKU=$(echo "$CONFIG" | jq -r '.DEVICE_METADATA.localhost.hwsku')

echo "Generating SONiC base configuration file for device $HWSKU..."
sudo sonic-cfggen  -H --preset l3 -k "$HWSKU" | sudo tee  "$CONFIG_DIR/config_db.json" > /dev/null

echo "Applying SONiC configuration..."
sudo config load "$CONFIG_DIR/$CONFIG_JSON_FILENAME" -y

echo "Saving SONiC configuration to the config_db.json..."
sudo config save -y

echo "Reloading the entire SONiC configuration from the config_db.json..."
sudo config reload -y -f

echo "Restarting BGP container..."
docker restart bgp

echo "Configuration applied successfully."
