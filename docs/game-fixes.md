# Game-Specific Fixes and Overrides

This section documents several games that required special treatment after the main cabinet configuration was working.

The goal is not to maintain a giant compatibility list.

Instead, these examples demonstrate a reusable principle:

> Keep the global configuration stable, and apply the smallest possible per-game override when a title has unusual input or display requirements.

The working examples in this build are:

* Tempest — spinner/dial-style input
* Pac-Man — vertical display sizing
* Frogger — vertical display sizing

---

# General Strategy

The preferred troubleshooting order is:

```text
1. Verify the game launches
2. Verify controls work
3. Verify video output
4. Identify what is unique about that game
5. Apply the smallest possible override
6. Confirm other games are unchanged
```

This avoids turning one game-specific issue into a cabinet-wide problem.

A useful decision rule is:

```text
Problem found
     │
     ▼
Does it affect most games?
     │
  ┌──┴──┐
 Yes    No
  │      │
  ▼      ▼
Global  Per-game
config  override
```

---

# Where the Overrides Live

The working per-game overrides are stored in:

```text
/userdata/system/batocera.conf
```

The repository also contains a clean reference copy of these settings here:

```text
config/game-overrides.conf
```

The ROM filenames in the configuration must match the actual ROM filenames exactly.

---

# Tempest — Verified Working Configuration

Tempest is a useful example because it is fundamentally different from a normal joystick-driven raster game.

The original arcade machine used:

* a vector display
* a rotary spinner
* analog-style dial input

The normal cabinet joystick configuration was therefore not sufficient by itself.

The working Batocera configuration is:

```ini
mame["tempest.zip"].core=mame
mame["tempest.zip"].emulator=libretro
mame["tempest.zip"].retroarchcore.mame_mouse_enable=enabled
```

These settings are stored in:

```text
/userdata/system/batocera.conf
```

The important setting is:

```ini
mame["tempest.zip"].retroarchcore.mame_mouse_enable=enabled
```

This enables mouse-style relative input for the MAME core.

The complete control path is:

```text
Original cabinet relative control
        ↓
Original AL3 controller
        ↓
Serial packet
        ↓
al3_bridge.py
        ↓
AL3 Trackball
        ↓
Linux REL_X / REL_Y
        ↓
libretro MAME mouse input
        ↓
Tempest dial control
```

This is a good example of why the global arcade control configuration was left unchanged.

Only Tempest receives the special behavior it requires.

---

# Verifying Tempest Launch Behavior

Batocera's launch log is useful for confirming what actually happened.

The relevant file is:

```text
/userdata/system/logs/es_launch_stdout.log
```

A useful command is:

```bash
grep -Ei 'tempest|/usr/bin/mame|mouse|dial|trackball' \
/userdata/system/logs/es_launch_stdout.log
```

This helps verify:

* which emulator/core launched
* whether the expected ROM was used
* whether mouse-related behavior was enabled
* whether a per-game override was actually applied

This is safer than assuming Batocera used the configuration you intended.

---

# Tempest Lesson

The reusable lesson is:

> When one arcade title uses a fundamentally different control type, configure that title at the emulator or game level rather than changing all arcade controls globally.

This same pattern can apply to:

* spinner games
* paddle games
* analog-stick games
* trackball games
* steering-wheel games
* light-gun games

---

# Pac-Man — Verified Working Configuration

Pac-Man launched and played correctly, but its vertical image was too large for the desired visible area of the cabinet display.

The controls worked correctly.

The emulator itself was functioning correctly.

The problem was presentation and scaling.

The working Batocera configuration is:

```ini
mame["pacman.zip"].ratio=custom
mame["pacman.zip"].retroarch.custom_viewport_width=335
mame["pacman.zip"].retroarch.custom_viewport_height=447
mame["pacman.zip"].retroarch.custom_viewport_x=0
mame["pacman.zip"].retroarch.custom_viewport_y=0
mame["pacman.zip"].retroarch.video_viewport_bias_x=0.5
mame["pacman.zip"].retroarch.video_viewport_bias_y=0.5
```

These settings are stored in:

```text
/userdata/system/batocera.conf
```

The effective custom viewport is:

```text
335 × 447
```

The global video configuration remains unchanged.

Conceptually:

```text
Normal arcade games
        ↓
Global Batocera video settings

Pac-Man
        ↓
Custom viewport
335 × 447
```

This keeps Pac-Man within the desired display area while avoiding unintended changes to horizontal games.

---

# Why Pac-Man Needed a Different Viewport

Pac-Man was designed for a vertically oriented arcade monitor.

Its display geometry is fundamentally different from many horizontal arcade games.

A modern emulator may preserve the correct aspect ratio while still producing an image that is physically too large for the usable area of a particular cabinet display.

That means the correct solution is not necessarily:

```text
change the global aspect ratio
```

The safer approach is:

```text
keep global video settings
        +
apply a game-specific viewport
```

---

# Pac-Man Lesson

The reusable rule is:

> If a game looks geometrically correct but is physically too large or too small for the cabinet display, adjust that game's viewport rather than changing global video settings.

This is especially useful for:

* vertical arcade games
* unusual native resolutions
* overscan-sensitive titles
* games with unusual visible areas

---

# Frogger — Verified Working Configuration

Frogger showed the same class of display-sizing issue as Pac-Man.

The game launched correctly.

The controls worked correctly.

The image simply required a smaller custom viewport on this cabinet.

The working configuration is:

```ini
mame["frogger.zip"].ratio=custom
mame["frogger.zip"].retroarch.custom_viewport_width=335
mame["frogger.zip"].retroarch.custom_viewport_height=447
mame["frogger.zip"].retroarch.custom_viewport_x=0
mame["frogger.zip"].retroarch.custom_viewport_y=0
mame["frogger.zip"].retroarch.video_viewport_bias_x=0.5
mame["frogger.zip"].retroarch.video_viewport_bias_y=0.5
```

Again, these settings live in:

```text
/userdata/system/batocera.conf
```

Frogger uses the same custom viewport as Pac-Man:

```text
335 × 447
```

This confirms that some vertical games may benefit from the same cabinet-specific display sizing.

---

# Pac-Man and Frogger Together

Pac-Man and Frogger illustrate an important distinction.

The problem was not:

```text
all games are too large
```

The problem was:

```text
some vertical games need different sizing
```

Those are very different situations.

If the global display settings had been changed to fix Pac-Man and Frogger, many horizontal games could have ended up too small.

The safer approach was:

```text
Stable global configuration
            +
Scoped per-game viewport overrides
```

---

# Verified Override Reference

The complete working example set is:

```ini
# Tempest
mame["tempest.zip"].core=mame
mame["tempest.zip"].emulator=libretro
mame["tempest.zip"].retroarchcore.mame_mouse_enable=enabled

# Pac-Man
mame["pacman.zip"].ratio=custom
mame["pacman.zip"].retroarch.custom_viewport_width=335
mame["pacman.zip"].retroarch.custom_viewport_height=447
mame["pacman.zip"].retroarch.custom_viewport_x=0
mame["pacman.zip"].retroarch.custom_viewport_y=0
mame["pacman.zip"].retroarch.video_viewport_bias_x=0.5
mame["pacman.zip"].retroarch.video_viewport_bias_y=0.5

# Frogger
mame["frogger.zip"].ratio=custom
mame["frogger.zip"].retroarch.custom_viewport_width=335
mame["frogger.zip"].retroarch.custom_viewport_height=447
mame["frogger.zip"].retroarch.custom_viewport_x=0
mame["frogger.zip"].retroarch.custom_viewport_y=0
mame["frogger.zip"].retroarch.video_viewport_bias_x=0.5
mame["frogger.zip"].retroarch.video_viewport_bias_y=0.5
```

These values reflect the working configuration on this cabinet.

They should be treated as examples for other hardware rather than universal values.

---

# Do Not Assume These Viewport Numbers Fit Every Cabinet

The values:

```text
335 × 447
```

are correct for this cabinet's display setup.

Another cabinet may require different values depending on:

* monitor size
* resolution
* bezel
* overscan
* physical visible area
* aspect-ratio handling
* Batocera video mode

The important reusable technique is the per-game custom viewport, not the exact numeric values.

---

# Troubleshooting a Game That Does Not Launch

If one game does not launch, investigate:

```text
ROM filename
ROM set compatibility
BIOS requirements
selected emulator
MAME version
launch command
per-game configuration
```

Check the Batocera launch log first:

```text
/userdata/system/logs/es_launch_stdout.log
```

Useful command:

```bash
grep -Ei '/usr/bin/mame|mame' \
/userdata/system/logs/es_launch_stdout.log
```

For a specific title:

```bash
grep -Ei 'tempest|pacman|frogger' \
/userdata/system/logs/es_launch_stdout.log
```

Do not change the global arcade configuration simply because one ROM does not start.

---

# Troubleshooting Controls in One Game

If controls work in EmulationStation and most MAME games but fail in one title, the likely problem is higher in the stack.

Investigate:

```text
MAME game-specific mapping
control type
analog configuration
mouse input
dial input
```

Do not immediately modify:

```text
al3_bridge.py
es_input.cfg
global Batocera controller mapping
```

unless the same control problem appears across multiple games.

---

# Troubleshooting Spinner / Dial Games

For a spinner or dial title, verify the input path from the bottom upward.

First verify the AL3 relative input device:

```bash
evtest
```

Select:

```text
AL3 Trackball
```

Move the cabinet's relative control and verify:

```text
REL_X
REL_Y
```

events.

If Linux receives those events correctly but the game does not respond, investigate:

```text
MAME mouse input
dial mapping
analog mapping
per-game emulator settings
```

rather than changing the bridge.

---

# Troubleshooting Display Size

If a game:

* launches correctly
* has working controls
* has correct orientation

but appears too large or too small, investigate the video layer.

Possible causes include:

```text
aspect ratio
scaling
viewport
overscan
rotation
game-specific video settings
```

A custom viewport is often preferable when only a small subset of games is affected.

---

# Compare Against a Known-Good Game

When troubleshooting, always compare the failing game against a known-good game.

For example:

```text
Tempest does not respond correctly
Pac-Man works
```

This already proves that:

```text
Batocera is running
MAME is available
basic controls work
the cabinet input stack is alive
```

That narrows the problem considerably.

Similarly:

```text
Pac-Man image too large
horizontal game looks correct
```

strongly suggests a scoped display problem rather than a global display failure.

---

# Test After Every Override

After adding or changing a per-game override, test more than just the affected title.

For an input override:

```text
Test affected game
Test normal joystick game
Test trackball game
```

For a display override:

```text
Test affected game
Test another vertical game
Test horizontal game
```

This verifies that the change is truly scoped.

---

# Preserve the Working Configuration

Before changing important configuration files, make a backup.

For example:

```bash
cp /userdata/system/batocera.conf \
/userdata/system/batocera.conf.backup
```

The repository also contains the verified per-game settings separately:

```text
config/game-overrides.conf
```

This makes it easier to restore or compare the configuration later.

---

# Reusable Principles

The examples in this build represent two main categories.

## Tempest

Problem:

```text
Control-type mismatch
```

Solution:

```text
Per-game MAME input override
```

## Pac-Man

Problem:

```text
Vertical display sizing
```

Solution:

```text
Per-game custom viewport
```

## Frogger

Problem:

```text
Vertical display sizing
```

Solution:

```text
Per-game custom viewport
```

The broader rule is:

> Match the scope of the fix to the scope of the problem.

---

# Final Rule

Do not fix a local problem globally.

Bad pattern:

```text
One game has a spinner problem
        ↓
Change mouse behavior globally
        ↓
Other games behave differently
```

Better pattern:

```text
Stable global configuration
        +
Narrow per-game exception
```

The same applies to video:

```text
One vertical game is too large
        ↓
Do not shrink every game

Instead:

Per-game viewport override
```

This approach keeps the cabinet predictable and makes future troubleshooting much easier.
