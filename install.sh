#!/usr/bin/env bash
# Install script for Photon Laser Tag Project (Team 7)

set -e

echo "Updating apt..."
sudo apt update

echo "Installing system dependencies..."
sudo apt install -y python3 python3-pip python3-psycopg2

echo "Installing Python packages..."
python3 -m pip install --user --upgrade psycopg2-binary pygame

echo "Installation complete."
