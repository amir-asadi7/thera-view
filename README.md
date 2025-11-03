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

---

## 1. Venv setup and installation

    ```bash
    git clone #link
    cd thera-view
    python3 -m venv venv     # you may need to run this:    sudo apt install python3.10-venv  ##to be cheked on Rpi
    source venv/bin/activate
    pip install -r requirements.txt
    ```


