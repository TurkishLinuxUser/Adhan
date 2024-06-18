#!/bin/bash

if [ -f /etc/debian_version ]; then
    DISTRO="debian"
elif [ -f /etc/redhat-release ]; then
    DISTRO="fedora"
elif [ -f /etc/arch-release ]; then
    DISTRO="arch"
else
    echo "Desteklenmeyen işletim sistemi."
    exit 1
fi

if command -v curl &> /dev/null; then
    DOWNLOAD_CMD="curl -L -o"
elif command -v wget &> /dev/null; then
    DOWNLOAD_CMD="wget -O"
else
    if [ "$DISTRO" == "debian" ]; then
        sudo apt update
        sudo apt install -y wget
    elif [ "$DISTRO" == "fedora" ]; then
        sudo dnf install -y wget
    elif [ "$DISTRO" == "arch" ]; then
        sudo pacman -Sy wget
    fi
    DOWNLOAD_CMD="wget -O"
fi

ZIP_URL="https://github.com/TurkishLinuxUser/Adhan/releases/download/1.0.0/adhan.zip" 
ZIP_FILE="/tmp/adhan.zip"

$DOWNLOAD_CMD $ZIP_FILE $ZIP_URL
unzip -o $ZIP_FILE -d ~/.local/share/

echo "~/.local/share/adhan/Adhan" | sudo tee /usr/bin/adhan > /dev/null
sudo chmod +x /usr/bin/adhan

sudo rm -rf /tmp/adhan.zip

USERNAME=$USER
cat << EOF | sudo tee /usr/share/applications/adhan.desktop > /dev/null
[Desktop Entry]
Name=Adhan
Exec=/home/$USERNAME/.local/share/adhan/Adhan
Icon=/home/$USERNAME/.local/share/adhan/Adhan/icon128x128.png
Type=Application
Categories=Utility;
EOF

sudo chmod +x /usr/share/applications/adhan.desktop
