# Controls and Input Bridge

This document explains how the original Arcade Legends 3 controls are translated into standard Linux input devices that Batocera and MAME can use.

The goal of the project was to keep the original cabinet controls, trackball, wiring, and controller/interface electronics rather than replace everything with generic USB arcade encoders.

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

The controller sends a continuous stream of binary data.

The packet format observed during this project is:

    19 bytes

with framing bytes:

    Start: 0x5A
    End:   0xA5

The Python bridge reads this stream, identifies valid packets, decodes the relevant controls, and converts them into standard Linux input events.

---

## Why Virtual Linux Devices?

Rather than modifying Batocera, SDL, or MAME to understand the original Arcade Legends protocol directly, the bridge uses:

    evdev
    UInput

to create standard Linux input devices.

From the software side:

    Original proprietary controller protocol
                ↓
    al3_bridge.py
                ↓
    Normal Linux input devices
                ↓
    SDL
                ↓
    Batocera
                ↓
    MAME

Batocera and MAME therefore do not need to understand the original controller protocol.

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

Provides cabinet-level hotkey input separate from normal gameplay controls.

The verified bridge exposes:

    KEY_EXIT

through this device.

Keeping cabinet-level functions separate reduces the chance of accidentally assigning a normal gameplay button to a system function.

---

## Joystick Handling

The original cabinet joysticks are digital arcade joysticks.

The bridge converts their state into standard Linux directional input.

For example:

    Original controller:
    Player 1 LEFT active

            ↓

    al3_bridge.py

            ↓

    Linux input:
    Player 1 LEFT

The same applies to:

    UP
    DOWN
    LEFT
    RIGHT

for both players.

From Batocera's perspective, these are normal digital controller directions.

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

The bridge handles the hardware-specific translation once.

After that, controller assignment is handled normally by Batocera and MAME.

---

## Start and Coin Without Adding Buttons

One of the goals of the conversion was to preserve the original control panel without drilling holes for additional Coin buttons.

The existing player button therefore has two software-defined behaviors.

Short press:

    START

Long press of approximately one second:

    SELECT / COIN

Conceptually:

    Player button pressed
            │
            ├── released quickly
            │       ↓
            │     START
            │
            └── held about 1 second
                    ↓
                 COIN / SELECT

This allows the original physical controls to provide both emulator functions without modifying the panel.

---

## SDL Button Mapping

The virtual Player 1 and Player 2 controllers expose eight buttons.

The verified mappings are:

    SELECT = SDL button 6
    START  = SDL button 7

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

The important part is maintaining consistency through the whole input chain:

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

A joystick represents direction or position.

A trackball represents movement.

For example:

    Joystick:
    LEFT is pressed

    Trackball:
    move 12 units left

The AL3 bridge therefore exposes the trackball using Linux relative movement events:

    REL_X
    REL_Y

This causes Linux to treat the original arcade trackball like a mouse.

That is the type of input many MAME games expect.

---

## Trackball Data Flow

The full trackball path is:

    Physical trackball movement
            ↓
    Original Arcade Legends controller/interface
            ↓
    Movement encoded in serial packet
            ↓
    al3_bridge.py
            ↓
    REL_X / REL_Y
            ↓
    AL3 Trackball
            ↓
    MAME relative input

This allows the original cabinet trackball to remain in use without rewiring it to a separate USB trackball controller.

---

## Spinner and Dial Games

Some arcade games use rotary or dial-style controls rather than a trackball.

MAME may represent those controls as:

    DIAL
    PADDLE
    MOUSE

depending on the game.

Because the AL3 bridge already produces relative movement, that input can also be used by games that expect spinner-style movement.

Some games still require a game-specific emulator setting.

For example, Tempest required MAME mouse input to be enabled.

That configuration is documented in:

[game-fixes.md](game-fixes.md)

The important design rule is to keep such fixes game-specific when the rest of the cabinet already works correctly.

---

## Cabinet Exit Control

The bridge creates a separate:

    AL3 Hotkeys

device for cabinet-level system functions.

The verified bridge maps the cabinet EXIT control to:

    KEY_EXIT

This keeps the exit function separate from Player 1 and Player 2 gameplay buttons.

The intended behavior is:

    EXIT
    → leave the current game and return to EmulationStation

---

## Cabinet Volume Control

A cabinet-level volume-control shortcut was also used during the build so volume could be changed without adding dedicated physical volume buttons.

The intended cabinet behavior was:

    EXIT + Player 1 UP
    → Volume Up

    EXIT + Player 1 DOWN
    → Volume Down

while:

    EXIT alone
    → Exit the current game

This preserves the original control panel and reuses existing controls as a modifier combination.

However, the current repository version of `al3_bridge.py` only exposes the EXIT control through `AL3 Hotkeys` as `KEY_EXIT`.

The exact software implementation that turns:

    EXIT + Player 1 UP
    EXIT + Player 1 DOWN

into system volume commands is not currently included in the repository.

For that reason, this behavior is documented here as part of the working cabinet design, but it should not be assumed to be provided by `al3_bridge.py` alone.

The missing volume-control implementation should be added to the repository once the exact working configuration is recovered.

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

The cabinet exit control should generate the event associated with:

    KEY_EXIT

If the expected event is visible in `evtest`, the original hardware and bridge are probably working correctly.

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

If SDL works but one MAME game does not, the issue is probably higher in the emulator/game configuration layer.

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
    service status
    serial configuration
    Python dependencies
    permissions

Useful commands:

    ps aux | grep '[a]l3_bridge.py'

    batocera-services list | grep -i AL3

    tail -f /userdata/system/al3_bridge.log

### `evtest` works but Batocera does not

Check:

    SDL controller detection
    es_input.cfg
    controller assignment

### Batocera works but one MAME game does not

Check:

    MAME input configuration
    game-specific override

Do not change the bridge unless the problem actually exists at the bridge layer.

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
