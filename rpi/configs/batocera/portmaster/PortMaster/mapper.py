#!/usr/bin/env python3
#
# SPDX-License-Identifier: MIT
#

import xml.etree.ElementTree as ET
import argparse
from pathlib import Path

# ES to SDL2 controller configuration translation map 
TR_MAP = {
    "b" : "a",
    "a" : "b",
    "x" : "y",
    "y" : "x",
    "hotkeyenable" : "guide",
    "hotkey" : "guide",
    "up" : "dpup",
    "down" : "dpdown",
    "left" : "dpleft",
    "right" : "dpright",
    "leftshoulder" : "leftshoulder",
    "l2" : "leftshoulder",
    "leftthumb" : "leftstick",
    "l3" : "leftstick",
    "lefttrigger" : "lefttrigger",
    "rightshoulder" : "rightshoulder",
    "r2" : "rightshoulder",
    "rightthumb" : "rightstick",
    "r3" :  "rightstick",
    "righttrigger": "righttrigger",
    "select" : "back",
    "start" : "start",
    "leftanalogup" : "-lefty",
    "leftanalogleft" : "-leftx",
    "leftanalogdown" : "+lefty",
    "leftanalogright" : "+leftx",
    "rightanalogup" : "-righty",
    "rightanalogleft" : "-rightx",
    "rightanalogdown" : "+righty",
    "rightanalogright" : "+rightx"
}

# Mapping suffix for the Linux platform
MAP_SUFFIX="platform:Linux,"

# -- Helper function --
# Pre Map
# We need here to split joystick input entry into two analog entries (up/down and left/right)
# before we can map them
def premap_input(input_entry):
    input_name = input_entry["name"]
    input_type = input_entry["type"]
    input_id = input_entry["id"]
    input_value = input_entry["value"]


    invert_value = "-1"
    if input_value == "-1":
        invert_value = "1"

    if input_name == "joystick1left":
        leftanalogleft = map_input("leftanalogleft", input_type, input_id, input_value)
        leftanalogright = map_input("leftanalogright", input_type, input_id, invert_value)
        return f"{leftanalogleft}{leftanalogright}"
    elif input_name == "joystick1up":
        leftanalogup = map_input("leftanalogup", input_type, input_id, input_value)
        leftanalogdown = map_input("leftanalogdown", input_type, input_id, invert_value)
        return f"{leftanalogup}{leftanalogdown}"
    elif input_name == "joystick2left":
        rightanalogleft = map_input("rightanalogleft", input_type, input_id, input_value)
        rightanalogright = map_input("rightanalogright", input_type, input_id, invert_value)
        return f"{rightanalogleft}{rightanalogright}"
    elif input_name == "joystick2up":
        rightanalogup = map_input("rightanalogup", input_type, input_id, input_value)
        rightanalogdown = map_input("rightanalogdown", input_type, input_id, invert_value)
        return f"{rightanalogup}{rightanalogdown}"
    else:
         # button or hat
         return f"{map_input(input_name, input_type, input_id, input_value)}"

# Map the actual button/hat/axis
def map_input(input_name, input_type, input_id, input_value):

    # Ignore unknown ES input name
    if not input_name in TR_MAP.keys():
      print(f"Invalid mapping {input_name}.")
      return ""

    # Map ES input name to SDL controller input name
    tr_name = TR_MAP[input_name]

    print(f"{input_name} -> {tr_name}")

    # Axis can be either a stick or an analog trigger
    if input_type == "axis":
        if int(input_value) < 0:
            # Stick (negative)
            return f"{tr_name}:-a{input_id},"
        else:
            # Most (save for a few misbehaved children...) triggers are [0, 1] instead of [-1, 1]
            # Shitty workaround for an emulationstation issue
            if "trigger" in input_name:
                # Analog trigger (full range)
                return f"{tr_name}:a{input_id},"
            else:
                # Stick (positive)
                return f"{tr_name}:+a{input_id},"

    elif input_type == "button":
        # Button
        return f"{tr_name}:b{input_id},"
    
    elif input_type == "hat":
        # Hat
        return f"{tr_name}:h{input_id}.{input_value},"
    
    else:
        # Ignore unknow type
        print(f"Invalid entry {input_type}")
        return ""

def main():

    default_es_input_path = Path.home() / ".config" / "emulationstation" / "es_input.cfg"
    parser = argparse.ArgumentParser(description='ES input to gamecontrollerdb mapper')
    parser.add_argument('-i','--input', default=f"{default_es_input_path}", help='es_input file path (eg: ${HOME}/.config/emulationstation/es_input.cfg)')
    parser.add_argument('gamecontrollerdb_path', help='gamecontrollerdb file path (eg: /tmp/gamecontrollerdb.txt)')

    args = parser.parse_args()

    # List of already configured device GUID
    deviceGUID_list = []

    # es_input.cfg
    es_input_path = Path(args.input)
    # gamecontrollerdb.txt
    gamecontrollerdb_path = Path(args.gamecontrollerdb_path)

    # if the file don't exist don't try to read it
    if gamecontrollerdb_path.is_file():
        with open(gamecontrollerdb_path,"r") as gamecontrollerdb:
            # For each line append the device GUID to deviceGUID_list
            for line in gamecontrollerdb.readlines():
                line = line.strip()
                # Ignore empty and commented lines
                if line.startswith("#") or len(line) == 0:
                    continue
                deviceGUID = line.split(",")[0]
                deviceGUID_list.append(deviceGUID)

    # open gamecontrollerdb.txt for writing (append mode)
    with open(gamecontrollerdb_path, "a") as gamecontrollerdb:

        gamecontrollerdb.write("\n# Custom Entries\n")

        print("## ES Dev Mapper ##")

        # open es_input.cfg (XML)
        tree = ET.parse(es_input_path)
        root = tree.getroot()

        # for each inputConfig entry
        for entry_l1 in root:
            if entry_l1.tag == "inputConfig":
                inputConfig = entry_l1.attrib

                # Get device GUID
                deviceGUID = inputConfig['deviceGUID']

                # Ignore keyboards
                if deviceGUID == "-1":
                    continue

                # Check if GUID exists in gamecontrollerdb.txt
                if deviceGUID in deviceGUID_list:
                    print("Already mapped...")
                    continue

                deviceName = inputConfig['deviceName']

                # Start with an empty mapping for the current input config
                mapping = ""

                # For each input entry (axis, button, hat)
                for entry_l2 in entry_l1:
                    if entry_l2.tag == "input":
                        # Concat input with the mapping entry
                        mapping = f"{mapping}{premap_input(entry_l2.attrib)}"
                
                # Check that there is a mapping
                if len(mapping) > 0:
                    # Add prefix and suffix
                    mapping = f"{deviceGUID},{deviceName},{mapping}{MAP_SUFFIX}"

                    # Write the mapping entry
                    gamecontrollerdb.write(f"{mapping}\n")
                    print(f"{mapping}\n\n")

                else:
                    print("Failed to map anything.")

if __name__ == '__main__':
    main()