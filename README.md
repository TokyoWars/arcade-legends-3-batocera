# Arcade Legends 3 → Batocera

This project documents the conversion of a **Chicago Gaming Company Arcade Legends 3** cabinet to **Batocera**, while preserving as much of the original arcade hardware as practical.

![Arcade Legends 3 cabinet running Batocera](images/Console.jpeg)

The original game computer was replaced by a laptop running Batocera, but the cabinet itself remains largely original.

The conversion keeps the original CRT, control panel, joysticks, buttons, trackball, speakers, wiring, and controller/interface electronics.

The goal was simple:

> **Modernize the game platform without unnecessarily replacing the arcade machine around it.**

---

## What Was Preserved

The project retains:

- Original Arcade Legends cabinet and artwork
- Original CRT monitor
- Original two-player control panel
- Original joysticks and buttons
- Original trackball
- Original speakers and audio path
- Original cabinet wiring
- Original controller/interface electronics

The original motherboard is no longer used as the game computer.

Batocera now runs on a laptop connected to the existing cabinet hardware.

For the full physical conversion with photos, see:

**[Hardware Conversion](docs/hardware.md)**

---

## How the Conversion Works

The original Arcade Legends controls do not appear to Linux as standard USB gamepads.

The cabinet controller/interface connects to the Batocera laptop by USB.

Linux detects its FTDI serial interface as:

```text
FT232R USB UART
/dev/ttyUSB0
```

The verified serial configuration is:

```text
115200 8N1
```

The Arcade Legends controller sends 19-byte packets framed by:

```text
0x5A ... 0xA5
```

A custom Python bridge reads those packets and converts the original controls into standard Linux UInput devices.

```text
Original controls and trackball
            ↓
Original Arcade Legends controller/interface
            ↓
USB connection
            ↓
FTDI serial interface
/dev/ttyUSB0
            ↓
al3_bridge.py
            ↓
AL3 Player 1
AL3 Player 2
AL3 Trackball
AL3 Hotkeys
            ↓
Linux input
            ↓
SDL / Batocera / MAME
```

The working bridge is included in:

```text
scripts/al3_bridge.py
```

On the cabinet it is installed as:

```text
/userdata/system/al3_bridge.py
```

---

## Controls

The original two-player control panel remains in use.

The bridge creates:

```text
AL3 Player 1
AL3 Player 2
AL3 Trackball
AL3 Hotkeys
```

### Start and Coin

No additional Coin buttons were added to the cabinet.

The original player buttons provide two functions:

```text
Tap player button
→ START

Hold for approximately one second
→ SELECT / COIN
```

The verified SDL mappings are:

```text
Button 6 → SELECT / COIN
Button 7 → START
```

This keeps the original control panel intact without drilling additional holes.

---

## Cabinet Volume Control

The original cabinet EXIT button also doubles as a volume-control modifier.

The verified working behavior is:

```text
EXIT
→ Exit current game

EXIT + Player 1 UP
→ Volume Up

EXIT + Player 1 DOWN
→ Volume Down
```

The bridge emits standard Linux multimedia keys:

```text
KEY_VOLUMEUP
KEY_VOLUMEDOWN
```

The first volume adjustment occurs immediately.

If the joystick direction remains held, volume repeat begins after approximately:

```text
0.35 seconds
```

and then repeats approximately every:

```text
0.12 seconds
```

While EXIT is being used as the volume modifier, Player 1 vertical joystick movement is suppressed.

This prevents the game from receiving an Up or Down command while changing volume.

If EXIT was used for volume control, releasing it does **not** exit the game.

EXIT by itself exits through Batocera using:

```text
hotkeygen --send exit
```

This allows full cabinet volume control without adding dedicated volume buttons or changing the original control panel.

For the complete control implementation, see:

**[Controls](docs/controls.md)**

---

## Trackball

The original Arcade Legends trackball remains connected through the original controller/interface electronics.

The bridge converts its movement into Linux relative mouse events:

```text
REL_X
REL_Y
```

The working cabinet configuration applies a **2× sensitivity multiplier** to the raw trackball movement:

```python
dx = signed7(pkt[5]) * 2
dy = signed7(pkt[6]) * 2
```

This was the sensitivity that worked correctly on this cabinet.

The multiplier can be adjusted in `al3_bridge.py` if a different trackball speed is preferred.

The relative input also provides the input path needed by certain trackball, dial, and spinner-style games.

---

## Automatic Startup

The AL3 controller bridge starts automatically using Batocera's service mechanism.

The repository includes:

```text
services/AL3_Bridge
```

On the cabinet it is installed as:

```text
/userdata/system/services/AL3_Bridge
```

The service:

1. waits for `/dev/ttyUSB0`
2. starts the Python bridge
3. logs its output
4. restarts the bridge if it exits

This avoids startup timing problems if the controller interface is not immediately available when Batocera boots.

---

## Video and Audio

The Batocera laptop connects to the cabinet through three primary paths:

```text
USB
→ original controller/interface electronics

VGA
→ original CRT video path

Analog audio
→ original cabinet audio path
```

The original CRT remains in use.

The original cabinet speakers and audio system also remain in use.

This was an important part of the conversion because the objective was to retain the look and feel of the original Arcade Legends cabinet instead of converting it into a generic LCD-based arcade machine.

---

## Audio Output Service

Batocera did not always select the required analog output automatically after boot.

The project therefore includes:

```text
services/Force_Headphones
```

This forces the required:

```text
analog-output-headphones
```

port on the configured audio sink.

The sink name included in the service is specific to the Batocera computer used in this build and may need to be changed on another system.

---

## Game-Specific Examples

The project avoids changing global emulator settings to solve problems that affect only one game.

Instead, game-specific fixes are applied only where needed.

### Tempest

Tempest is an example of a game that required relative mouse input for its dial/spinner-style control.

The working configuration is:

```text
mame["tempest.zip"].core=mame
mame["tempest.zip"].emulator=libretro
mame["tempest.zip"].retroarchcore.mame_mouse_enable=enabled
```

### Pac-Man and Frogger

Pac-Man and Frogger are examples of games that required custom viewport settings because the default image was larger than the usable visible area of this cabinet's CRT.

The working viewport on this cabinet is:

```text
335 x 447
```

Those dimensions are specific to this machine and should be treated as an example rather than a universal setting.

The general rule used throughout the project is:

> **If the problem exists in one game, fix one game. If it exists everywhere, fix the global configuration.**

The verified examples are documented in:

**[Game-Specific Fixes](docs/game-fixes.md)**

The repository also includes:

```text
config/game-overrides.conf
```

with the current verified per-game overrides.

---

## Installation

For the condensed setup procedure, see:

**[INSTALL.md](INSTALL.md)**

The installation guide covers:

1. verifying the original controller interface
2. installing the AL3 bridge
3. installing and enabling the Batocera service
4. updating EmulationStation Start/Select mappings
5. verifying input with Linux and SDL tools
6. configuring the cabinet audio output
7. applying per-game overrides where needed

---

## Important Batocera Paths

The main persistent files used by this project are:

```text
/userdata/system/al3_bridge.py
/userdata/system/al3_bridge.log
/userdata/system/services/AL3_Bridge
/userdata/system/services/Force_Headphones
/userdata/system/configs/emulationstation/es_input.cfg
/userdata/system/batocera.conf
```

Project-specific customizations are kept under:

```text
/userdata
```

so they persist across normal Batocera reboots and updates.

---

## Troubleshooting Philosophy

The most useful lesson from this project was to troubleshoot from the lowest layer upward.

```text
Physical control
      ↓
Original cabinet wiring
      ↓
Controller/interface board
      ↓
USB / FTDI serial interface
      ↓
/dev/ttyUSB0
      ↓
AL3 bridge
      ↓
Linux input
      ↓
EmulationStation / Batocera
      ↓
MAME
      ↓
Individual game
```

For example:

```text
/dev/ttyUSB0 missing
→ USB / controller interface problem

evtest shows no input
→ bridge or controller problem

evtest works but EmulationStation does not
→ controller mapping problem

EmulationStation works but one game does not
→ emulator or game configuration problem

Only one game is oversized
→ per-game viewport problem
```

Useful commands include:

```bash
ls -l /dev/ttyUSB*
dmesg | grep -i -E 'ftdi|ttyUSB'
ps aux | grep '[a]l3_bridge.py'
batocera-services list | grep -i AL3
evtest
export DISPLAY=:0.0
sdl2-jstest --list
tail -f /userdata/system/al3_bridge.log
```

For the complete troubleshooting process, see:

**[Troubleshooting](docs/troubleshooting.md)**

---

## Design Philosophy

This conversion deliberately avoids unnecessary hardware replacement.

The project does **not** rely on:

- completely rewiring the control panel
- replacing the original controls with generic USB arcade kits
- replacing the original CRT with an LCD
- adding separate Coin buttons
- adding separate volume buttons
- applying game-specific fixes globally

Instead, the original cabinet hardware is preserved wherever practical and compatibility issues are solved in software.

The general principle is:

> **Solve each problem at the narrowest layer where the problem actually exists.**

---

## Repository Structure

```text
arcade-legends-3-batocera/
├── README.md
├── INSTALL.md
├── LICENSE
│
├── config/
│   └── game-overrides.conf
│
├── docs/
│   ├── hardware.md
│   ├── batocera-configuration.md
│   ├── controls.md
│   ├── game-fixes.md
│   └── troubleshooting.md
│
├── images/
│
├── scripts/
│   ├── al3_bridge.py
│   └── update_es_input.py
│
└── services/
    ├── AL3_Bridge
    └── Force_Headphones
```

---

## Documentation

- **[Installation](INSTALL.md)**
- **[Hardware Conversion](docs/hardware.md)**
- **[Batocera Configuration](docs/batocera-configuration.md)**
- **[Controls](docs/controls.md)**
- **[Game-Specific Fixes](docs/game-fixes.md)**
- **[Troubleshooting](docs/troubleshooting.md)**

The hardware guide includes photos of the actual cabinet, original electronics, CRT, control panel, Batocera laptop, and physical connections.

---

## Current Status

The cabinet is operational with:

- original two-player arcade controls
- original trackball
- Start/Coin long-press behavior
- EXIT-based cabinet volume controls
- original CRT
- original cabinet speakers and audio path
- automatic controller bridge startup
- persistent Batocera configuration
- game-specific input overrides
- game-specific CRT viewport overrides

The project is intended both as a record of this particular conversion and as a reference for others who want to modernize an Arcade Legends cabinet without unnecessarily replacing the original hardware.

---

## License

Released under the **[MIT License](LICENSE)**.
