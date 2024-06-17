#!/bin/bash

# 1. Sistem türünü kontrol etme
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

# 2. curl ve wget kontrolü
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

# 3. Zip dosyasını indirme ve çıkarma
ZIP_URL="https://github.com/TurkishLinuxUser/Adhan/releases/download/1.0.0/adhan.zip" 
ZIP_FILE="/tmp/adhan.zip"

$DOWNLOAD_CMD $ZIP_FILE $ZIP_URL
sudo unzip -o $ZIP_FILE -d ~/.local/share/

# 4. /usr/bin içerisine adhan dosyası oluşturma
echo "~/.local/share/adhan/Adhan" | sudo tee /usr/bin/adhan > /dev/null
sudo chmod +x /usr/bin/adhan

# 5. /usr/share/applications içerisine kısayol oluşturma
cat << EOF | sudo tee /usr/share/applications/adhan.desktop > /dev/null
[Desktop Entry]
Name=Adhan
Exec=~/.local/share/adhan/Adhan
Icon=~/.local/share/adhan/Adhan/icon128x128.png
Type=Application
Categories=Utility;
EOF

sudo chmod +x /usr/share/applications/adhan.desktop
