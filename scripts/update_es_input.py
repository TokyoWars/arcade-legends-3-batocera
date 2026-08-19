#!/usr/bin/env python3

from pathlib import Path
import xml.etree.ElementTree as ET

cfg = Path(
    "/userdata/system/configs/emulationstation/es_input.cfg"
)

tree = ET.parse(cfg)
root = tree.getroot()

for dev in root.findall("inputConfig"):
    if dev.get("deviceName") not in (
        "AL3 Player 1",
        "AL3 Player 2"
    ):
        continue

    # Remove any previous SELECT entry
    for inp in list(dev.findall("input")):
        if inp.get("name") == "select":
            dev.remove(inp)

    # START = SDL button 7
    for inp in dev.findall("input"):
        if inp.get("name") == "start":
            inp.set("id", "7")

    # SELECT = SDL button 6
    ET.SubElement(dev, "input", {
        "name": "select",
        "type": "button",
        "id": "6",
        "value": "1"
    })

if hasattr(ET, "indent"):
    ET.indent(tree, space="\t")

tree.write(
    cfg,
    encoding="utf-8",
    xml_declaration=True
)

print("Updated START/SELECT mappings.")
