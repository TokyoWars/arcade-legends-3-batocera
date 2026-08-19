# Batocera Configuration

This document describes the Batocera-side configuration used to integrate the original Arcade Legends 3 hardware, preserve the custom controller behavior across reboots, and keep game-specific fixes isolated from the global configuration.

The general philosophy of the project is:

> Keep global Batocera configuration simple, place custom logic under `/userdata`, and use per-game overrides only when a specific game genuinely requires them.

This makes the cabinet easier to maintain, troubleshoot, and rebuild.

---

## Why `/userdata` Matters

Batocera is designed as an appliance-style operating system.

The project therefore keeps custom scripts, services, controller mappings, and configuration under persistent storage whenever possible:

```text
/userdata/
```

The most important project files are stored under:

```text
/userdata/system/
```

This includes:

```text
/userdata/system/al3_bridge.py
/userdata/system/al3_bridge.log
/userdata/system/services/AL3_Bridge
/userdata/system/services/Force_Headphones
/userdata/system/configs/emulationstation/es_input.cfg
/userdata/system/batocera.conf
```

Keeping the customizations under `/userdata` allows them to survive normal reboots and Batocera updates.

---

## Controller Startup Architecture

The original Arcade Legends controller/interface connects to the Batocera computer by USB.

Linux detects its FTDI serial interface as:

```text
FT232R USB UART
```

and exposes it as:

```text
/dev/ttyUSB0
```

The controller path is:

```text
Original Arcade Legends controls
            ↓
Original controller/interface
            ↓
USB
            ↓
FTDI serial interface
            ↓
/dev/ttyUSB0
            ↓
al3_bridge.py
            ↓
Linux UInput devices
            ↓
Batocera / SDL / MAME
```

The bridge creates:

```text
AL3 Player 1
AL3 Player 2
AL3 Trackball
AL3 Hotkeys
```

These devices allow Batocera to work with the original cabinet hardware without requiring the original controls to appear as standard USB gamepads.

---

## AL3 Bridge Service

The controller bridge is:

```text
/userdata/system/al3_bridge.py
```

It is started automatically by the Batocera service:

```text
/userdata/system/services/AL3_Bridge
```

The service waits until:

```text
/dev/ttyUSB0
```

exists before starting the Python bridge.

If the bridge exits, the service waits briefly and starts it again.

This prevents a USB startup timing issue from leaving the cabinet without controls after boot.

Useful checks are:

```bash
batocera-services list | grep -i AL3
```

and:

```bash
ps aux | grep '[a]l3_bridge.py'
```

The bridge log is:

```text
/userdata/system/al3_bridge.log
```

and can be monitored with:

```bash
tail -f /userdata/system/al3_bridge.log
```

---

## Controller Configuration

Once the bridge creates the virtual Linux input devices, Player 1 and Player 2 are mapped through EmulationStation.

The relevant mapping file is:

```text
/userdata/system/configs/emulationstation/es_input.cfg
```

The virtual player devices expose:

- joystick directions
- six arcade buttons
- Select / Coin
- Start

The verified SDL mappings are:

```text
Button 6 → SELECT
Button 7 → START
```

The repository contains:

```text
scripts/update_es_input.py
```

which updates only:

```text
AL3 Player 1
AL3 Player 2
```

in `es_input.cfg`.

This avoids modifying unrelated controllers.

---

## Start and Coin Behavior

The original player buttons were kept physically unchanged.

The bridge interprets each player button according to how long it is held.

```text
Short press
→ START

Hold approximately one second
→ SELECT / COIN
```

The long-press behavior is implemented in `al3_bridge.py`.

From Batocera's point of view, these appear as normal controller buttons.

This avoids drilling additional Coin buttons into the original control panel.

---

## Cabinet Exit Handling

The original cabinet EXIT control is also retained.

The current working bridge handles EXIT on button release.

If EXIT was not used as the volume modifier, the bridge executes:

```text
hotkeygen --send exit
```

The normal behavior is therefore:

```text
EXIT
→ Exit current game
→ Return to EmulationStation
```

Using `hotkeygen` lets Batocera perform the emulator exit rather than relying on a game-specific key assignment.

---

## Cabinet Volume Control

No dedicated volume buttons were added to the cabinet.

Instead, the EXIT button also acts as a modifier for Player 1 Up and Down.

The working controls are:

```text
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

through the:

```text
AL3 Hotkeys
```

virtual input device.

The first volume change occurs immediately.

If the joystick remains held, repeat begins after approximately:

```text
0.35 seconds
```

and then repeats approximately every:

```text
0.12 seconds
```

This allows both quick volume taps and larger volume adjustments.

---

## Preventing Accidental Exit and Movement

The bridge distinguishes between EXIT being used normally and EXIT being used as the volume modifier.

Conceptually:

```text
EXIT pressed
    │
    ├── no P1 Up/Down
    │       ↓
    │   EXIT released
    │       ↓
    │   hotkeygen --send exit
    │
    └── P1 Up/Down used
            ↓
        adjust volume
            ↓
        EXIT released
            ↓
        do not exit
```

While EXIT is held, Player 1 vertical joystick movement is suppressed.

Therefore:

```text
EXIT + P1 UP
```

changes volume but does not also move Player 1 upward in the game.

The same applies to:

```text
EXIT + P1 DOWN
```

This makes the shortcut usable during gameplay without generating unwanted movement or accidentally exiting the emulator.

---

## AL3 Hotkeys Device

The bridge creates a dedicated virtual device named:

```text
AL3 Hotkeys
```

Its advertised key capabilities include:

```text
KEY_EXIT
KEY_VOLUMEUP
KEY_VOLUMEDOWN
```

In the current working bridge:

```text
KEY_VOLUMEUP
KEY_VOLUMEDOWN
```

are emitted through this virtual device for cabinet volume control.

The actual emulator exit action is handled separately through:

```text
hotkeygen --send exit
```

This distinction is important when troubleshooting.

---

## Trackball Configuration

The original Arcade Legends trackball remains connected through the original cabinet controller/interface.

The bridge converts its movement into Linux relative mouse input:

```text
REL_X
REL_Y
```

The path is:

```text
Physical trackball
        ↓
Original controller/interface
        ↓
Serial packet
        ↓
al3_bridge.py
        ↓
REL_X / REL_Y
        ↓
AL3 Trackball
        ↓
MAME
```

This allows Batocera and MAME to use the original trackball without replacing its controller electronics.

---

## Trackball Sensitivity

The working bridge applies a 2× sensitivity multiplier to the raw trackball movement:

```python
dx = signed7(pkt[5]) * 2
dy = signed7(pkt[6]) * 2
```

This is the sensitivity currently used on the completed cabinet.

The multiplier is part of the bridge rather than a global MAME setting.

If another cabinet requires a different overall trackball speed, this value can be adjusted.

If only one game has incorrect analog sensitivity, the game's own configuration should be investigated first.

---

## Audio Configuration

The Batocera computer sends analog audio into the original cabinet audio path.

On this computer, Batocera did not always select the intended analog output after boot.

The repository therefore includes:

```text
services/Force_Headphones
```

which is installed as:

```text
/userdata/system/services/Force_Headphones
```

The working service selects:

```text
analog-output-headphones
```

on the sink:

```text
alsa_output.pci-0000_00_1f.3.analog-stereo
```

The sink name is specific to the computer used in this cabinet.

Another Batocera computer may use a different sink name.

Available sinks can be checked with:

```bash
pactl list short sinks
```

The active port can be checked with:

```bash
pactl list sinks | grep "Active Port"
```

---

## MAME Configuration Strategy

Most games should use the same basic global configuration.

The preferred model is:

```text
Global configuration
        +
Per-game exceptions
```

rather than modifying the global emulator setup whenever one game behaves differently.

Arcade games can use very different original controls and display formats, including:

- digital joysticks
- trackballs
- spinners
- analog controls
- horizontal displays
- vertical displays
- vector displays

A setting that solves one title can easily create problems for another.

---

## Per-Game Overrides

When a game requires different behavior, the fix is limited to that game whenever practical.

Examples from this cabinet include:

```text
Tempest
→ relative-input / mouse configuration

Pac-Man
→ CRT viewport adjustment

Frogger
→ CRT viewport adjustment
```

The repository includes the verified examples in:

```text
config/game-overrides.conf
```

The active cabinet settings are stored in:

```text
/userdata/system/batocera.conf
```

The general rule is:

> If the problem exists in one game, fix one game. If the problem exists everywhere, fix the global configuration.

---

## Tempest Example

Tempest required relative input for its dial/spinner-style control.

The working per-game configuration is:

```text
mame["tempest.zip"].core=mame
mame["tempest.zip"].emulator=libretro
mame["tempest.zip"].retroarchcore.mame_mouse_enable=enabled
```

The important point is not that every spinner game should use this exact configuration.

The important point is that Tempest's input issue was solved at the game level rather than by changing the entire arcade controller configuration.

---

## Pac-Man and Frogger Examples

Pac-Man and Frogger launched and played correctly but were too large for the usable visible area of this cabinet's CRT.

The solution was to use a per-game custom viewport.

The working cabinet-specific dimensions are:

```text
335 × 447
```

These dimensions should not be treated as universal settings.

They are specific to the physical CRT and visible area of this cabinet.

The useful technique is the per-game viewport override, not the particular numbers.

---

## Launch Logs

One of the most useful Batocera troubleshooting files is:

```text
/userdata/system/logs/es_launch_stdout.log
```

This shows what Batocera actually launched.

For MAME:

```bash
grep -Ei '/usr/bin/mame|mame' \
/userdata/system/logs/es_launch_stdout.log
```

For Tempest:

```bash
grep -Ei 'tempest|/usr/bin/mame|mouse|dial|trackball' \
/userdata/system/logs/es_launch_stdout.log
```

For Pac-Man and Frogger:

```bash
grep -Ei 'pacman|frogger' \
/userdata/system/logs/es_launch_stdout.log
```

The launch log is more useful than guessing which emulator, core, or arguments Batocera selected.

---

## Testing Linux Input

Before changing Batocera or MAME settings, test the input at the Linux layer.

Run:

```bash
evtest
```

The bridge should expose:

```text
AL3 Player 1
AL3 Player 2
AL3 Trackball
AL3 Hotkeys
```

Use `evtest` to verify:

- joystick movement
- arcade buttons
- Start
- Coin / Select
- trackball movement
- volume keys

The trackball should produce:

```text
REL_X
REL_Y
```

The volume shortcut should produce:

```text
KEY_VOLUMEUP
KEY_VOLUMEDOWN
```

If Linux already receives the correct event, troubleshooting should move higher in the stack.

---

## SDL Testing

After Linux input is confirmed, verify SDL.

Run:

```bash
export DISPLAY=:0.0
sdl2-jstest --list
```

A focused version is:

```bash
export DISPLAY=:0.0
sdl2-jstest --list | grep -E 'Joystick Name|Number of Buttons|Button code'
```

The expected player devices are:

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

---

## Configuration Layers

The final system can be viewed as separate layers:

```text
1. Cabinet Hardware
        ↓
2. Controller / FTDI Serial Interface
        ↓
3. AL3 Input Bridge
        ↓
4. Linux / SDL Input
        ↓
5. EmulationStation / Batocera
        ↓
6. MAME
        ↓
7. Per-Game Overrides
```

Each layer has a specific responsibility.

This makes troubleshooting much easier than treating every problem as a Batocera problem.

---

## Avoiding Unnecessary Global Changes

The troubleshooting sequence used throughout the build is:

```text
Verify hardware
      ↓
Verify /dev/ttyUSB0
      ↓
Verify AL3 bridge
      ↓
Verify Linux input
      ↓
Verify SDL
      ↓
Verify EmulationStation
      ↓
Verify MAME
      ↓
Verify individual game
```

Only change the layer where the problem actually appears.

For example:

```text
evtest is wrong
→ investigate bridge / hardware

evtest correct, EmulationStation wrong
→ investigate controller mapping

Most games work, one fails
→ investigate that game

One game is oversized
→ use a per-game viewport
```

This greatly reduces the chance of solving one problem while creating several new ones.

---

## Configuration Persistence

Custom cabinet behavior should survive:

- reboot
- shutdown
- emulator restart
- normal Batocera use

For that reason, project-specific files are kept under:

```text
/userdata
```

Important files should be tested again after reboot to verify that the configuration remains active.

---

## Recommended Backup

The cabinet depends on several custom files.

Important backup targets include:

```text
/userdata/system/al3_bridge.py
/userdata/system/services/AL3_Bridge
/userdata/system/services/Force_Headphones
/userdata/system/configs/emulationstation/es_input.cfg
/userdata/system/batocera.conf
```

The GitHub repository also contains copies of the custom bridge, helper script, service files, documentation, and verified game overrides.

This makes recovery easier if:

- the Batocera storage device fails
- Batocera is reinstalled
- the computer is replaced
- a configuration file is accidentally overwritten

---

## Final Configuration Philosophy

The project ultimately follows three rules:

1. **Preserve the original cabinet hardware where practical.**
2. **Solve problems at the lowest layer where they actually exist.**
3. **Use per-game overrides instead of global changes when only one game needs a fix.**

That combination keeps the cabinet understandable and maintainable while still allowing unusual hardware such as the original Arcade Legends controller and trackball to work with Batocera.

---

## Related Documentation

- [Installation](../INSTALL.md)
- [Hardware Conversion](hardware.md)
- [Controls](controls.md)
- [Game-Specific Fixes](game-fixes.md)
- [Troubleshooting](troubleshooting.md)
