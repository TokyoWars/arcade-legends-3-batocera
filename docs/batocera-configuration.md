# Batocera Configuration

This section documents the Batocera configuration used to integrate the original arcade cabinet controls, preserve custom behavior across reboots, and support game-specific overrides without making unnecessary global changes.

The general philosophy was:

> Keep global Batocera configuration simple, put custom logic under `/userdata`, and use per-game overrides only when a specific game genuinely requires them.

This made the system easier to maintain and troubleshoot.

---

# Why `/userdata` Matters

Batocera is designed as an appliance-style operating system.

The core operating system is not intended to be modified like a normal Linux installation.

Persistent user configuration should therefore be stored under:

```text
/userdata/
```

This became the foundation of the project.

Custom files, scripts, controller mappings, emulator configuration, and startup logic were kept in persistent locations whenever possible.

---

# Important Persistent Paths

Some of the important paths used during this project include:

```text
/userdata/system/
```

for system-level customizations and scripts.

The custom arcade controller bridge was stored under:

```text
/userdata/system/al3_bridge.py
```

Batocera's EmulationStation controller configuration is stored under:

```text
/userdata/system/configs/emulationstation/es_input.cfg
```

Other emulator-specific or system-specific configuration is also kept under the `/userdata/system/configs/` tree.

---

# Startup Architecture

The custom arcade controls need to be available before games are launched.

The startup process therefore follows this general pattern:

```text
Batocera boots
      ↓
/dev/ttyUSB0 appears
      ↓
AL3 input bridge starts
      ↓
Virtual input devices are created
      ↓
EmulationStation starts
      ↓
Batocera sees normal controllers
```

The important part is that the AL3 bridge runs automatically rather than requiring manual intervention after every boot.

The bridge creates the virtual Linux input devices used throughout the system:

```text
AL3 Player 1
AL3 Player 2
AL3 Trackball
AL3 Hotkeys
```

---

# Controller Configuration

Once the AL3 bridge creates Linux input devices, Batocera treats them like normal controllers.

The two player devices are mapped through EmulationStation.

The player controls include:

* joystick directions
* arcade action buttons
* Start
* Select / Coin

The controller mapping is stored in:

```text
/userdata/system/configs/emulationstation/es_input.cfg
```

During the build, the Player 1 and Player 2 virtual controllers were configured so that the Start and Select functions matched the custom behavior produced by the AL3 bridge.

The resulting controller exposes the required buttons to SDL and Batocera without requiring a keyboard during normal operation.

---

# Start and Coin Behavior

The physical player buttons were intentionally kept unchanged.

Instead of adding additional cabinet buttons, the AL3 bridge interprets the same physical button differently depending on how long it is pressed.

A short press generates:

```text
START
```

A long press generates:

```text
SELECT / COIN
```

From Batocera's point of view, these appear as ordinary controller buttons.

This means the cabinet can support modern emulator expectations while preserving the original control panel layout.

---

# Exit / Hotkey Handling

An arcade cabinet needs a reliable way to leave a game and return to EmulationStation.

That functionality is handled through the dedicated virtual hotkey device:

```text
AL3 Hotkeys
```

This separates cabinet-level functions from normal player controls.

The benefit of this approach is that game controls remain game controls, while front-end actions such as exiting a game can be handled independently.

---

# MAME Configuration Strategy

Most arcade games should use the same basic MAME configuration.

The preferred configuration model is:

```text
Global MAME configuration
        +
Per-game exceptions
```

rather than creating one heavily customized global configuration that tries to accommodate every game.

This is particularly important because MAME emulates games with very different original hardware.

Games may use:

* digital joysticks
* trackballs
* spinners
* analog controls
* horizontal monitors
* vertical monitors
* vector displays

A single global configuration cannot always represent all of those correctly.

---

# Per-Game Overrides

When a game requires different behavior, the change should be limited to that game.

Examples from this build include:

* Tempest
* Pac-Man
* Frogger

These games were not used as the basis for the global configuration.

Instead, they serve as examples of when exceptions are appropriate.

For example:

```text
Most games
    ↓
Global settings

Tempest
    ↓
Input-specific override

Pac-Man
    ↓
Display-specific override

Frogger
    ↓
Display-specific override
```

This prevents a fix for one game from creating problems in dozens of others.

---

# Tempest as an Example

Tempest is a useful example because it does not behave like a typical joystick-driven raster game.

It was originally designed around:

* a vector display
* a rotary spinner-style input

The cabinet's normal joystick configuration was therefore not sufficient on its own.

The solution was handled as a game-specific MAME exception rather than by changing the controls globally.

This preserved normal joystick behavior for the rest of the arcade library.

---

# Pac-Man and Frogger as Examples

Pac-Man and Frogger presented a different issue.

Both are vertical-format games.

The games launched and played correctly, but their displayed image required adjustment for the physical cabinet screen.

Rather than changing the cabinet's global screen configuration, each game received its own display-related override.

This demonstrates an important rule used throughout the project:

> If the problem exists in one game, fix one game.

> If the problem exists across the entire system, fix the global configuration.

---

# Logs Used During Troubleshooting

Batocera provides several useful logs when diagnosing launch and emulator problems.

One of the most useful during this project was:

```text
/userdata/system/logs/es_launch_stdout.log
```

This helped identify the actual emulator command being launched and confirm whether MAME-specific arguments were being used.

For example, launch behavior could be checked with commands such as:

```bash
grep -Ei 'tempest|/usr/bin/mame|mouse|dial|trackball' \
/userdata/system/logs/es_launch_stdout.log
```

This was particularly useful while troubleshooting Tempest.

---

# Testing Linux Input Devices

Before changing Batocera or MAME settings, the input devices were tested directly at the Linux level.

Useful tools included:

```bash
evtest
```

and SDL controller testing utilities.

The troubleshooting sequence was generally:

```text
Does Linux see the physical input?
        ↓
Does the AL3 bridge generate the correct event?
        ↓
Does SDL see the controller?
        ↓
Does Batocera see the controller?
        ↓
Does MAME see the controller?
        ↓
Does the specific game map it correctly?
```

This avoids changing emulator configuration when the real problem is lower in the stack.

---

# Avoiding Unnecessary Global Changes

During the project, several issues initially looked like global Batocera problems but turned out to be narrower.

The general rule became:

1. Verify the hardware.
2. Verify Linux input.
3. Verify SDL.
4. Verify Batocera.
5. Verify MAME.
6. Only then create a game-specific override if necessary.

This significantly reduced the risk of fixing one problem while creating another.

---

# Configuration Persistence

Any custom behavior required for the cabinet should survive:

* reboot
* shutdown
* normal Batocera use
* emulator restarts

For that reason, custom files were stored under `/userdata`.

The project avoids relying on temporary changes made directly to Batocera's read-only system partition.

When a configuration change was made, it was tested again after reboot to confirm that it remained active.

---

# Recommended Backup

Because the cabinet now depends on several custom files, it is a good idea to back up the persistent configuration tree.

The most important areas are:

```text
/userdata/system/
/userdata/system/configs/
/userdata/system/al3_bridge.py
```

A copy of the custom scripts should also be maintained in this GitHub repository.

That allows the system to be rebuilt if:

* the storage device fails
* Batocera is reinstalled
* the PC is replaced
* configuration is accidentally overwritten

---

# Configuration Layers

The final system can be viewed as five configuration layers:

```text
1. Cabinet Hardware
        ↓
2. AL3 Input Bridge
        ↓
3. Linux / SDL Input
        ↓
4. Batocera / MAME
        ↓
5. Per-Game Overrides
```

Each layer has a specific responsibility.

This makes the system much easier to understand than treating every issue as a Batocera problem.

---

# Next

The next document is:

[`controls.md`](controls.md)

That section will go deeper into the AL3 controller bridge, including:

* serial packet handling
* joystick decoding
* button decoding
* Start / Coin logic
* trackball handling
* virtual Linux input devices
* hotkey behavior
