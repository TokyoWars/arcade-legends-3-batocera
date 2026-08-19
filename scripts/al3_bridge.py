#!/usr/bin/env python3

import os
import time
import subprocess
from evdev import UInput, ecodes as e, AbsInfo

PORT = "/dev/ttyUSB0"
LONG_PRESS = 1.0

subprocess.run([
    "stty", "-F", PORT,
    "115200", "raw", "-echo",
    "cs8", "-parenb", "-cstopb",
    "-crtscts", "-ixon", "-ixoff"
], check=True)

hat = AbsInfo(
    value=0,
    min=-1,
    max=1,
    fuzz=0,
    flat=0,
    resolution=0
)

pad_caps = {
    e.EV_KEY: [
        e.BTN_SOUTH,
        e.BTN_EAST,
        e.BTN_WEST,
        e.BTN_NORTH,
        e.BTN_TL,
        e.BTN_TR,
        e.BTN_SELECT,
        e.BTN_START
    ],
    e.EV_ABS: [
        (e.ABS_HAT0X, hat),
        (e.ABS_HAT0Y, hat)
    ]
}

mouse_caps = {
    e.EV_KEY: [e.BTN_LEFT],
    e.EV_REL: [e.REL_X, e.REL_Y]
}

hotkey_caps = {
    e.EV_KEY: [
        e.KEY_EXIT,
        e.KEY_VOLUMEUP,
        e.KEY_VOLUMEDOWN
    ]
}

p1 = UInput(pad_caps, name="AL3 Player 1")
p2 = UInput(pad_caps, name="AL3 Player 2")
mouse = UInput(mouse_caps, name="AL3 Trackball")
hotkeys = UInput(hotkey_caps, name="AL3 Hotkeys")

print("AL3 bridge running", flush=True)
print("Tap player button = START", flush=True)
print("Hold player button 1 second = COIN", flush=True)


def pressed(byte, bit):
    return (byte & (1 << bit)) == 0


def signed7(v):
    if v & 0x40:
        return v - 0x80
    return v


button_codes = [
    e.BTN_WEST,
    e.BTN_NORTH,
    e.BTN_TL,
    e.BTN_SOUTH,
    e.BTN_EAST,
    e.BTN_TR
]


def emit_pad(ui, state, previous):
    if state == previous:
        return previous

    x, y, buttons = state

    if previous is None:
        old_x = 0
        old_y = 0
        old_buttons = [False] * 6
    else:
        old_x, old_y, old_buttons = previous

    changed = False

    if x != old_x:
        ui.write(e.EV_ABS, e.ABS_HAT0X, x)
        changed = True

    if y != old_y:
        ui.write(e.EV_ABS, e.ABS_HAT0Y, y)
        changed = True

    for code, new, old in zip(button_codes, buttons, old_buttons):
        if new != old:
            ui.write(e.EV_KEY, code, int(new))
            changed = True

    if changed:
        ui.syn()

    return state


def pulse(ui, code):
    ui.write(e.EV_KEY, code, 1)
    ui.syn()
    time.sleep(0.03)
    ui.write(e.EV_KEY, code, 0)
    ui.syn()


def handle_player_button(ui, is_down, tracker, now):
    if is_down:
        if tracker["since"] is None:
            tracker["since"] = now
            tracker["coin_sent"] = False

        elif (
            not tracker["coin_sent"]
            and now - tracker["since"] >= LONG_PRESS
        ):
            pulse(ui, e.BTN_SELECT)
            tracker["coin_sent"] = True

    else:
        if tracker["since"] is not None:
            if not tracker["coin_sent"]:
                pulse(ui, e.BTN_START)

            tracker["since"] = None
            tracker["coin_sent"] = False


p1_tracker = {"since": None, "coin_sent": False}
p2_tracker = {"since": None, "coin_sent": False}

last_p1 = None
last_p2 = None
last_exit = False
exit_used_for_volume = False
last_volume_key = None
next_volume_repeat = 0.0

fd = os.open(PORT, os.O_RDONLY)
buf = bytearray()

try:
    while True:
        data = os.read(fd, 256)

        if not data:
            continue

        buf.extend(data)

        while True:
            try:
                i = buf.index(0x5A)
            except ValueError:
                buf.clear()
                break

            if i:
                del buf[:i]

            if len(buf) < 19:
                break

            if buf[18] != 0xA5:
                del buf[0]
                continue

            pkt = bytes(buf[:19])
            del buf[:19]

            b1 = pkt[1]
            b2 = pkt[2]
            b3 = pkt[3]
            b4 = pkt[4]

            # Player 1
            p1_up    = pressed(b1, 0)
            p1_down  = pressed(b1, 1)
            p1_left  = pressed(b1, 2)
            p1_right = pressed(b1, 3)
            p1_start = pressed(b1, 4)

            p1_x = -1 if p1_left and not p1_right else \
                    1 if p1_right and not p1_left else 0

            p1_y = -1 if p1_up and not p1_down else \
                    1 if p1_down and not p1_up else 0

            p1_buttons = [
                pressed(b1, 6),
                pressed(b1, 7),
                pressed(b2, 0),
                pressed(b2, 1),
                pressed(b2, 2),
                pressed(b2, 3)
            ]

            # EXIT acts as a volume modifier for P1 Up/Down
            exit_now = pressed(b4, 0)
            volume_now = time.monotonic()

            volume_key = None

            if exit_now and p1_up and not p1_down:
                volume_key = e.KEY_VOLUMEUP
            elif exit_now and p1_down and not p1_up:
                volume_key = e.KEY_VOLUMEDOWN

            # Do not send vertical joystick movement to the game
            # while EXIT is being used as the modifier.
            p1_y_out = 0 if exit_now else p1_y

            if exit_now and volume_key is not None:
                exit_used_for_volume = True

                # Immediate first step, then repeat while held.
                if last_volume_key != volume_key:
                    pulse(hotkeys, volume_key)
                    last_volume_key = volume_key
                    next_volume_repeat = volume_now + 0.35

                elif volume_now >= next_volume_repeat:
                    pulse(hotkeys, volume_key)
                    next_volume_repeat = volume_now + 0.12

            elif exit_now:
                last_volume_key = None
                next_volume_repeat = 0.0

            else:
                last_volume_key = None
                next_volume_repeat = 0.0

            p1_state = (p1_x, p1_y_out, p1_buttons)
            last_p1 = emit_pad(p1, p1_state, last_p1)

            # Player 2
            p2_up    = pressed(b2, 4)
            p2_down  = pressed(b2, 5)
            p2_left  = pressed(b2, 6)
            p2_right = pressed(b2, 7)
            p2_start = pressed(b3, 0)

            p2_x = -1 if p2_left and not p2_right else \
                    1 if p2_right and not p2_left else 0

            p2_y = -1 if p2_up and not p2_down else \
                    1 if p2_down and not p2_up else 0

            p2_buttons = [
                pressed(b3, 2),
                pressed(b3, 3),
                pressed(b3, 4),
                pressed(b3, 5),
                pressed(b3, 6),
                pressed(b3, 7)
            ]

            p2_state = (p2_x, p2_y, p2_buttons)
            last_p2 = emit_pad(p2, p2_state, last_p2)

            now = time.monotonic()

            handle_player_button(
                p1, p1_start, p1_tracker, now
            )

            handle_player_button(
                p2, p2_start, p2_tracker, now
            )

            # EXIT alone exits the game.
            # If EXIT was used with P1 Up/Down, do not exit.
            if last_exit and not exit_now:
                if not exit_used_for_volume:
                    subprocess.run(
                        ["hotkeygen", "--send", "exit"],
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL
                    )

                exit_used_for_volume = False

            last_exit = exit_now

            # Trackball
            # Arcade trackball sensitivity multiplier
            dx = signed7(pkt[5]) * 2
            dy = signed7(pkt[6]) * 2

            if dx or dy:
                if dx:
                    mouse.write(e.EV_REL, e.REL_X, dx)
                if dy:
                    mouse.write(e.EV_REL, e.REL_Y, dy)
                mouse.syn()

finally:
    os.close(fd)
    p1.close()
    p2.close()
    mouse.close()
    hotkeys.close()
