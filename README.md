# thera-view
Thera-View coordinates two Raspberry Pi devices, each connected to a webcam, to record synchronized video streams of physiotherapy or occupational therapy sessions

## Hardware Requirements

Each setup requires:  
- **Raspberry Pi**: model 4B used for development (other models may also work)  
- **MicroSD card**: at least 32 GB, Class 10 or better recommended  
- **Webcam**: standard USB webcam (tested models to be listed)  
- **TFT display**: optional, for local monitoring (details to follow)  
- **Power supply**: official Raspberry Pi adapter or equivalent  

---

## 0. Initial Raspberry Pi Setup

1. **Prepare the operating system**  
   - Use **Raspberry Pi Imager**  
   - Select the **64-bit Lite** version of Raspberry Pi OS  

2. **Set the hostname**  
   - Use the pattern `rpicam##` (for example `rpicam04`) to identify each board  

3. **Enable SSH**  
   - In the imager settings, enable **SSH** for remote access  

4. **Configure Wi-Fi**  
   - Connect to a Wi-Fi network during installation  
   - A mobile hotspot works well for setup  
   - On iPhones, remove any apostrophe from the device name before sharing (for example, rename *Jack’s iPhone* to *JackPhone*)  

5. **Network connection**  
   - After flashing and booting the Pi, connect your laptop or PC to the same network as the Pi devices  

Additional configuration details will be added later.


## Development Mode: X11 Forwarding Setup

To develop or test GUI applications remotely, set up **X11 forwarding** between your Raspberry Pi and Ubuntu system.

1. Edit the SSH daemon configuration:  
   ```bash
   sudo nano /etc/ssh/sshd_config
   ```
Uncomment or add the following lines:
   ```bash
   X11Forwarding yes
   X11DisplayOffset 10
   X11UseLocalhost yes

   ```
Restart the SSH service
   ```bash
   sudo systemctl restart ssh
   ```


On the Ubuntu (client) side

Install utilities
   ```bash
   sudo apt update
   sudo apt install xorg openssh-client 
   ```

edit the SSH configuration to allow X forwarding:
   ```bash
   sudo nano /etc/ssh/ssh_config
   ```
Add or confirm this line:
   ```bash
   ForwardX11 yes
   ```

Connect to the Raspberry Pi using X forwarding:
```bash
ssh -X rpicam@rpicam.local
```

## Rpi setup

    ```bash
   sudo apt update && sudo apt upgrade -y
   sudo apt-get install git python3 python3-venv python3-pip -y #current version of python is 3.13.5 ()
    ```

## Virtual env setup and requirements

    ```bash
    git clone #link
    cd thera-view
    python3 -m venv venv     
    source venv/bin/activate
    pip install -r requirements.txt
