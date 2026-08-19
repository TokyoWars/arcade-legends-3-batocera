# Controls and Input Bridge

This document explains how the original Arcade Legends 3 controls are translated into standard Linux input devices that Batocera and MAME can use.

The goal was to preserve the original cabinet controls, trackball, wiring, and controller/interface electronics rather than replace them with generic USB arcade encoders.

The custom AL3 bridge acts as the compatibility layer between the original cabinet hardware and Linux.

---

## Input Architecture

The control path is:

```text
Original buttons / joysticks / trackball
                │
                ▼
Original Arcade Legends controller/interface
                │
                ▼
USB connection
                │
                ▼
FTDI serial interface detected by Linux
                │
                ▼
/dev/ttyUSB0
                │
                ▼
AL3 Python input bridge
                │
                ▼
Linux UInput virtual devices
                │
                ├── AL3 Player 1
                ├── AL3 Player 2
                ├── AL3 Trackball
                └── AL3 Hotkeys
                │
                ▼
SDL / Batocera / MAME
```

The bridge allows the original proprietary cabinet controller to behave like normal Linux input hardware.

---

## Serial Interface

The original Arcade Legends controller/interface connects to the Batocera computer by USB.

Linux detects its FTDI serial interface as:

```text
FT232R USB UART
```

and exposes it as:

```text
/dev/ttyUSB0
```

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

The controller sends a continuous stream of binary packets.

The packet format used by this bridge is:

```text
19 bytes
```

with framing bytes:

```text
Start: 0x5A
End:   0xA5
```

The Python bridge reads the stream, identifies valid packets, decodes the controls, and converts them into standard Linux input events.

---

## Why Virtual Linux Devices?

Rather than modifying Batocera, SDL, or MAME to understand the Arcade Legends protocol directly, the bridge uses Python `evdev` and Linux `UInput` to create standard input devices.

The software flow becomes:

```text
Original proprietary controller protocol
                ↓
al3_bridge.py
                ↓
Standard Linux input devices
                ↓
SDL
                ↓
Batocera
                ↓
MAME
```

The proprietary protocol therefore only has to be translated once.

---

## Virtual Devices

The bridge creates four logical devices.

### AL3 Player 1

Provides:

- Player 1 joystick directions
- Player 1 arcade buttons
- Start
- Select / Coin

### AL3 Player 2

Provides:

- Player 2 joystick directions
- Player 2 arcade buttons
- Start
- Select / Coin

### AL3 Trackball

Provides relative movement:

```text
REL_X
REL_Y
```

This makes the original trackball appear to Linux as a mouse-style relative input device.

### AL3 Hotkeys

The bridge also creates:

```text
AL3 Hotkeys
```

Its advertised key capabilities include:

```text
KEY_EXIT
KEY_VOLUMEUP
KEY_VOLUMEDOWN
```

In the current working implementation, `KEY_VOLUMEUP` and `KEY_VOLUMEDOWN` are emitted through this device.

Game exit is handled separately through Batocera's `hotkeygen` mechanism, described below.

This separation keeps cabinet-level functions away from the normal Player 1 and Player 2 controller mappings.

---

## Joystick Handling

The original cabinet joysticks are digital arcade joysticks.

The bridge converts their state into standard Linux directional input.

For example:

```text
Player 1 LEFT active
        ↓
al3_bridge.py
        ↓
AL3 Player 1
        ↓
Linux directional event
        ↓
Batocera / MAME
```

The same applies to:

```text
UP
DOWN
LEFT
RIGHT
```

for both players.

---

## Button Handling

Each physical arcade button is decoded from the controller packet and mapped to a Linux joystick button.

The general path is:

```text
Physical arcade button
        ↓
Controller packet bit
        ↓
AL3 bridge
        ↓
Linux BTN event
        ↓
SDL button number
        ↓
Batocera / MAME
```

Once the hardware-specific translation is done by the bridge, Batocera and MAME can treat the controls normally.

---

## Start and Coin Without Adding Buttons

One goal of the conversion was to keep the original control panel intact.

No additional Coin buttons were added.

Instead, each original player button has two behaviors:

```text
Short press
→ START

Hold for approximately one second
→ SELECT / COIN
```

Conceptually:

```text
Player button pressed
        │
        ├── released quickly
        │       ↓
        │     START
        │
        └── held approximately 1 second
                ↓
             SELECT / COIN
```

This gives Batocera and MAME the functions they need without physically modifying the cabinet.

---

## SDL Button Mapping

The virtual Player 1 and Player 2 controllers expose eight buttons.

The verified mappings are:

```text
Button 6 → SELECT
Button 7 → START
```

These mappings are stored in:

```text
/userdata/system/configs/emulationstation/es_input.cfg
```

The repository includes:

```text
scripts/update_es_input.py
```

which updates only:

```text
AL3 Player 1
AL3 Player 2
```

and assigns:

```text
Button 6 → SELECT
Button 7 → START
```

The important part is maintaining consistency through the input chain:

```text
AL3 bridge
    ↓
SDL
    ↓
EmulationStation
    ↓
MAME
```

---

## Trackball Handling

A joystick represents a direction or position.

A trackball represents movement.

The AL3 bridge therefore exposes the original trackball using Linux relative movement events:

```text
REL_X
REL_Y
```

This causes Linux to treat the trackball like a mouse-style relative device.

That is the type of input many MAME trackball, dial, and spinner configurations expect.

---

## Trackball Data Flow

The full trackball path is:

```text
Physical trackball movement
        ↓
Original Arcade Legends controller/interface
        ↓
Movement encoded in controller packet
        ↓
al3_bridge.py
        ↓
REL_X / REL_Y
        ↓
AL3 Trackball
        ↓
MAME relative input
```

The trackball remains connected through the original cabinet electronics.

---

## Trackball Sensitivity

The working bridge applies a 2× multiplier to the raw trackball movement:

```python
dx = signed7(pkt[5]) * 2
dy = signed7(pkt[6]) * 2
```

This is the sensitivity currently used on the completed cabinet.

The multiplier can be changed in `al3_bridge.py` if a different cabinet requires faster or slower trackball movement.

---

## Spinner and Dial Games

Some arcade games use rotary or dial-style controls rather than conventional digital joysticks.

MAME may represent those inputs as:

```text
DIAL
PADDLE
MOUSE
```

depending on the game.

Because the AL3 bridge already produces relative movement, that input can also be used by games requiring spinner-style movement.

Some games still require a game-specific emulator setting.

Tempest is one example.

Its working configuration is documented in:

[game-fixes.md](game-fixes.md)

The design principle is to keep such changes game-specific when the rest of the cabinet already works correctly.

---

## Cabinet Exit Control

The original cabinet EXIT control retains its normal purpose:

```text
EXIT
→ Exit the current game and return to EmulationStation
```

The current bridge handles EXIT on release.

If EXIT was not used as a volume modifier, the bridge runs:

```text
hotkeygen --send exit
```

This uses Batocera's normal emulator-exit mechanism rather than relying on a game-specific keyboard mapping.

---

## Cabinet Volume Control

No dedicated volume buttons were added to the control panel.

Instead, the EXIT button doubles as a volume modifier for Player 1 Up and Down:

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

through the `AL3 Hotkeys` virtual input device.

The first volume adjustment happens immediately.

If the joystick remains held, the bridge waits approximately:

```text
0.35 seconds
```

before repeating, and then repeats approximately every:

```text
0.12 seconds
```

This allows both small adjustments and larger volume changes.

---

## Preventing Accidental Movement and Exit

When EXIT is held, Player 1 vertical joystick movement is suppressed:

```text
EXIT + P1 UP
→ Volume Up only

EXIT + P1 DOWN
→ Volume Down only
```

The game does not simultaneously receive Player 1 Up or Down.

The bridge also tracks whether EXIT was used for volume.

Conceptually:

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

This prevents accidentally leaving a game while adjusting cabinet volume.

---

## Final Cabinet Control Shortcuts

The main cabinet-level behaviors are:

```text
Tap Player 1 button
→ Player 1 START

Hold Player 1 button ~1 second
→ Player 1 COIN / SELECT

Tap Player 2 button
→ Player 2 START

Hold Player 2 button ~1 second
→ Player 2 COIN / SELECT

EXIT
→ Exit current game

EXIT + Player 1 UP
→ Volume Up

EXIT + Player 1 DOWN
→ Volume Down
```

These functions require no additional physical buttons.

---

## Testing the Linux Input Layer

Before troubleshooting Batocera or MAME, verify what Linux receives.

Run:

```bash
evtest
```

Look for:

```text
AL3 Player 1
AL3 Player 2
AL3 Trackball
AL3 Hotkeys
```

Test each device.

Player joystick movement should generate directional events.

Arcade buttons should generate button events.

The trackball should generate:

```text
REL_X
REL_Y
```

The volume shortcut should generate:

```text
KEY_VOLUMEUP
KEY_VOLUMEDOWN
```

If the expected events appear in `evtest`, the original hardware and bridge are probably working correctly.

---

## SDL Testing

The next layer is SDL.

Run:

```bash
export DISPLAY=:0.0
sdl2-jstest --list
```

Or:

```bash
export DISPLAY=:0.0
sdl2-jstest --list | grep -E 'Joystick Name|Number of Buttons|Button code'
```

The expected player controllers are:

```text
AL3 Player 1
AL3 Player 2
```

Each should expose eight buttons.

The verified mappings are:

```text
Button 6 → SELECT
Button 7 → START
```

The troubleshooting path should normally be:

```text
evtest works
      ↓
SDL controller test
      ↓
EmulationStation configuration
      ↓
MAME
```

If `evtest` works but SDL does not, the serial bridge is probably not the problem.

If SDL works and most games work but one MAME game does not, the issue is probably at the emulator or per-game configuration layer.

---

## Troubleshooting by Layer

### No response from a physical control

Check:

```text
physical control
    ↓
cabinet wiring
    ↓
original controller/interface
```

### `/dev/ttyUSB0` is missing

Check:

```text
USB connection
    ↓
FTDI serial interface detection
    ↓
kernel log
```

Useful command:

```bash
dmesg | grep -Ei 'ftdi|ttyUSB'
```

### `/dev/ttyUSB0` exists but no AL3 devices appear

Check:

```text
al3_bridge.py
AL3_Bridge service
serial configuration
Python dependencies
permissions
```

Useful commands:

```bash
ps aux | grep '[a]l3_bridge.py'
```

```bash
batocera-services list | grep -i AL3
```

```bash
tail -f /userdata/system/al3_bridge.log
```

### Controls work but volume does not

Verify that the running bridge contains:

```text
KEY_VOLUMEUP
KEY_VOLUMEDOWN
```

Then test:

```text
EXIT + P1 UP
EXIT + P1 DOWN
```

with `evtest`.

### EXIT also exits while changing volume

Verify that the bridge contains:

```text
exit_used_for_volume
```

and that EXIT is only passed to:

```text
hotkeygen --send exit
```

when the volume modifier was not used.

### Trackball is too slow or too fast

The working cabinet uses:

```python
dx = signed7(pkt[5]) * 2
dy = signed7(pkt[6]) * 2
```

Adjust the multiplier only if necessary.

### `evtest` works but Batocera does not

Check:

```text
SDL controller detection
es_input.cfg
controller assignment
```

### Batocera works but one MAME game does not

Check:

```text
MAME input configuration
control type
game-specific override
```

Do not change the controller bridge unless the problem actually exists at the bridge layer.

---

## Design Principle

The controls follow the same philosophy as the rest of the conversion:

> Solve each problem at the narrowest layer possible.

Examples:

```text
Physical button failure
→ hardware / wiring

Wrong decoded control
→ AL3 bridge

Wrong Start / Select assignment
→ EmulationStation configuration

Wrong MAME function
→ MAME mapping

Only one game behaves differently
→ per-game override
```

This prevents global workarounds from creating problems elsewhere.

---

## Source Code

The working controller bridge is included as:

```text
scripts/al3_bridge.py
```

On the cabinet it is installed as:

```text
/userdata/system/al3_bridge.py
```

The automatic startup service is:

```text
services/AL3_Bridge
```

and is installed on the cabinet as:

```text
/userdata/system/services/AL3_Bridge
```

The repository version should remain synchronized with the known-good bridge running on the cabinet.

---

## Related Documentation

- [Installation](../INSTALL.md)
- [Hardware Conversion](hardware.md)
- [Batocera Configuration](batocera-configuration.md)
- [Game-Specific Fixes](game-fixes.md)
- [Troubleshooting](troubleshooting.md)
