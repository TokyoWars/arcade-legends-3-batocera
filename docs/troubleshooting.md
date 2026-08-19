# Troubleshooting Guide

This document describes the troubleshooting method used during the Arcade Legends 3 Batocera conversion.

The most important principle is:

> **Troubleshoot from the bottom of the stack upward.**

Do not begin changing MAME settings if Linux is not receiving the controller correctly.

Do not modify the controller bridge because one game behaves differently.

The system becomes much easier to diagnose when each layer is tested independently.

---

## Troubleshooting Stack

Work through the system in this order:

```text
Physical control
      ↓
Cabinet wiring
      ↓
Original controller/interface
      ↓
USB / FTDI serial interface
      ↓
/dev/ttyUSB0
      ↓
AL3 bridge
      ↓
Linux input
      ↓
SDL
      ↓
EmulationStation / Batocera
      ↓
MAME
      ↓
Individual game
```

Only move upward after confirming the layer below it works.

---

## 1. Check the Physical Controls

Start with the simplest possible causes.

Check:

- joystick movement
- arcade buttons
- player buttons
- trackball movement
- EXIT button
- cabinet connectors
- loose plugs
- damaged wiring
- recently moved cables

If only one physical control fails, the problem is more likely to be:

```text
switch
wiring
connector
controller input
```

than a Batocera-wide problem.

If several unrelated controls fail simultaneously, move farther up the troubleshooting stack.

---

## 2. Verify the Controller Interface

The original Arcade Legends controller/interface connects to the Batocera computer by USB.

Linux detects its FTDI serial interface as:

```text
FT232R USB UART
```

and exposes it as:

```text
/dev/ttyUSB0
```

Check detection with:

```bash
dmesg | grep -Ei 'ftdi|ttyUSB'
```

Then verify the device exists:

```bash
ls -l /dev/ttyUSB*
```

The expected device is:

```text
/dev/ttyUSB0
```

If `/dev/ttyUSB0` does not exist, investigate:

- USB cable
- USB port
- controller/interface power
- connector seating
- kernel detection
- whether another USB serial device changed the device number

Do not troubleshoot MAME until the controller interface exists at the Linux level.

---

## 3. Verify Serial Communication

Once `/dev/ttyUSB0` exists, the next layer is communication with the original controller.

The verified working serial configuration is:

```text
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

The original controller sends repeating binary packets.

The bridge expects:

```text
19-byte packets
```

framed by:

```text
Start: 0x5A
End:   0xA5
```

If the serial interface exists but the bridge cannot decode useful packets, investigate:

```text
controller power
USB connection
serial interface
baud rate
serial configuration
packet framing
```

The bridge itself configures `/dev/ttyUSB0` using `stty`, so the running script should normally establish the required serial settings automatically.

---

## 4. Verify the AL3 Bridge Service

The controller bridge is:

```text
/userdata/system/al3_bridge.py
```

It is started automatically through:

```text
/userdata/system/services/AL3_Bridge
```

Check whether the service is enabled:

```bash
batocera-services list | grep -i AL3
```

The expected result includes:

```text
AL3_Bridge;*
```

Check whether the Python bridge is running:

```bash
ps aux | grep '[a]l3_bridge.py'
```

The expected process should resemble:

```text
python3 /userdata/system/al3_bridge.py
```

If `/dev/ttyUSB0` exists but the bridge is not running, inspect the bridge log:

```bash
tail -100 /userdata/system/al3_bridge.log
```

For live monitoring:

```bash
tail -f /userdata/system/al3_bridge.log
```

The service waits for `/dev/ttyUSB0`, starts the bridge, and restarts it if the bridge exits.

---

## 5. Verify the Virtual Linux Devices

When the bridge is running successfully, it creates:

```text
AL3 Player 1
AL3 Player 2
AL3 Trackball
AL3 Hotkeys
```

Run:

```bash
evtest
```

Look for those four devices.

If none of them exist even though `/dev/ttyUSB0` exists, investigate:

```text
AL3 bridge
Python / evdev
UInput
serial parsing
service status
permissions
bridge log
```

Do not move into EmulationStation or MAME troubleshooting until the Linux devices exist.

---

## 6. Test Player 1 and Player 2

Use:

```bash
evtest
```

and select:

```text
AL3 Player 1
```

Test:

- Up
- Down
- Left
- Right
- all arcade buttons
- player button short press
- player button long press

Repeat for:

```text
AL3 Player 2
```

The expected player-button behavior is:

```text
Tap
→ START

Hold approximately one second
→ SELECT / COIN
```

If the correct Linux events appear, the controller hardware and bridge are doing their job.

If Batocera behaves incorrectly after this point, move higher in the stack.

---

## 7. Test Start and Coin

The bridge intentionally gives each original player button two functions.

Expected behavior:

```text
Quick press
→ START

Hold approximately 1 second
→ SELECT / COIN
```

The verified virtual-controller mappings are:

```text
Button 6 → SELECT
Button 7 → START
```

If Start and Coin are reversed or incorrect in EmulationStation, check:

```text
/userdata/system/configs/emulationstation/es_input.cfg
```

The repository also includes:

```text
scripts/update_es_input.py
```

which fixes the mappings specifically for:

```text
AL3 Player 1
AL3 Player 2
```

Do not change the packet-decoding logic if Linux already reports the correct buttons.

---

## 8. Test the Trackball

In `evtest`, select:

```text
AL3 Trackball
```

Move the trackball.

You should see relative events:

```text
REL_X
REL_Y
```

The working bridge applies a 2× multiplier:

```python
dx = signed7(pkt[5]) * 2
dy = signed7(pkt[6]) * 2
```

If movement exists but feels too slow or too fast, the sensitivity multiplier is the relevant setting.

Do not change it simply because one game has an unusual analog sensitivity setting. First determine whether the problem exists across multiple trackball games.

---

## 9. Test the Cabinet Volume Shortcut

The working cabinet uses the EXIT button as a modifier for Player 1 Up and Down.

Expected behavior:

```text
EXIT + Player 1 UP
→ Volume Up

EXIT + Player 1 DOWN
→ Volume Down
```

The bridge emits:

```text
KEY_VOLUMEUP
KEY_VOLUMEDOWN
```

through the `AL3 Hotkeys` device.

Use:

```bash
evtest
```

and select:

```text
AL3 Hotkeys
```

Then test:

```text
EXIT + P1 UP
EXIT + P1 DOWN
```

You should see the corresponding volume-key events.

The first volume event occurs immediately.

If the direction remains held, the bridge waits approximately:

```text
0.35 seconds
```

then repeats approximately every:

```text
0.12 seconds
```

---

## 10. Volume Shortcut Also Moves Player 1

This should not happen with the working bridge.

While EXIT is held, Player 1 vertical movement is suppressed.

Expected behavior:

```text
EXIT + P1 UP
→ Volume Up only

EXIT + P1 DOWN
→ Volume Down only
```

If the game also receives Up or Down, verify that the running bridge contains logic equivalent to:

```python
p1_y_out = 0 if exit_now else p1_y
```

Also confirm that the repository copy and the file actually running on Batocera are the same version.

---

## 11. EXIT Behavior

EXIT by itself should:

```text
Exit the current game
→ Return to EmulationStation
```

The current working bridge handles exit on button release.

If EXIT was not used for volume, it invokes:

```text
hotkeygen --send exit
```

This uses Batocera's normal emulator-exit mechanism.

If EXIT was used as the volume modifier, the bridge intentionally does **not** exit the game when EXIT is released.

---

## 12. EXIT Closes the Game While Changing Volume

This should not happen.

The bridge keeps track of:

```text
exit_used_for_volume
```

The intended flow is:

```text
EXIT pressed
    │
    ├── no P1 Up/Down used
    │       ↓
    │   release EXIT
    │       ↓
    │   hotkeygen --send exit
    │
    └── P1 Up or Down used
            ↓
        adjust volume
            ↓
        release EXIT
            ↓
        do not exit
```

If changing volume also exits the emulator, confirm that the running bridge contains the `exit_used_for_volume` logic.

---

## 13. Verify SDL

Batocera relies on SDL for controller handling.

Linux input can work correctly while SDL or EmulationStation still has an incorrect controller mapping.

Set the display variable:

```bash
export DISPLAY=:0.0
```

Then run:

```bash
sdl2-jstest --list
```

A more focused command is:

```bash
sdl2-jstest --list | grep -E 'Joystick Name|Number of Buttons|Button code'
```

Look for:

```text
AL3 Player 1
AL3 Player 2
```

Each should expose eight buttons.

The verified mappings include:

```text
Button 6 → SELECT
Button 7 → START
```

If `evtest` is correct but SDL is wrong, do not modify the serial packet decoder without additional evidence.

---

## 14. Check EmulationStation Controller Mapping

The controller configuration is stored in:

```text
/userdata/system/configs/emulationstation/es_input.cfg
```

The important AL3 mappings include:

```text
joystick directions
arcade buttons
START
SELECT
```

The repository helper:

```text
scripts/update_es_input.py
```

sets:

```text
SELECT → Button 6
START  → Button 7
```

for the AL3 virtual player controllers.

Before manually editing `es_input.cfg`, make a backup:

```bash
cp /userdata/system/configs/emulationstation/es_input.cfg \
/userdata/system/configs/emulationstation/es_input.cfg.backup
```

---

## 15. Determine Whether the Problem Is Global or Game-Specific

Before changing anything, test more than one game.

Ask:

```text
Does the problem happen everywhere?
```

If yes:

```text
investigate global configuration
```

If no:

```text
investigate the individual game or emulator
```

Decision tree:

```text
Problem
   │
   ▼
Multiple games affected?
   │
 ┌─┴─┐
Yes  No
 │    │
 ▼    ▼
Global   Game-specific
issue    issue
```

This is one of the most useful troubleshooting shortcuts in the entire project.

---

## 16. Check Batocera Launch Logs

One of the most useful files is:

```text
/userdata/system/logs/es_launch_stdout.log
```

It shows what Batocera actually launched.

For MAME-related launches:

```bash
grep -Ei '/usr/bin/mame|mame' \
/userdata/system/logs/es_launch_stdout.log
```

For Tempest:

```bash
grep -Ei 'tempest|/usr/bin/mame|mouse|dial|trackball' \
/userdata/system/logs/es_launch_stdout.log
```

For Pac-Man or Frogger:

```bash
grep -Ei 'pacman|frogger' \
/userdata/system/logs/es_launch_stdout.log
```

Launch logs can help confirm:

- ROM name
- emulator
- core
- launch arguments
- control-related options
- video overrides
- whether an unexpected configuration was applied

Prefer launch evidence over assumptions.

---

## 17. Game Does Not Launch

If one game fails to launch while others work, investigate:

```text
ROM name
ROM-set compatibility
BIOS requirements
selected emulator
selected core
MAME version
launch command
per-game configuration
```

Check the launch log first.

Do not change the global arcade configuration because one ROM fails.

---

## 18. Controls Fail in Only One Game

If:

```text
EmulationStation works
most MAME games work
one title has incorrect controls
```

the likely problem is higher in the stack.

Investigate:

```text
MAME game-specific mapping
control type
analog configuration
mouse input
dial input
game-specific override
```

Tempest is an example of this type of problem.

The global controller bridge should remain unchanged unless evidence shows the Linux events themselves are wrong.

---

## 19. Spinner / Dial Games

Some games use:

```text
DIAL
PADDLE
MOUSE
```

rather than conventional joystick input.

If the relative input works correctly in Linux but the game does not respond:

1. Confirm `AL3 Trackball` generates `REL_X` and `REL_Y`.
2. Confirm the game expects a relative analog input.
3. Confirm MAME mouse input is enabled if required.
4. Confirm the game's control is mapped to the appropriate MAME analog input.
5. Confirm the correct per-game override was applied.

For Tempest, the working Batocera override includes:

```text
mame["tempest.zip"].core=mame
mame["tempest.zip"].emulator=libretro
mame["tempest.zip"].retroarchcore.mame_mouse_enable=enabled
```

Useful launch-log check:

```bash
grep -Ei 'tempest|/usr/bin/mame|mouse|dial|trackball' \
/userdata/system/logs/es_launch_stdout.log
```

---

## 20. Trackball Is Too Slow or Too Fast

First determine whether the issue occurs:

```text
in every trackball game
```

or:

```text
in one game only
```

The working cabinet bridge uses:

```python
dx = signed7(pkt[5]) * 2
dy = signed7(pkt[6]) * 2
```

If every trackball game feels too slow or too fast, adjusting this multiplier may be appropriate.

If only one game feels wrong, investigate that game's analog sensitivity settings first.

---

## 21. Display Is Too Large or Too Small

If a game:

- launches correctly
- has working controls
- has the correct orientation
- but does not fit the visible CRT area

the problem is probably in the video layer.

Investigate:

```text
aspect ratio
viewport
scaling
overscan
rotation
per-game video settings
```

Do not automatically change global video settings.

Pac-Man and Frogger were examples where a game-specific viewport adjustment was preferable.

The working cabinet-specific viewport used for those games is:

```text
335 × 447
```

Those numbers are specific to this CRT and cabinet.

They should not be treated as universal settings.

---

## 22. Compare Against a Working Game

Always compare a failing game with a known-good title.

Example:

```text
Tempest fails
Pac-Man works
```

This already tells you:

```text
Batocera boots
MAME launches
basic controller path works
video output works
```

That greatly narrows the problem.

Similarly:

```text
Pac-Man image is oversized
horizontal games look correct
```

suggests:

```text
game-specific viewport issue
```

rather than:

```text
global CRT failure
```

---

## 23. No Cabinet Audio

The Batocera laptop feeds analog audio into the original cabinet audio path.

The project includes:

```text
/userdata/system/services/Force_Headphones
```

to select the intended analog output after boot.

Check the service:

```bash
batocera-services list | grep -i Headphones
```

The expected enabled service is:

```text
Force_Headphones;*
```

Check the current active audio port:

```bash
pactl list sinks | grep "Active Port"
```

The working cabinet expects:

```text
analog-output-headphones
```

---

## 24. Wrong Audio Port After Boot

The working service uses the sink:

```text
alsa_output.pci-0000_00_1f.3.analog-stereo
```

This name is specific to the Batocera computer used in this cabinet.

Another PC may use a different sink name.

List available sinks with:

```bash
pactl list short sinks
```

Then inspect:

```text
/userdata/system/services/Force_Headphones
```

If necessary, change:

```bash
SINK="alsa_output.pci-0000_00_1f.3.analog-stereo"
```

to the sink used by that computer.

---

## 25. Volume Buttons Generate Events but Volume Does Not Change

First verify with:

```bash
evtest
```

that:

```text
EXIT + P1 UP
```

generates:

```text
KEY_VOLUMEUP
```

and:

```text
EXIT + P1 DOWN
```

generates:

```text
KEY_VOLUMEDOWN
```

If those events exist, the bridge is working.

The remaining problem is higher in the audio/input stack.

Do not rewrite the controller packet decoder if the correct multimedia keys already appear in Linux.

---

## 26. Check Recent Changes First

If the cabinet worked correctly and suddenly stopped, begin with whatever changed most recently.

Examples:

- cable moved
- USB port changed
- controller remapped
- Batocera setting changed
- bridge script edited
- service edited
- emulator changed
- game override added
- audio device changed
- display setting changed

Avoid changing several things simultaneously.

Use:

```text
change one thing
↓
test
↓
observe
↓
continue
```

That makes rollback and diagnosis much easier.

---

## 27. Back Up Before Editing

Before modifying an important file, make a copy.

For EmulationStation:

```bash
cp /userdata/system/configs/emulationstation/es_input.cfg \
/userdata/system/configs/emulationstation/es_input.cfg.backup
```

For the bridge:

```bash
cp /userdata/system/al3_bridge.py \
/userdata/system/al3_bridge.py.backup
```

For Batocera configuration:

```bash
cp /userdata/system/batocera.conf \
/userdata/system/batocera.conf.backup
```

This gives you an immediate rollback point.

---

## 28. Useful Commands

### Detect the controller's FTDI serial interface

```bash
dmesg | grep -Ei 'ftdi|ttyUSB'
```

### Check serial devices

```bash
ls -l /dev/ttyUSB*
```

### Check the AL3 service

```bash
batocera-services list | grep -i AL3
```

### Check the bridge process

```bash
ps aux | grep '[a]l3_bridge.py'
```

### View the bridge log

```bash
tail -100 /userdata/system/al3_bridge.log
```

### Follow the bridge log live

```bash
tail -f /userdata/system/al3_bridge.log
```

### Test Linux input

```bash
evtest
```

### Inspect SDL controllers

```bash
export DISPLAY=:0.0
sdl2-jstest --list
```

### Inspect SDL controller details

```bash
export DISPLAY=:0.0
sdl2-jstest --list | grep -E 'Joystick Name|Number of Buttons|Button code'
```

### Inspect MAME launches

```bash
grep -Ei '/usr/bin/mame|mame' \
/userdata/system/logs/es_launch_stdout.log
```

### Inspect Tempest launch behavior

```bash
grep -Ei 'tempest|/usr/bin/mame|mouse|dial|trackball' \
/userdata/system/logs/es_launch_stdout.log
```

### Inspect Pac-Man / Frogger

```bash
grep -Ei 'pacman|frogger' \
/userdata/system/logs/es_launch_stdout.log
```

### Check audio output

```bash
pactl list sinks | grep "Active Port"
```

### List audio sinks

```bash
pactl list short sinks
```

---

## Troubleshooting Matrix

| Symptom | Most Likely Layer |
|---|---|
| One physical button does nothing | Hardware / wiring |
| `/dev/ttyUSB0` missing | USB / FTDI serial interface |
| Serial device exists, no AL3 devices | AL3 bridge |
| `evtest` reports wrong controls | Bridge / decoding |
| `evtest` correct, SDL wrong | SDL |
| SDL correct, EmulationStation wrong | EmulationStation mapping |
| Start and Coin reversed | `es_input.cfg` |
| EXIT does nothing | Bridge / `hotkeygen` |
| EXIT exits while changing volume | Volume-modifier logic |
| Volume shortcut produces no Linux event | AL3 Hotkeys / bridge |
| Volume keys appear but volume does not change | Audio / OS layer |
| Trackball has no movement | Controller / bridge |
| Trackball globally too slow or fast | Bridge sensitivity |
| One spinner game fails | MAME analog / mouse configuration |
| Most games work, one fails | Game-specific configuration |
| One game is oversized | Per-game video viewport |
| No cabinet audio | Audio output / Force_Headphones |
| Audio works until reboot | Audio startup service |

This table is a starting point, not an absolute diagnosis.

---

## The Most Important Question

When troubleshooting, ask:

```text
What is the lowest layer where the behavior becomes wrong?
```

That is usually where the problem lives.

For example:

```text
Physical trackball moves
↓
AL3 controller reports it
↓
AL3 bridge creates REL_X / REL_Y
↓
evtest shows movement
↓
Batocera works
↓
Tempest does not respond correctly

→ investigate Tempest / MAME
```

Do not jump back to:

```text
rewrite al3_bridge.py
```

when all evidence says the bridge is already working.

---

## Final Principle

The project became much easier to maintain when troubleshooting stopped being:

```text
change settings until something works
```

and became:

```text
observe
↓
identify the failing layer
↓
change the smallest possible thing
↓
verify
```

That approach is useful well beyond this particular Arcade Legends cabinet.

---

## Related Documentation

- [Installation](../INSTALL.md)
- [Hardware Conversion](hardware.md)
- [Batocera Configuration](batocera-configuration.md)
- [Controls](controls.md)
- [Game-Specific Fixes](game-fixes.md)
