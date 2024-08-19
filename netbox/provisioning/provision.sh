#!/bin/bash

# This script is designed for use with Zero Touch Provisioning (ZTP) to automatically apply the initial device configuration.
# The device hostname is used as a key to retrieve the config_db.json and frr.conf files from NetBox,
# which are then saved on the device where the script is executed.
#
# Usage: ./provision.sh -u NETBOX_URL -t AUTH_TOKEN

CONFIG_DIR="/etc/sonic"
TEMP_DIR="/tmp/ztp_config"
CONFIG_DB_PATH="$CONFIG_DIR/config_db.json"
FRR_CONF_PATH="$CONFIG_DIR/frr/frr.conf"

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

validate_commands jq yq curl

HOSTNAME=$(hostname)

echo "Querying NetBox information for device: $HOSTNAME ..."
DEVICE_INFO=$(curl -s -H "Authorization: Token $AUTH_TOKEN" -H "Content-Type: application/json" "${NETBOX_API}?name=${HOSTNAME}")

DEVICE_ID=$(echo "$DEVICE_INFO" | jq -r '.results[0].id')
if [ -z "$DEVICE_ID" ] || [ "$DEVICE_ID" == "null" ]; then
    echo "Error: Device not found in NetBox with hostname '$HOSTNAME'"
    exit 1
fi

echo "Fetching rendered configuration from NetBox for device ID: $DEVICE_ID ..."
CONFIG=$(curl -X POST -s -H "Authorization: Token $AUTH_TOKEN" -H "Content-Type: application/json" "${NETBOX_API}${DEVICE_ID}/render-config/")

# Create temporary directory
mkdir -p "$TEMP_DIR"

# Extract and save config_db.json
CONFIG_DB_JSON=$(echo "$CONFIG" | jq -r '.content' | yq e '."config_db.json"' -)
if [ -n "$CONFIG_DB_JSON" ]; then
    echo "Writing config_db.json to temporary directory..."
    echo "$CONFIG_DB_JSON" > "$TEMP_DIR/config_db.json"
else
    echo "Error: config_db.json not found in the rendered configuration."
    exit 1
fi

# Extract and save frr.conf
FRR_CONF=$(echo "$CONFIG" | jq -r '.content' | yq e '."frr.conf"' -)
if [ -n "$FRR_CONF" ]; then
    echo "Writing frr.conf to temporary directory..."
    echo "$FRR_CONF" > "$TEMP_DIR/frr.conf"
else
    echo "Error: frr.conf not found in the rendered configuration."
    exit 1
fi

# Move files to the desired location with sudo
echo "Moving files to $CONFIG_DIR..."
sudo mv "$TEMP_DIR/config_db.json" "$CONFIG_DB_PATH"
sudo mv "$TEMP_DIR/frr.conf" "$FRR_CONF_PATH"

rm -rf "$TEMP_DIR"

echo "Applying config_db.json config..."
sudo config reload -y

echo "Applying FRR config..."
docker restart bgp

echo "Configuration applied successfully."
