# Installation Guide

This guide installs the custom Arcade Legends controller bridge and startup services on Batocera.

It assumes the original Arcade Legends controller/interface is connected by USB and Linux detects its FTDI serial interface as:

    /dev/ttyUSB0

The files in this repository were built around that working configuration.

---

## 1. Verify the controller interface

Before installing anything, confirm that the controller's FTDI serial interface is detected.

Run:

    dmesg | grep -i -E 'ftdi|ttyUSB'

You should see something similar to:

    FT232R USB UART

Then check:

    ls -l /dev/ttyUSB*

The expected device is:

    /dev/ttyUSB0

If `/dev/ttyUSB0` does not exist, stop here and troubleshoot the USB/controller connection before continuing.

---

## 2. Install the AL3 controller bridge

Copy:

    scripts/al3_bridge.py

to:

    /userdata/system/al3_bridge.py

Example from another computer:

    scp scripts/al3_bridge.py root@batocera:/userdata/system/al3_bridge.py

Then make it executable:

    chmod +x /userdata/system/al3_bridge.py

The bridge is configured for:

    /dev/ttyUSB0
    115200 baud
    8 data bits
    no parity
    1 stop bit
    no hardware flow control

or:

    115200 8N1

The script creates four Linux virtual input devices:

    AL3 Player 1
    AL3 Player 2
    AL3 Trackball
    AL3 Hotkeys

---

## 3. Install the AL3 Batocera service

Copy:

    services/AL3_Bridge

to:

    /userdata/system/services/AL3_Bridge

Example:

    scp services/AL3_Bridge root@batocera:/userdata/system/services/AL3_Bridge

Make it executable:

    chmod +x /userdata/system/services/AL3_Bridge

Enable the service:

    batocera-services enable AL3_Bridge

Start it:

    batocera-services start AL3_Bridge

Verify it is enabled:

    batocera-services list | grep -i AL3

The expected output should include:

    AL3_Bridge;*

You can also verify that the bridge process is running:

    ps aux | grep '[a]l3_bridge.py'

The service waits for `/dev/ttyUSB0`, starts the bridge, and restarts it if the bridge exits.

---

## 4. Verify the Linux input devices

Run:

    evtest

You should see devices named:

    AL3 Player 1
    AL3 Player 2
    AL3 Trackball
    AL3 Hotkeys

Test Player 1 and Player 2 controls.

The player button behavior is:

    Short press
    → START

    Hold for approximately one second
    → SELECT / COIN

The trackball should generate relative input events:

    REL_X
    REL_Y

If the virtual devices do not appear, check the bridge log:

    tail -f /userdata/system/al3_bridge.log

---

## 5. Back up the EmulationStation controller configuration

Before modifying the EmulationStation controller mapping, create a backup:

    cp /userdata/system/configs/emulationstation/es_input.cfg \
       /userdata/system/configs/emulationstation/es_input.cfg.backup

The file being modified is:

    /userdata/system/configs/emulationstation/es_input.cfg

---

## 6. Install the EmulationStation mapping helper

Copy:

    scripts/update_es_input.py

to:

    /userdata/system/update_es_input.py

Example:

    scp scripts/update_es_input.py root@batocera:/userdata/system/update_es_input.py

Run it:

    python3 /userdata/system/update_es_input.py

The script updates only:

    AL3 Player 1
    AL3 Player 2

It sets:

    Button 6 → SELECT
    Button 7 → START

and leaves unrelated controllers alone.

---

## 7. Verify the SDL controller mappings

Set the display variable:

    export DISPLAY=:0.0

Then run:

    sdl2-jstest --list

Or filter the output:

    sdl2-jstest --list | grep -E 'Joystick Name|Number of Buttons|Button code'

You should see:

    AL3 Player 1
    AL3 Player 2

Each virtual player controller should expose eight buttons.

The verified button mappings are:

    Button 6 → SELECT
    Button 7 → START

This is the important check before moving on to emulator-specific troubleshooting.

---

## 8. Reboot and verify persistence

Reboot Batocera:

    reboot

After the system comes back up, verify:

    batocera-services list | grep -i AL3

and:

    ps aux | grep '[a]l3_bridge.py'

The bridge should start automatically.

You can also run:

    evtest

again to confirm that the AL3 virtual input devices return after reboot.

---

## 9. Install the audio service if needed

The cabinet used for this project required Batocera to force the analog headphone output after boot.

Copy:

    services/Force_Headphones

to:

    /userdata/system/services/Force_Headphones

Example:

    scp services/Force_Headphones root@batocera:/userdata/system/services/Force_Headphones

Make it executable:

    chmod +x /userdata/system/services/Force_Headphones

Enable it:

    batocera-services enable Force_Headphones

Start it:

    batocera-services start Force_Headphones

Verify it is enabled:

    batocera-services list | grep -i Headphones

The expected output should include:

    Force_Headphones;*

---

## 10. Verify the audio output

The included service uses this sink:

    alsa_output.pci-0000_00_1f.3.analog-stereo

and selects:

    analog-output-headphones

Verify the current active port with:

    pactl list sinks | grep "Active Port"

You should see:

    Active Port: analog-output-headphones

Important:

The sink name in `services/Force_Headphones` is specific to the Batocera computer used in this build.

Another PC may use a different sink name.

To inspect available sinks, run:

    pactl list short sinks

If your sink name differs, edit:

    /userdata/system/services/Force_Headphones

and change:

    SINK="alsa_output.pci-0000_00_1f.3.analog-stereo"

to the correct value for your system.

---

## 11. Apply game-specific overrides only when needed

Verified examples are included in:

    config/game-overrides.conf

These settings are intended as examples of solving specific game issues without changing global emulator behavior.

Examples include:

- Tempest — relative mouse/spinner input
- Pac-Man — CRT viewport adjustment
- Frogger — CRT viewport adjustment

The settings can be added to:

    /userdata/system/batocera.conf

Only apply the overrides you actually need.

For details, see:

    docs/game-fixes.md

---

## 12. Final functional test

After reboot, verify the complete control path.

### Player controls

Test:

- Player 1 joystick
- Player 1 buttons
- Player 2 joystick
- Player 2 buttons

### Start and Coin behavior

Verify:

    Tap player button
    → START

    Hold approximately one second
    → SELECT / COIN

### Trackball

Verify the trackball moves correctly in a supported game or through Linux input testing.

### Exit / hotkey behavior

Verify the cabinet exit control behaves as expected.

### Audio

Confirm that cabinet audio is present and that the intended analog output is active.

### Video

Confirm that Batocera is displaying correctly on the original CRT.

---

## Troubleshooting

If the controller is not detected:

    ls -l /dev/ttyUSB*

and:

    dmesg | grep -i -E 'ftdi|ttyUSB'

If `/dev/ttyUSB0` is missing, troubleshoot the USB/controller connection first.

If `/dev/ttyUSB0` exists but the AL3 devices do not appear:

    ps aux | grep '[a]l3_bridge.py'

and:

    tail -f /userdata/system/al3_bridge.log

If the AL3 devices appear in Linux but EmulationStation mappings are wrong:

    export DISPLAY=:0.0
    sdl2-jstest --list

Then verify the `es_input.cfg` mappings.

If EmulationStation works but one game does not, move troubleshooting to the emulator or per-game configuration layer rather than changing the controller bridge.

For the full troubleshooting workflow, see:

    docs/troubleshooting.md

---

## Installed files

A completed installation should include:

    /userdata/system/al3_bridge.py
    /userdata/system/update_es_input.py
    /userdata/system/services/AL3_Bridge
    /userdata/system/services/Force_Headphones
    /userdata/system/configs/emulationstation/es_input.cfg

The game-specific settings used by this cabinet are stored in:

    /userdata/system/batocera.conf

The bridge log is:

    /userdata/system/al3_bridge.log

---

## Next steps

Once the installation is working, see:

- [Hardware Conversion](docs/hardware.md)
- [Batocera Configuration](docs/batocera-configuration.md)
- [Controls](docs/controls.md)
- [Game-Specific Fixes](docs/game-fixes.md)
- [Troubleshooting](docs/troubleshooting.md)
