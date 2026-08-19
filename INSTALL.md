# Installation Guide

This guide installs the custom Arcade Legends 3 controller bridge and startup services on Batocera.

It assumes the original Arcade Legends controller/interface is connected by USB and Linux detects its FTDI serial interface as:

```text
/dev/ttyUSB0
```

The files in this repository are based on the verified working configuration from the completed cabinet.

---

## 1. Verify the Controller Interface

Before installing anything, confirm that Linux detects the controller's FTDI serial interface.

Run:

```bash
dmesg | grep -i -E 'ftdi|ttyUSB'
```

You should see something similar to:

```text
FT232R USB UART
```

Then check:

```bash
ls -l /dev/ttyUSB*
```

The expected device is:

```text
/dev/ttyUSB0
```

If `/dev/ttyUSB0` does not exist, stop here and troubleshoot the USB/controller connection before continuing.

---

## 2. Install the AL3 Controller Bridge

Copy:

```text
scripts/al3_bridge.py
```

to:

```text
/userdata/system/al3_bridge.py
```

Example from another computer:

```bash
scp scripts/al3_bridge.py root@batocera:/userdata/system/al3_bridge.py
```

Make it executable:

```bash
chmod +x /userdata/system/al3_bridge.py
```

The bridge is configured for:

```text
/dev/ttyUSB0
115200 baud
8 data bits
no parity
1 stop bit
no hardware flow control
```

or:

```text
115200 8N1
```

The controller sends 19-byte packets framed by:

```text
Start: 0x5A
End:   0xA5
```

The script creates four Linux virtual input devices:

```text
AL3 Player 1
AL3 Player 2
AL3 Trackball
AL3 Hotkeys
```

---

## 3. Install the AL3 Batocera Service

Copy:

```text
services/AL3_Bridge
```

to:

```text
/userdata/system/services/AL3_Bridge
```

Example:

```bash
scp services/AL3_Bridge root@batocera:/userdata/system/services/AL3_Bridge
```

Make it executable:

```bash
chmod +x /userdata/system/services/AL3_Bridge
```

Enable the service:

```bash
batocera-services enable AL3_Bridge
```

Start it:

```bash
batocera-services start AL3_Bridge
```

Verify it is enabled:

```bash
batocera-services list | grep -i AL3
```

The expected output should include:

```text
AL3_Bridge;*
```

Verify that the bridge process is running:

```bash
ps aux | grep '[a]l3_bridge.py'
```

The service waits for `/dev/ttyUSB0`, starts the bridge, logs its output, and restarts it if it exits.

---

## 4. Verify the Linux Input Devices

Run:

```bash
evtest
```

You should see:

```text
AL3 Player 1
AL3 Player 2
AL3 Trackball
AL3 Hotkeys
```

Test Player 1 and Player 2.

The player-button behavior is:

```text
Short press
→ START

Hold approximately one second
→ SELECT / COIN
```

The trackball should generate:

```text
REL_X
REL_Y
```

If the virtual devices do not appear, check:

```bash
tail -f /userdata/system/al3_bridge.log
```

---

## 5. Verify the Trackball

Select:

```text
AL3 Trackball
```

in `evtest`.

Move the original cabinet trackball.

You should see:

```text
REL_X
REL_Y
```

The working bridge applies a 2× multiplier to the raw movement:

```python
dx = signed7(pkt[5]) * 2
dy = signed7(pkt[6]) * 2
```

This is the sensitivity used on the completed cabinet.

If the trackball works but feels too fast or too slow across all games, this multiplier can be adjusted.

If only one game has incorrect sensitivity, investigate that game's settings before changing the bridge.

---

## 6. Verify the Cabinet Volume Shortcut

Select:

```text
AL3 Hotkeys
```

in `evtest`.

The working cabinet shortcuts are:

```text
EXIT + Player 1 UP
→ Volume Up

EXIT + Player 1 DOWN
→ Volume Down
```

The bridge should generate:

```text
KEY_VOLUMEUP
KEY_VOLUMEDOWN
```

The first volume step happens immediately.

If the joystick remains held, repeat begins after approximately:

```text
0.35 seconds
```

and repeats approximately every:

```text
0.12 seconds
```

Player 1 vertical movement is suppressed while EXIT is held, so adjusting volume should not also move the player.

---

## 7. Verify the EXIT Button

EXIT by itself should exit the current game.

The working bridge handles EXIT on release using:

```text
hotkeygen --send exit
```

Expected behavior:

```text
EXIT
→ Exit current game
→ Return to EmulationStation
```

If EXIT was used together with Player 1 Up or Down for volume adjustment, releasing EXIT should **not** exit the game.

---

## 8. Back Up the EmulationStation Controller Configuration

Before modifying the EmulationStation mapping, create a backup:

```bash
cp /userdata/system/configs/emulationstation/es_input.cfg \
   /userdata/system/configs/emulationstation/es_input.cfg.backup
```

The file being modified is:

```text
/userdata/system/configs/emulationstation/es_input.cfg
```

---

## 9. Install the EmulationStation Mapping Helper

Copy:

```text
scripts/update_es_input.py
```

to:

```text
/userdata/system/update_es_input.py
```

Example:

```bash
scp scripts/update_es_input.py root@batocera:/userdata/system/update_es_input.py
```

Run it:

```bash
python3 /userdata/system/update_es_input.py
```

The script updates only:

```text
AL3 Player 1
AL3 Player 2
```

It sets:

```text
Button 6 → SELECT
Button 7 → START
```

and leaves unrelated controllers unchanged.

---

## 10. Verify the SDL Controller Mappings

Set the display variable:

```bash
export DISPLAY=:0.0
```

Then run:

```bash
sdl2-jstest --list
```

Or:

```bash
sdl2-jstest --list | grep -E 'Joystick Name|Number of Buttons|Button code'
```

You should see:

```text
AL3 Player 1
AL3 Player 2
```

Each virtual player controller should expose eight buttons.

The verified mappings are:

```text
Button 6 → SELECT
Button 7 → START
```

If Linux input is correct but SDL is not, troubleshoot SDL or the EmulationStation mapping rather than the serial bridge.

---

## 11. Reboot and Verify Persistence

Reboot Batocera:

```bash
reboot
```

After the system returns, verify:

```bash
batocera-services list | grep -i AL3
```

and:

```bash
ps aux | grep '[a]l3_bridge.py'
```

The bridge should start automatically.

Run:

```bash
evtest
```

again and confirm that:

```text
AL3 Player 1
AL3 Player 2
AL3 Trackball
AL3 Hotkeys
```

are present after reboot.

---

## 12. Install the Audio Service if Needed

The cabinet used for this project required Batocera to force the analog headphone output after boot.

Copy:

```text
services/Force_Headphones
```

to:

```text
/userdata/system/services/Force_Headphones
```

Example:

```bash
scp services/Force_Headphones root@batocera:/userdata/system/services/Force_Headphones
```

Make it executable:

```bash
chmod +x /userdata/system/services/Force_Headphones
```

Enable it:

```bash
batocera-services enable Force_Headphones
```

Start it:

```bash
batocera-services start Force_Headphones
```

Verify it is enabled:

```bash
batocera-services list | grep -i Headphones
```

The expected output should include:

```text
Force_Headphones;*
```

---

## 13. Verify the Audio Output

The included service uses this sink:

```text
alsa_output.pci-0000_00_1f.3.analog-stereo
```

and selects:

```text
analog-output-headphones
```

Check the current active port:

```bash
pactl list sinks | grep "Active Port"
```

The working cabinet reports:

```text
Active Port: analog-output-headphones
```

The sink name in `services/Force_Headphones` is specific to the Batocera computer used in this project.

Another computer may use a different sink.

List available sinks with:

```bash
pactl list short sinks
```

If your sink differs, edit:

```text
/userdata/system/services/Force_Headphones
```

and change:

```bash
SINK="alsa_output.pci-0000_00_1f.3.analog-stereo"
```

to the correct sink for your system.

---

## 14. Apply Game-Specific Overrides Only When Needed

Verified examples are included in:

```text
config/game-overrides.conf
```

Examples include:

```text
Tempest
→ relative mouse/spinner input

Pac-Man
→ CRT viewport adjustment

Frogger
→ CRT viewport adjustment
```

The settings can be added to:

```text
/userdata/system/batocera.conf
```

Only apply the overrides you actually need.

The exact viewport values used on this cabinet are cabinet-specific and should not automatically be copied to another CRT.

For details, see:

[Game-Specific Fixes](docs/game-fixes.md)

---

## 15. Final Functional Test

After reboot, verify the complete cabinet.

### Player 1

Test:

- joystick Up
- joystick Down
- joystick Left
- joystick Right
- all arcade buttons
- Start
- Coin

### Player 2

Test:

- joystick Up
- joystick Down
- joystick Left
- joystick Right
- all arcade buttons
- Start
- Coin

### Start and Coin

Verify:

```text
Tap player button
→ START

Hold approximately one second
→ SELECT / COIN
```

### Trackball

Verify that the original trackball moves correctly.

The working bridge uses the 2× movement multiplier.

### Volume

Verify:

```text
EXIT + P1 UP
→ Volume Up

EXIT + P1 DOWN
→ Volume Down
```

Confirm that Player 1 does not also move vertically while changing volume.

### EXIT

Verify:

```text
EXIT
→ Exit game
```

Then verify that changing volume does **not** accidentally exit the game.

### Audio

Confirm that cabinet audio is present and:

```text
analog-output-headphones
```

is active.

### Video

Confirm that Batocera displays correctly on the original CRT.

### Game-specific behavior

Test at least:

- one normal joystick game
- one trackball or relative-input game
- one vertical game

This helps verify the different configuration layers independently.

---

## Troubleshooting

If the controller is not detected:

```bash
ls -l /dev/ttyUSB*
```

and:

```bash
dmesg | grep -i -E 'ftdi|ttyUSB'
```

If `/dev/ttyUSB0` is missing, troubleshoot the USB/controller connection first.

If `/dev/ttyUSB0` exists but the AL3 devices do not appear:

```bash
ps aux | grep '[a]l3_bridge.py'
```

and:

```bash
tail -f /userdata/system/al3_bridge.log
```

If the AL3 devices appear in Linux but EmulationStation mappings are wrong:

```bash
export DISPLAY=:0.0
sdl2-jstest --list
```

Then verify:

```text
/userdata/system/configs/emulationstation/es_input.cfg
```

If the volume shortcut produces no events, test:

```text
AL3 Hotkeys
```

with `evtest`.

If EXIT works by itself but also exits while adjusting volume, verify that the running bridge contains the `exit_used_for_volume` logic.

If EmulationStation works but only one game has a problem, move troubleshooting to the emulator or per-game configuration layer rather than changing the controller bridge.

For the complete workflow, see:

[Troubleshooting](docs/troubleshooting.md)

---

## Installed Files

A completed installation should include:

```text
/userdata/system/al3_bridge.py
/userdata/system/update_es_input.py
/userdata/system/services/AL3_Bridge
/userdata/system/services/Force_Headphones
/userdata/system/configs/emulationstation/es_input.cfg
```

The game-specific settings used by the cabinet are stored in:

```text
/userdata/system/batocera.conf
```

The bridge log is:

```text
/userdata/system/al3_bridge.log
```

---

## Documentation

Once installation is complete, see:

- [Hardware Conversion](docs/hardware.md)
- [Batocera Configuration](docs/batocera-configuration.md)
- [Controls](docs/controls.md)
- [Game-Specific Fixes](docs/game-fixes.md)
- [Troubleshooting](docs/troubleshooting.md)
