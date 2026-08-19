# Controls and Input Bridge

This section explains how the original arcade cabinet controls are translated into standard Linux input devices that Batocera and MAME can understand.

The key idea is simple:

> Keep the original cabinet controls and controller hardware, then translate their proprietary serial data into normal Linux joystick and mouse events.

This avoids completely rewiring the cabinet into generic USB arcade encoders.

---

# Input Architecture

The complete path is:

```text
Original buttons / joysticks / trackball
        │
        ▼
Original cabinet controller
        │
        ▼
Serial data
        │
        ▼
FTDI USB-to-Serial adapter
        │
        ▼
/dev/ttyUSB0
        │
        ▼
AL3 Python Input Bridge
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

The bridge is therefore the compatibility layer between the old arcade electronics and the modern operating system.

---

# Serial Interface

The cabinet controller connects to the Batocera PC through an FTDI USB-to-serial adapter.

Linux identifies it as an:

```text
FT232R USB UART
```

and exposes it as:

```text
/dev/ttyUSB0
```

The controller communicates using:

```text
115200 baud
8 data bits
no parity
1 stop bit
no hardware flow control
```

This is commonly written as:

```text
115200 8N1
```

---

# Packet Format

The controller sends a continuous stream of binary packets.

The packets use framing bytes:

```text
Start: 0x5A
End:   0xA5
```

The packet length observed during this project is:

```text
19 bytes
```

Conceptually:

```text
0x5A
  │
  ├── control state
  ├── joystick state
  ├── button state
  ├── trackball movement
  └── additional controller data
  │
0xA5
```

The Python bridge watches the serial stream, identifies valid packets, decodes the relevant fields, and converts them into Linux input events.

---

# Why Create Virtual Devices?

Linux already has a standard input subsystem.

Instead of modifying Batocera or MAME to understand the arcade controller protocol directly, the bridge creates normal virtual Linux input devices using:

```text
evdev
UInput
```

The resulting devices behave like physical USB controllers from the point of view of applications.

That means:

```text
Batocera does not need to know about the serial protocol.

MAME does not need to know about the serial protocol.

SDL does not need to know about the serial protocol.
```

They only see normal input devices.

---

# Virtual Devices

The bridge creates four logical devices.

## AL3 Player 1

Contains:

* joystick directions
* Player 1 arcade buttons
* Start
* Select / Coin

## AL3 Player 2

Contains:

* joystick directions
* Player 2 arcade buttons
* Start
* Select / Coin

## AL3 Trackball

Contains:

* horizontal relative movement
* vertical relative movement

The trackball is presented as a mouse-style device rather than joystick axes.

## AL3 Hotkeys

Contains cabinet-level functions that should remain separate from normal gameplay.

For example:

* exit game
* return to EmulationStation

This separation makes controller configuration much cleaner.

---

# Joystick Handling

The cabinet joysticks are digital arcade joysticks.

The bridge converts their state into standard Linux directional input.

Conceptually:

```text
Original controller says:
Player 1 LEFT is active

        ↓

Python bridge

        ↓

Linux input event:
Player 1 LEFT
```

The same applies to:

```text
UP
DOWN
LEFT
RIGHT
```

for both players.

From Batocera's perspective, they are ordinary digital gamepad directions.

---

# Button Handling

Each physical arcade button is decoded from the controller packet and mapped to a Linux joystick button.

The important design principle is that the bridge performs the hardware-specific translation only once.

After that, button assignment is handled normally through Batocera and MAME.

For example:

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
Batocera / MAME function
```

This layering is very useful when troubleshooting.

---

# Player Start and Coin Buttons

One challenge was preserving the original control panel without adding more buttons.

Modern emulators commonly expect separate controls for:

```text
START
SELECT / COIN
```

Instead of drilling another hole in the cabinet, the bridge gives the existing player button two behaviors.

### Short press

```text
START
```

### Long press

Approximately one second:

```text
SELECT / COIN
```

Conceptually:

```text
Player button pressed
        │
        ├── released quickly
        │       ↓
        │     START
        │
        └── held
                ↓
              COIN
```

This makes it possible to insert a virtual coin and start the game using the original cabinet controls.

---

# Why This Is Better Than Adding Buttons

The alternative would have been to add dedicated Coin buttons.

That would work technically, but would require:

* drilling the control panel
* changing the original appearance
* adding wiring
* adding additional physical controls

The software-based approach preserves the cabinet while still providing the functionality required by MAME.

---

# SDL Button Mapping

After the virtual controllers are created, Batocera sees them through SDL.

The final virtual controller exposes enough buttons for both normal arcade controls and Start/Select functionality.

During configuration, the important mappings were:

```text
SELECT = SDL button 6
START  = SDL button 7
```

These are then stored in Batocera's EmulationStation controller configuration:

```text
/userdata/system/configs/emulationstation/es_input.cfg
```

The exact SDL button number is less important than maintaining consistency between:

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

# Trackball Handling

The trackball is fundamentally different from a joystick.

A joystick represents position or direction.

A trackball represents movement.

For example:

```text
Joystick:
LEFT is pressed

Trackball:
move 12 units left
```

The AL3 bridge therefore exposes the trackball using Linux relative movement events:

```text
REL_X
REL_Y
```

This causes Linux to treat the original arcade trackball like a mouse.

That is exactly what many MAME games expect.

---

# Trackball Data Flow

The trackball path is:

```text
Physical trackball movement
        ↓
Original controller
        ↓
Movement encoded in serial packet
        ↓
AL3 bridge calculates X/Y movement
        ↓
REL_X / REL_Y events
        ↓
AL3 Trackball
        ↓
MAME mouse input
```

This allows the original cabinet trackball to remain fully usable.

---

# Spinner and Dial Games

Some arcade games, such as Tempest, were designed around rotary controls rather than trackballs.

MAME commonly represents these as:

```text
DIAL
PADDLE
MOUSE
```

inputs depending on the machine being emulated.

Because the bridge already exposes relative movement to Linux, MAME can use this input for games that need spinner-like behavior.

However, not every game interprets relative controls in exactly the same way.

For that reason, games such as Tempest may still require a per-game MAME input override.

That is documented in:

[`game-fixes.md`](game-fixes.md)

---

# Hotkey Device

Cabinet-level controls should not interfere with gameplay.

For that reason, the bridge creates a separate device:

```text
AL3 Hotkeys
```

This can be used for functions such as:

```text
Exit game
Return to EmulationStation
```

Keeping hotkeys separate also reduces the chance of accidentally assigning a gameplay button to a Batocera system function.

---

# Testing the Input Layer

Before troubleshooting MAME, it is important to verify that Linux is receiving the expected input.

A useful tool is:

```bash
evtest
```

List the available input devices and identify:

```text
AL3 Player 1
AL3 Player 2
AL3 Trackball
AL3 Hotkeys
```

Then select the appropriate device.

For example, moving Player 1's joystick should generate directional events.

Pressing buttons should generate button events.

Moving the trackball should produce:

```text
REL_X
REL_Y
```

events.

---

# SDL Testing

The next layer to verify is SDL.

The general troubleshooting path is:

```text
evtest works
     ↓
SDL controller test
     ↓
Batocera controller configuration
     ↓
MAME
```

If `evtest` works but SDL does not, the serial bridge itself is probably not the problem.

If SDL works but MAME does not, the issue is probably emulator-side configuration.

---

# Troubleshooting by Layer

This project became much easier once control problems were divided into layers.

## No response from a physical button

Check:

```text
button
↓
wiring
↓
original controller
```

## `/dev/ttyUSB0` missing

Check:

```text
USB cable
FTDI adapter
USB detection
kernel log
```

Useful command:

```bash
dmesg | grep -Ei 'ftdi|ttyUSB'
```

## Serial data exists but no AL3 devices

Check:

```text
al3_bridge.py
Python dependencies
serial port configuration
permissions
```

## `evtest` works but Batocera does not

Check:

```text
SDL controller detection
es_input.cfg
controller assignment
```

## Batocera works but one MAME game does not

Check:

```text
MAME input configuration
game-specific override
```

Do not change the bridge unless the problem actually exists at the bridge layer.

---

# Design Principle

The controls follow the same philosophy as the rest of this build:

> Solve each problem at the narrowest layer possible.

Examples:

```text
Physical button failure
→ hardware

Wrong decoded button
→ AL3 bridge

Wrong Batocera assignment
→ EmulationStation configuration

Wrong MAME function
→ MAME mapping

Only one game behaves differently
→ per-game override
```

This avoids creating global workarounds for local problems.

---

# Source Code

The controller bridge source code will be included in:

```text
scripts/al3_bridge.py
```

The repository version should represent the working configuration used by the cabinet.

Before changing the script, it is strongly recommended to keep a known-good copy.

---

# Next

The next document is:

[`game-fixes.md`](game-fixes.md)

This will use several games as examples of how game-specific issues were solved without compromising the global cabinet configuration.

Examples include:

* Tempest — spinner/dial input and launch behavior
* Pac-Man — display sizing
* Frogger — display sizing

The purpose is not to document every game individually.

Instead, these examples demonstrate reusable techniques for handling games that differ from the cabinet's normal configuration.
