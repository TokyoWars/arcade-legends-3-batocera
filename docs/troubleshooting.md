# Troubleshooting Guide

This section documents the troubleshooting method used throughout the cabinet conversion.

The most important principle is:

> Troubleshoot from the bottom of the stack upward.

Do not begin by changing MAME settings if Linux is not seeing the controller correctly.

Do not change the controller bridge if the problem exists only in one game.

The system is easiest to diagnose when each layer is tested independently.

---

# Troubleshooting Stack

Use this order:

```text
Physical control
      ↓
Cabinet wiring
      ↓
Original controller
      ↓
Serial interface
      ↓
AL3 bridge
      ↓
Linux input
      ↓
SDL
      ↓
Batocera
      ↓
MAME
      ↓
Individual game
```

Only move to the next layer after confirming the previous one works.

---

# 1. Check the Physical Controls

Start with the simplest possible causes.

Check:

* joystick movement
* pushbuttons
* player buttons
* trackball movement
* cabinet connectors
* loose plugs
* damaged wiring
* recently moved cables

If only one physical control fails, the problem is more likely to be:

```text
switch
wiring
connector
controller input
```

than a Batocera-wide issue.

---

# 2. Verify the USB-to-Serial Adapter

The cabinet controller reaches the Batocera PC through an FTDI USB-to-serial adapter.

Check whether Linux detected it:

```bash
dmesg | grep -Ei 'ftdi|ttyUSB'
```

The expected device is:

```text
/dev/ttyUSB0
```

You can also check directly:

```bash
ls -l /dev/ttyUSB*
```

If `/dev/ttyUSB0` does not exist, investigate:

* USB cable
* USB port
* FTDI adapter
* connector seating
* kernel detection

Do not troubleshoot MAME until the serial device exists.

---

# 3. Verify Serial Communication

Once `/dev/ttyUSB0` exists, confirm that the controller is actually transmitting data.

The controller uses:

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

The controller sends repeating binary packets framed approximately as:

```text
0x5A ... 0xA5
```

with the packet format decoded by the AL3 bridge.

If the serial interface exists but no useful data is arriving, investigate:

* cable routing
* controller power
* serial wiring
* FTDI interface
* baud rate
* serial configuration

---

# 4. Verify the AL3 Bridge Is Running

The custom controller bridge is stored under:

```text
/userdata/system/al3_bridge.py
```

Its job is to read `/dev/ttyUSB0` and create Linux virtual input devices.

Expected virtual devices include:

```text
AL3 Player 1
AL3 Player 2
AL3 Trackball
AL3 Hotkeys
```

If `/dev/ttyUSB0` works but these devices do not appear, the likely problem is in:

```text
Python bridge
startup mechanism
dependencies
permissions
serial parsing
```

rather than Batocera or MAME.

---

# 5. Verify Linux Input With `evtest`

Before testing Batocera, verify the virtual devices directly.

Run:

```bash
evtest
```

Look for devices named:

```text
AL3 Player 1
AL3 Player 2
AL3 Trackball
AL3 Hotkeys
```

Select one and test it.

For Player 1:

* move joystick up
* move joystick down
* move joystick left
* move joystick right
* press arcade buttons
* tap the player button
* hold the player button

Expected behavior should appear as Linux input events.

---

# Player Button Test

The player button has two functions.

A short press should generate:

```text
START
```

A longer press should generate:

```text
SELECT / COIN
```

If the correct events appear in `evtest`, the AL3 bridge is doing its job.

If Batocera behaves incorrectly after that, move upward in the stack.

---

# Trackball Test

Select:

```text
AL3 Trackball
```

in `evtest`.

Move the trackball.

You should see relative movement events such as:

```text
REL_X
REL_Y
```

If these events appear correctly, the hardware, serial communication, and bridge are all working.

Any remaining problem is likely higher in the stack.

---

# 6. Verify SDL

Batocera relies heavily on SDL for controller handling.

If `evtest` works but Batocera does not, check whether SDL sees the virtual controllers correctly.

The expected path is:

```text
Linux input
   ↓
SDL
   ↓
EmulationStation
```

This is an important boundary.

If Linux sees correct events but SDL does not, do not modify the serial bridge unless there is additional evidence that the bridge is wrong.

---

# 7. Check EmulationStation Controller Mapping

Batocera's controller mappings are stored under:

```text
/userdata/system/configs/emulationstation/es_input.cfg
```

The AL3 player devices should have valid mappings.

Important functions include:

```text
joystick directions
arcade buttons
START
SELECT
```

In the working configuration, Start and Select were assigned consistently with the virtual controller layout.

If a controller works in Linux but not in EmulationStation, check this file and the Batocera controller configuration.

---

# 8. Determine Whether the Problem Is Global or Game-Specific

Before changing anything, test more than one game.

Ask:

```text
Does the problem happen everywhere?
```

If yes, investigate global configuration.

If no, investigate the game or emulator.

A useful decision tree is:

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

This one decision can save a large amount of unnecessary work.

---

# 9. Check Batocera Launch Logs

One of the most useful files is:

```text
/userdata/system/logs/es_launch_stdout.log
```

This shows what Batocera actually launched.

For MAME:

```bash
grep -Ei '/usr/bin/mame|mame' \
/userdata/system/logs/es_launch_stdout.log
```

For a specific game:

```bash
grep -Ei 'tempest' \
/userdata/system/logs/es_launch_stdout.log
```

or:

```bash
grep -Ei 'pacman|frogger' \
/userdata/system/logs/es_launch_stdout.log
```

This helps confirm:

* correct ROM name
* selected emulator
* MAME executable
* launch arguments
* whether an override was applied
* whether an unexpected configuration was used

Always prefer launch evidence over assumptions.

---

# 10. Troubleshooting a Game That Does Not Launch

If one game does not launch, investigate:

```text
ROM name
ROM set compatibility
BIOS requirements
selected emulator
MAME version
launch command
per-game configuration
```

Check the launch log first.

Do not change the global arcade configuration simply because one ROM does not start.

---

# 11. Troubleshooting Controls in One Game

If controls work in EmulationStation and most MAME games, but fail in one title, the likely problem is:

```text
MAME game-specific mapping
control type
analog configuration
mouse input
dial input
```

This was the type of issue encountered with games such as Tempest.

The global controller bridge should remain unchanged unless evidence shows that its output is wrong.

---

# 12. Troubleshooting Spinner / Dial Games

Games using spinner-style controls require different treatment from normal digital joystick games.

Examples may use MAME inputs such as:

```text
DIAL
PADDLE
MOUSE
```

If the cabinet's relative input works in Linux but the game does not respond correctly, verify:

1. `AL3 Trackball` generates relative events.
2. MAME has mouse input enabled where required.
3. The game's control is mapped to the expected MAME analog input.
4. The launch command includes any required override.

For Tempest troubleshooting, this command was useful:

```bash
grep -Ei 'tempest|/usr/bin/mame|mouse|dial|trackball' \
/userdata/system/logs/es_launch_stdout.log
```

---

# 13. Troubleshooting Display Size

If a game:

* launches correctly
* has working controls
* has correct orientation

but appears too large or too small, the problem is likely in the video layer.

Investigate:

```text
aspect ratio
scaling
viewport
overscan
rotation
game-specific video settings
```

Do not automatically change the global display configuration.

Pac-Man and Frogger were examples where a game-specific display adjustment was preferable.

---

# 14. Compare a Working Game

When troubleshooting, always compare the failing game against a known-good game.

For example:

```text
Tempest fails
Pac-Man works
```

That immediately tells you that:

```text
PC works
Batocera works
MAME launches
basic controller path works
```

which greatly narrows the problem.

Similarly:

```text
Pac-Man image wrong
horizontal game looks correct
```

strongly suggests a scoped display issue rather than a global video failure.

---

# 15. Check Recent Changes First

If the cabinet was working and suddenly stops working, begin with whatever changed most recently.

Examples:

* cable moved
* controller remapped
* Batocera setting changed
* emulator changed
* script edited
* USB port changed
* game override added

Avoid changing five things at once.

Make one change, test, and record the result.

---

# 16. Back Up Before Editing

Before modifying an important configuration file, make a copy.

For example:

```bash
cp /userdata/system/configs/emulationstation/es_input.cfg \
/userdata/system/configs/emulationstation/es_input.cfg.backup
```

For scripts:

```bash
cp /userdata/system/al3_bridge.py \
/userdata/system/al3_bridge.py.backup
```

This gives you a known rollback point.

---

# 17. Useful Commands

## Find the serial adapter

```bash
dmesg | grep -Ei 'ftdi|ttyUSB'
```

## Check serial device

```bash
ls -l /dev/ttyUSB*
```

## Test Linux input devices

```bash
evtest
```

## Inspect MAME launches

```bash
grep -Ei '/usr/bin/mame|mame' \
/userdata/system/logs/es_launch_stdout.log
```

## Inspect a specific game

```bash
grep -Ei 'tempest|pacman|frogger' \
/userdata/system/logs/es_launch_stdout.log
```

## Look for mouse / dial configuration

```bash
grep -Ei 'mouse|dial|trackball' \
/userdata/system/logs/es_launch_stdout.log
```

---

# 18. Troubleshooting Matrix

| Symptom                          | Most Likely Layer             |
| -------------------------------- | ----------------------------- |
| One physical button does nothing | Hardware / wiring             |
| `/dev/ttyUSB0` missing           | USB / FTDI                    |
| Serial exists, no AL3 devices    | AL3 bridge                    |
| `evtest` incorrect               | Bridge / input decoding       |
| `evtest` correct, Batocera wrong | SDL / EmulationStation        |
| Batocera works, MAME wrong       | MAME                          |
| Most games work, one fails       | Game-specific                 |
| Controls work, image wrong       | Video configuration           |
| Only spinner game fails          | Analog / mouse / dial mapping |

This table is not absolute, but it is a good starting point.

---

# 19. General Rule

When troubleshooting, always ask:

```text
What is the lowest layer where the behavior becomes wrong?
```

That is usually where the problem lives.

For example:

```text
Physical control works
Serial works
evtest works
Batocera works
Tempest does not

→ investigate Tempest / MAME
```

not:

```text
rewrite the controller bridge
```

---

# Final Principle

The project became significantly easier to maintain once troubleshooting stopped being:

```text
change settings until it works
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

That approach is useful far beyond this particular cabinet.
