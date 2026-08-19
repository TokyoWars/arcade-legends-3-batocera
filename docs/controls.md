# Controls and Input Bridge

This document explains how the original Arcade Legends 3 controls are translated into standard Linux input devices that Batocera and MAME can use.

The goal of the project was to preserve the original cabinet controls, trackball, wiring, and controller/interface electronics rather than replace them with generic USB arcade encoders.

The custom AL3 bridge acts as the compatibility layer between the original cabinet hardware and Linux.

---

## Input Architecture

The control path is:

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

The bridge allows the original proprietary cabinet controller to behave like normal Linux input hardware.

---

## Serial Interface

The original Arcade Legends controller/interface connects to the Batocera computer by USB.

Linux detects its FTDI serial interface as:

    FT232R USB UART

and exposes it as:

    /dev/ttyUSB0

The verified working serial configuration is:

    115200 baud
    8 data bits
    no parity
    1 stop bit
    no hardware flow control

or:

    115200 8N1

The controller sends a continuous stream of binary packets.

The packet format observed during this project is:

    19 bytes

with framing bytes:

    Start: 0x5A
    End:   0xA5

The Python bridge reads this stream, identifies valid packets, decodes the controls, and converts them into standard Linux input events.

---

## Why Virtual Linux Devices?

Rather than modifying Batocera, SDL, or MAME to understand the Arcade Legends protocol directly, the bridge uses:

    evdev
    UInput

to create normal Linux input devices.

The software flow becomes:

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

From Batocera's perspective, the original cabinet controls now behave like normal game controllers and relative pointing devices.

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

    REL_X
    REL_Y

This makes the original trackball appear to Linux as a mouse-style relative input device.

### AL3 Hotkeys

Provides cabinet-level functions separate from normal gameplay controls.

The working bridge exposes:

    KEY_EXIT
    KEY_VOLUMEUP
    KEY_VOLUMEDOWN

The volume keys are used by the EXIT + Player 1 Up/Down shortcut described below.

---

## Joystick Handling

The original cabinet joysticks are digital arcade joysticks.

The bridge converts their state into standard Linux directional input.

For example:

    Player 1 LEFT active
            ↓
    al3_bridge.py
            ↓
    AL3 Player 1
            ↓
    Linux directional event
            ↓
    Batocera / MAME

The same applies to:

    UP
    DOWN
    LEFT
    RIGHT

for both players.

---

## Button Handling

Each physical arcade button is decoded from the controller packet and mapped to a Linux joystick button.

The general path is:

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

The hardware-specific translation is handled once in the bridge.

After that, Batocera and MAME can work with the controls normally.

---

## Start and Coin Without Adding Buttons

One of the goals of the conversion was to keep the original control panel intact.

No additional Coin buttons were added.

Instead, the original player button has two behaviors:

    Short press
    → START

    Hold for approximately one second
    → SELECT / COIN

Conceptually:

    Player button pressed
            │
            ├── released quickly
            │       ↓
            │     START
            │
            └── held approximately 1 second
                    ↓
                 SELECT / COIN

This gives Batocera and MAME the functions they need without modifying the cabinet.

---

## SDL Button Mapping

The virtual Player 1 and Player 2 controllers expose eight buttons.

The verified mappings are:

    Button 6 → SELECT
    Button 7 → START

These mappings are stored in:

    /userdata/system/configs/emulationstation/es_input.cfg

The repository includes:

    scripts/update_es_input.py

which updates only:

    AL3 Player 1
    AL3 Player 2

and sets:

    Button 6 → SELECT
    Button 7 → START

This keeps the input chain consistent:

    AL3 bridge
        ↓
    SDL
        ↓
    EmulationStation
        ↓
    MAME

---

## Trackball Handling

The trackball behaves differently from a joystick.

A joystick represents a direction or position.

A trackball represents movement.

For example:

    Joystick:
    LEFT is pressed

    Trackball:
    move a number of units left

The AL3 bridge therefore exposes the original trackball using Linux relative movement events:

    REL_X
    REL_Y

This causes Linux to treat it like a mouse-style device.

That is the type of input many MAME games expect for trackball and some dial/spinner controls.

---

## Trackball Data Flow

The trackball path is:

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

This allows the original trackball to remain connected through the original cabinet electronics.

---

## Trackball Sensitivity

The working bridge applies a 2× multiplier to the raw trackball data:

    dx = signed7(pkt[5]) * 2
    dy = signed7(pkt[6]) * 2

This was the working sensitivity used on the completed cabinet. :contentReference[oaicite:1]{index=1}

The multiplier can be adjusted in `al3_bridge.py` if a different cabinet requires a faster or slower response.

---

## Spinner and Dial Games

Some arcade games use rotary or dial-style controls rather than a trackball.

MAME may expose those controls as:

    DIAL
    PADDLE
    MOUSE

depending on the game.

Because the AL3 bridge already produces relative movement, the original trackball can provide the relative input path needed by some of those games.

Certain games still require game-specific emulator settings.

Tempest is one example.

Its working configuration is documented in:

[game-fixes.md](game-fixes.md)

The project deliberately keeps these fixes game-specific when the rest of the cabinet already works correctly.

---

## Cabinet Exit Control

The original cabinet EXIT control is handled directly by the AL3 bridge.

EXIT by itself behaves normally:

    EXIT
    → Exit the current game and return to EmulationStation

The working bridge does not simply emit a raw exit key and hope the emulator interprets it correctly.

Instead, when EXIT is released, the bridge invokes:

    hotkeygen --send exit

This uses Batocera's normal hotkey mechanism to exit the current emulator. :contentReference[oaicite:2]{index=2}

---

## Cabinet Volume Control

The cabinet also provides volume adjustment without adding dedicated physical volume buttons.

The original EXIT button doubles as a modifier for Player 1 Up and Down.

The behavior is:

    EXIT + Player 1 UP
    → Volume Up

    EXIT + Player 1 DOWN
    → Volume Down

The bridge emits standard Linux multimedia keys:

    KEY_VOLUMEUP
    KEY_VOLUMEDOWN

The first volume adjustment happens immediately.

If the direction remains held, the bridge waits approximately:

    0.35 seconds

and then repeats approximately every:

    0.12 seconds

This makes both small and large volume changes practical. :contentReference[oaicite:3]{index=3}

While EXIT is held, Player 1 vertical joystick movement is suppressed so the game does not also receive Up or Down input.

If EXIT was used as the volume modifier, releasing EXIT does not exit the game.

The final behavior is therefore:

    EXIT alone
    → Exit game

    EXIT + P1 UP
    → Increase volume

    EXIT + P1 DOWN
    → Decrease volume

This provides cabinet-level volume control without adding any new switches or modifying the original control panel.

---

## Why the Volume Shortcut Works Cleanly

The bridge keeps track of whether EXIT has been used for volume.

Conceptually:

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
            volume adjustment
                ↓
            release EXIT
                ↓
            do not exit

This prevents accidental emulator exits while changing the cabinet volume.

---

## Testing the Linux Input Layer

Before troubleshooting Batocera or MAME, verify that Linux receives the expected events.

Run:

    evtest

Identify:

    AL3 Player 1
    AL3 Player 2
    AL3 Trackball
    AL3 Hotkeys

Then test each device.

Player joystick movement should generate directional events.

Arcade buttons should generate button events.

The trackball should generate:

    REL_X
    REL_Y

The volume shortcut should generate:

    KEY_VOLUMEUP
    KEY_VOLUMEDOWN

If the expected events are visible in `evtest`, the original hardware and bridge are probably working correctly.

---

## SDL Testing

The next layer is SDL.

Run:

    export DISPLAY=:0.0
    sdl2-jstest --list

Or:

    export DISPLAY=:0.0
    sdl2-jstest --list | grep -E 'Joystick Name|Number of Buttons|Button code'

The expected virtual controllers include:

    AL3 Player 1
    AL3 Player 2

Each should expose eight buttons.

The verified mappings are:

    Button 6 → SELECT
    Button 7 → START

The troubleshooting path should generally be:

    evtest works
          ↓
    SDL controller test
          ↓
    EmulationStation configuration
          ↓
    MAME

If `evtest` works but SDL does not, the serial bridge is probably not the problem.

If SDL works but one MAME game does not, the issue is probably at the emulator or game configuration layer.

---

## Troubleshooting by Layer

### No response from a physical control

Check:

    physical control
        ↓
    cabinet wiring
        ↓
    original controller/interface

### `/dev/ttyUSB0` is missing

Check:

    USB connection
        ↓
    FTDI serial interface detection
        ↓
    kernel log

Useful command:

    dmesg | grep -Ei 'ftdi|ttyUSB'

### `/dev/ttyUSB0` exists but no AL3 devices appear

Check:

    al3_bridge.py
    AL3_Bridge service
    serial configuration
    Python dependencies
    permissions

Useful commands:

    ps aux | grep '[a]l3_bridge.py'

    batocera-services list | grep -i AL3

    tail -f /userdata/system/al3_bridge.log

### Controls work but volume shortcut does not

Check that the running bridge contains:

    KEY_VOLUMEUP
    KEY_VOLUMEDOWN

and verify:

    EXIT + P1 UP
    EXIT + P1 DOWN

with `evtest`.

### EXIT also exits while changing volume

Verify that the running bridge contains the:

    exit_used_for_volume

logic and that EXIT is only sent through:

    hotkeygen --send exit

when the volume modifier was not used.

### `evtest` works but Batocera does not

Check:

    SDL controller detection
    es_input.cfg
    controller assignment

### Batocera works but one MAME game does not

Check:

    MAME input configuration
    game-specific override

Do not change the controller bridge unless the problem actually exists at the bridge layer.

---

## Design Principle

The controls follow the same philosophy as the rest of the conversion:

> Solve each problem at the narrowest layer possible.

Examples:

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

This prevents global workarounds from creating new problems elsewhere.

---

## Source Code

The working controller bridge is included as:

    scripts/al3_bridge.py

On the cabinet it is installed as:

    /userdata/system/al3_bridge.py

The automatic startup service is:

    services/AL3_Bridge

and is installed on the cabinet as:

    /userdata/system/services/AL3_Bridge

The repository version should remain aligned with the actual known-good cabinet configuration.

---

## Related Documentation

- [Installation](../INSTALL.md)
- [Hardware Conversion](hardware.md)
- [Batocera Configuration](batocera-configuration.md)
- [Game-Specific Fixes](game-fixes.md)
- [Troubleshooting](troubleshooting.md)
