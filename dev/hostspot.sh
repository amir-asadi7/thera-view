#!/bin/bash
echo "Setting up the hotspot"

HOSTNAME=$(hostname)

sudo nmcli device wifi hotspot con-name "${HOSTNAME}-hotspot" ssid "${HOSTNAME}" password "starseng"
sudo nmcli connection modify "${HOSTNAME}-hotspot" autoconnect yes
sudo nmcli connection up "${HOSTNAME}-hotspot"
