#!/bin/bash
# install_ffmpeg.sh
# Installs FFmpeg on Raspberry Pi and verifies the installation.

set -e

echo "Updating system packages..."
sudo apt update && sudo apt upgrade -y

echo "Installing FFmpeg..."
sudo apt install ffmpeg -y

echo "Verifying FFmpeg installation..."
ffmpeg -version

echo "FFmpeg installation complete."
