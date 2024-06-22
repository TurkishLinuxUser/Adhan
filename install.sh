#!/bin/bash

rm -rf /home/$USER/.local/share/adhan

# Determine distribution
if [ -f /etc/debian_version ]; then
    DISTRO="debian"
elif [ -f /etc/redhat-release ]; then
    DISTRO="fedora"
elif [ -f /etc/arch-release ]; then
    DISTRO="arch"
else
    echo "Unsupported operating system."
    exit 1
fi

# Install wget if necessary
if ! command -v wget &> /dev/null; then
    if [ "$DISTRO" == "debian" ]; then
        sudo apt update
        sudo apt install wget git python3 python3-tk python3-pip -y
    elif [ "$DISTRO" == "fedora" ]; then
        sudo dnf install wget git python3 python3-tk python3-pip -y
    elif [ "$DISTRO" == "arch" ]; then
        sudo pacman -Sy wget git python3 python3-tk python3-pip
    fi
fi

# Create and activate virtual environment
python -m venv adhan_env
source adhan_env/bin/activate

# Create requirements.txt file
cat << EOF > requirements.txt
pystray
pygame
pyinstaller
EOF


# Download Adhan raw files
ADHAN_URL="https://github.com/TurkishLinuxUser/Adhan"
RAW_URL="https://raw.githubusercontent.com/TurkishLinuxUser/Adhan/main"

# Download Adhan.py raw file (assuming this is the main script)
ADHAN_PY_URL="$RAW_URL/Adhan.py"
ADHAN_PY_FILE="/home/$USER/Adhan.py"
wget -O $ADHAN_PY_FILE $ADHAN_PY_URL
wget -O /home/$USER/ https://github.com/TurkishLinuxUser/releases/download/3.0.0/adhan.zip
unzip -o /home/$USER/adhan.zip -d ~/.local/share/ > /dev/null

# Install requirements
pip install -r requirements.txt > /dev/null

mkdir /home/$USER/output
pyinstaller --onedir --windowed --distpath=/home/$USER/output $ADHAN_PY_FILE
mv /home/$USER/output/dist/ /home/$USER/.local/share/adhan/

rm -rf mkdir /home/$USER/output
rm -rf $ADHAN_PY_FILE
rm -rf requirements.txt


# Create symbolic link in /usr/bin
echo "~/.local/share/adhan/Adhan" | sudo tee /usr/bin/adhan > /dev/null
sudo chmod +x /usr/bin/adhan

# Create adhan.desktop file
USERNAME=$USER
cat << EOF | sudo tee /usr/share/applications/adhan.desktop > /dev/null
[Desktop Entry]
Name=Adhan
Exec=/home/$USERNAME/.local/share/adhan/Adhan
Type=Application
Categories=Utility;
EOF

sudo chmod +x /usr/share/applications/adhan.desktop

# Deactivate virtual environment
deactivate

echo "Adhan has been installed successfully!"
