
# SPDX-License-Identifier: MIT

# System imports
import copy
import datetime
import fnmatch
import json
import math
import os
import pathlib
import platform
import re
import subprocess
import zipfile

from pathlib import Path

# Included imports

from loguru import logger

# Module imports
from .config import *
from .info import *
from .util import *


# This maps device name to HW_INFO, also includes manufacturer and compatible cfw.
DEVICES = {
    # Anbernic
    "Anbernic RG353 M/V/P": {"device": "rg353m",      "manufacturer": "Anbernic",  "cfw": ["ArkOS"]},
    "Anbernic RG353 VS/PS": {"device": "rg353ps",     "manufacturer": "Anbernic",  "cfw": ["ArkOS", "ROCKNIX"]},
    "Anbernic RG351MP":     {"device": "rg351mp",     "manufacturer": "Anbernic",  "cfw": ["ArkOS", "AmberELEC", "TheRA"]},
    "Anbernic RG503":       {"device": "rg503",       "manufacturer": "Anbernic",  "cfw": ["ArkOS", "ROCKNIX"]},
    "Anbernic RG552":       {"device": "rg552",       "manufacturer": "Anbernic",  "cfw": ["AmberELEC", "ROCKNIX"]},
    "Anbernic RGCUBEXX":    {"device": "rgcubexx",    "manufacturer": "Anbernic",  "cfw": ["muOS", "Knulli", "ROCKNIX"]},
    "Anbernic RG40XX H":    {"device": "rg40xx-h",    "manufacturer": "Anbernic",  "cfw": ["muOS", "Knulli", "ROCKNIX"]},
    "Anbernic RG40XX V":    {"device": "rg40xx-v",    "manufacturer": "Anbernic",  "cfw": ["muOS", "Knulli", "ROCKNIX"]},
    "Anbernic RG35XX PLUS": {"device": "rg35xx-plus", "manufacturer": "Anbernic",  "cfw": ["muOS", "Knulli", "ROCKNIX"]},
    "Anbernic RG35XX H":    {"device": "rg35xx-h",    "manufacturer": "Anbernic",  "cfw": ["muOS", "Knulli", "ROCKNIX"]},
    "Anbernic RG35XX SP":   {"device": "rg35xx-sp",   "manufacturer": "Anbernic",  "cfw": ["muOS", "Knulli", "ROCKNIX"]},
    "Anbernic RG34XX":      {"device": "rg34xx-h",    "manufacturer": "Anbernic",  "cfw": ["muOS", "Knulli", "ROCKNIX"]},
    "Anbernic RG28XX":      {"device": "rg28xx",      "manufacturer": "Anbernic",  "cfw": ["muOS", "Knulli", "ROCKNIX"]},
    "Anbernic RG351P/M":    {"device": "rg351p",      "manufacturer": "Anbernic",  "cfw": ["ArkOS (Wummle)", "AmberELEC", "ROCKNIX"]},
    "Anbernic RG351V":      {"device": "rg351v",      "manufacturer": "Anbernic",  "cfw": ["ArkOS", "AmberELEC", "ROCKNIX"]},

    # Powkiddy
    "Powkiddy RGB10":         {"device": "rgb10",        "manufacturer": "Powkiddy",  "cfw": ["ArkOS", "ROCKNIX"]},
    "Powkiddy RGB20S":        {"device": "rgb20s",       "manufacturer": "Powkiddy",  "cfw": ["AmberELEC"]},
    "Powkiddy RGB30":         {"device": "rgb30",        "manufacturer": "Powkiddy",  "cfw": ["ArkOS", "ROCKNIX"]},
    "Powkiddy RK2023":        {"device": "rk2023",       "manufacturer": "Powkiddy",  "cfw": ["ArkOS", "ROCKNIX"]},
    "Powkiddy X55":           {"device": "x55",          "manufacturer": "Powkiddy",  "cfw": ["ROCKNIX"]},
    "Powkiddy RGB10MAX3":     {"device": "rgb10max3",    "manufacturer": "Powkiddy",  "cfw": ["ROCKNIX"]},
    "Powkiddy RGB10MAX3 Pro": {"device": "rgb10max3pro", "manufacturer": "Powkiddy",  "cfw": ["ROCKNIX"]},

    # Hardkernel
    "Hardkernel ODROID GO Advance": {"device": "oga", "manufacturer": "Hardkernel",  "cfw": ["ArkOS", "AmberELEC", "EmuELEC", "ROCKNIX"]},
    "Hardkernel ODROID GO Super":   {"device": "ogs", "manufacturer": "Hardkernel",  "cfw": ["ArkOS", "AmberELEC", "EmuELEC", "ROCKNIX"]},
    "Hardkernel ODROID GO Ultra":   {"device": "ogu", "manufacturer": "Hardkernel",  "cfw": ["ArkOS", "AmberELEC", "EmuELEC", "ROCKNIX"]},

    # Gameforce
    "Gameforce Ace": {"device": "ace", "manufacturer": "Gameforce", "cfw": ["ROCKNIX"]},
    "Gameforce Chi": {"device": "chi", "manufacturer": "Gameforce", "cfw": ["ArkOS", "EmuELEC"]},

    # TrimUI
    "TrimUI Smart Pro": {"device": "trimui-smart-pro", "manufacturer": "TrimUI", "cfw": ["TrimUI", "KNULLI"]},
    "TrimUI Brick":     {"device": "trimui-brick",     "manufacturer": "TrimUI", "cfw": ["TrimUI", "KNULLI"]},

    # Retroid Pocket
    "Retroid Pocket 5":    {"device": "rp5",    "manufacturer": "Retroid Pocket", "cfw": ["ROCKNIX", "Batocera"]},
    "Retroid Pocket Mini": {"device": "rpmini", "manufacturer": "Retroid Pocket", "cfw": ["ROCKNIX", "Batocera"]},

    # ZPG GKD
    "GKD Bubble": {"device": "gkd-bubble", "manufacturer": "Game Kiddy", "cfw": ["EMUELEC"]},

    # Valve
    "SteamDeck":  {"device": "steamdeck", "manufacturer": "Valve", "cfw": ["RetroDECK", "Batocera"]},

    # Generic
    "XU10 Retro Handheld": {"device": "xu10", "manufacturer": "MagicX", "cfw": ["ArkOS", "AmberELEC", "ROCKNIX"]},
    "R33S Retro Handheld": {"device": "r33s", "manufacturer": "Game Console", "cfw": ["ArkOS", "AmberELEC", "ROCKNIX"]},
    "R35S Retro Handheld": {"device": "r35s", "manufacturer": "Game Console", "cfw": ["ArkOS", "AmberELEC", "ROCKNIX"]},
    "R36S Retro Handheld": {"device": "r36s", "manufacturer": "Game Console", "cfw": ["ArkOS", "AmberELEC", "ROCKNIX"]},
    }


HW_INFO = {
    # Anbernic Devices
    "rg552":   {"resolution": (1920, 1152), "analogsticks": 2, "cpu": "rk3399", "capabilities": ["power"], "ram": 4096},
    "rg503":   {"resolution": ( 960,  544), "analogsticks": 2, "cpu": "rk3566", "capabilities": ["power"], "ram": 1024},
    "rg351mp": {"resolution": ( 640,  480), "analogsticks": 2, "cpu": "rk3326", "capabilities": [], "ram": 1024},
    "rg351p":  {"resolution": ( 480,  320), "analogsticks": 2, "cpu": "rk3326", "capabilities": [], "ram": 1024},
    "rg353v":  {"resolution": ( 640,  480), "analogsticks": 2, "cpu": "rk3566", "capabilities": ["power"], "ram": 2048},
    "rg353p":  {"resolution": ( 640,  480), "analogsticks": 2, "cpu": "rk3566", "capabilities": ["power"], "ram": 2048},
    "rg353m":  {"resolution": ( 640,  480), "analogsticks": 2, "cpu": "rk3566", "capabilities": ["power"], "ram": 2048},
    "rg351v":  {"resolution": ( 640,  480), "analogsticks": 1, "cpu": "rk3326", "capabilities": [], "ram": 1024},
    "rg353vs": {"resolution": ( 640,  480), "analogsticks": 2, "cpu": "rk3566", "capabilities": ["power"], "ram": 1024},
    "rg353ps": {"resolution": ( 640,  480), "analogsticks": 2, "cpu": "rk3566", "capabilities": ["power"], "ram": 1024},

    # Anbernic RG35XX
    "rg40xx-h":    {"resolution": (640, 480), "analogsticks": 2, "cpu": "h700", "capabilities": ["power"], "ram": 1024},
    "rg40xx-v":    {"resolution": (640, 480), "analogsticks": 1, "cpu": "h700", "capabilities": ["power"], "ram": 1024},
    "rg35xx-h":    {"resolution": (640, 480), "analogsticks": 2, "cpu": "h700", "capabilities": ["power"], "ram": 1024},
    "rg35xx-plus": {"resolution": (640, 480), "analogsticks": 0, "cpu": "h700", "capabilities": ["power"], "ram": 1024},
    "rg35xx-sp":   {"resolution": (640, 480), "analogsticks": 0, "cpu": "h700", "capabilities": ["power"], "ram": 1024},
    "rg34xx-h":    {"resolution": (720, 480), "analogsticks": 0, "cpu": "h700", "capabilities": ["power"], "ram": 1024},
    "rg28xx":      {"resolution": (640, 480), "analogsticks": 0, "cpu": "h700", "capabilities": ["power"], "ram": 1024},
    "rg35xx":      {"resolution": (640, 480), "analogsticks": 0, "cpu": "h700", "capabilities": [], "ram": 256},

    # Hardkernel Devices
    "oga": {"resolution": (480, 320), "analogsticks": 1, "cpu": "rk3326", "capabilities": [], "ram": 1024},
    "ogs": {"resolution": (854, 480), "analogsticks": 2, "cpu": "rk3326", "capabilities": [], "ram": 1024},
    "ogu": {"resolution": (854, 480), "analogsticks": 2, "cpu": "s922x",  "capabilities": ["power"], "ram": 2048},

    # Powkiddy
    "x55":          {"resolution": (1280, 720), "analogsticks": 2, "cpu": "rk3566", "capabilities": ["power"], "ram": 2048},
    "rgb10max3pro": {"resolution": ( 854, 480), "analogsticks": 2, "cpu": "s922x",  "capabilities": ["power"], "ram": 2048},
    "rgb10max3":    {"resolution": (1280, 720), "analogsticks": 2, "cpu": "rk3566", "capabilities": ["power"], "ram": 1024},
    "rgb10max2":    {"resolution": ( 854, 480), "analogsticks": 2, "cpu": "rk3326", "capabilities": [], "ram": 1024},
    "rgb10max":     {"resolution": ( 854, 480), "analogsticks": 2, "cpu": "rk3326", "capabilities": [], "ram": 1024},
    "rgb10s":       {"resolution": ( 480, 320), "analogsticks": 1, "cpu": "rk3326", "capabilities": [], "ram": 1024},
    "rgb20s":       {"resolution": ( 640, 480), "analogsticks": 2, "cpu": "rk3326", "capabilities": [], "ram": 1024},
    "rgb30":        {"resolution": ( 720, 720), "analogsticks": 2, "cpu": "rk3566", "capabilities": ["power"], "ram": 1024},
    "rk2023":       {"resolution": ( 640, 480), "analogsticks": 2, "cpu": "rk3566", "capabilities": ["power"], "ram": 1024},
    "rk2020":       {"resolution": ( 480, 320), "analogsticks": 1, "cpu": "rk3326", "capabilities": [], "ram": 1024},

    # Miyoo
    "miyoo-flip":   {"resolution": ( 640,  480), "analogsticks": 2, "cpu": "rk3566", "capabilities": ["power"], "ram": 1024},

    # Gameforce Chi / Ace
    "chi":       {"resolution": ( 640,  480), "analogsticks": 2, "cpu": "rk3326", "capabilities": [], "ram": 1024},
    "ace":       {"resolution": (1920, 1080), "analogsticks": 2, "cpu": "rk3588", "capabilities": ["power", "ultra"], "ram": 8192},

    # Retroid Pocket
    "rpmini":    {"resolution": (1280,  960), "analogsticks": 2, "cpu": "sd865", "capabilities": ["power", "ultra"], "ram": 6144},
    "rp5":       {"resolution": (1920, 1080), "analogsticks": 2, "cpu": "sd865", "capabilities": ["power", "ultra"], "ram": 8192},

    # Generic
    "xu10":      {"resolution": ( 640,  480), "analogsticks": 2, "cpu": "rk3326", "capabilities": [], "ram": 1024},
    "r33s":      {"resolution": ( 640,  480), "analogsticks": 0, "cpu": "rk3326", "capabilities": [], "ram": 1024},
    "r35s":      {"resolution": ( 640,  480), "analogsticks": 2, "cpu": "rk3326", "capabilities": [], "ram": 1024},
    "r36s":      {"resolution": ( 640,  480), "analogsticks": 2, "cpu": "rk3326", "capabilities": [], "ram": 1024},

    # TrimUI
    "trimui-smart-pro": {"resolution": (1280, 720), "analogsticks": 2, "cpu": "a133plus", "capabilities": ["power"], "ram": 1024},
    "trimui-brick":     {"resolution": (1024, 768), "analogsticks": 0, "cpu": "a133plus", "capabilities": ["power"], "ram": 1024},

    # ZPG GKD
    "gkd-bubble": {"resolution": (640, 480), "analogsticks": 2, "cpu": "rk3566",  "capabilities": ["power"], "ram": 1024},

    # Computer/Testing
    "pc":        {"resolution": (640, 480), "analogsticks": 2, "cpu": "unknown", "capabilities": ["opengl", "power"]},

    # TODO: fix this.
    "retrodeck": {"resolution": (1280, 800), "analogsticks": 2, "cpu": "x86_64", "capabilities": ["opengl", "power", "ultra"], "ram": 16384},
    "steamdeck": {"resolution": (1280, 800), "analogsticks": 2, "cpu": "x86_64", "capabilities": ["opengl", "power", "ultra"], "ram": 16384},

    # Default
    "default":   {"resolution": (640, 480), "analogsticks": 2, "cpu": "unknown", "capabilities": ["opengl", "power"]},
    }


CFW_INFO = {
    ## From PortMaster.sh from JELOS, all devices except x55 and rg10max3 have opengl
    "jelos-x55":       {"capabilities": []},
    "jelos-rgb10max3": {"capabilities": []},
    "jelos-rgb30":     {"capabilities": []},
    "jelos":           {"capabilities": ["opengl"]},

    ## For ROCKNIX, should match JELOS for now. :)
    "rocknix-x55":       {"capabilities": []},
    "rocknix-rgb10max3": {"capabilities": []},
    "rocknix-rgb30":     {"capabilities": []},
    "rocknix":           {"capabilities": ["opengl"]},
    }


## OBSOLETE
CPU_INFO = {
    "rk3326":        {"capabilities": ["armhf", "aarch64"], "primary_arch": "aarch64"},
    "rk3399":        {"capabilities": ["armhf", "aarch64"], "primary_arch": "aarch64"},
    "rk3566-miyoo":  {"capabilities": ["aarch64"],          "primary_arch": "aarch64"},
    "rk3566":        {"capabilities": ["armhf", "aarch64"], "primary_arch": "aarch64"},
    "rk3588":        {"capabilities": ["armhf", "aarch64"], "primary_arch": "aarch64"},
    "h700-knulli":   {"capabilities": ["aarch64"],          "primary_arch": "aarch64"},
    "h700-batocera": {"capabilities": ["aarch64"],          "primary_arch": "aarch64"},
    "h700-muos":     {"capabilities": ["armhf", "aarch64"], "primary_arch": "aarch64"},
    "h700":          {"capabilities": ["armhf", "aarch64"], "primary_arch": "aarch64"},
    "a133plus":      {"capabilities": ["aarch64"],          "primary_arch": "aarch64"},
    "x86_64":        {"capabilities": ["x86_64"],           "primary_arch": "x86_64"},
    "s922x":         {"capabilities": ["aarch64"],          "primary_arch": "aarch64"},
    "sd865":         {"capabilities": ["armhf", "aarch64"], "primary_arch": "aarch64"},
    "unknown":       {"capabilities": ["armhf", "aarch64"], "primary_arch": "aarch64"},
    }


GLIBC_INFO = {
    "arkos-*":     "2.30",
    "trimui-*":    "2.33",
    "knulli-*":    "2.38",
    "muos-*":      "2.38",
    "amberelec-*": "2.38",
    "rocknix-*":   "2.40",
    "miyoo-*":     "2.36",

    "default":     "2.30",
    }


def cpu_info_v2(info):
    if Path('/lib/ld-linux-armhf.so.3').exists():
        info["capabilities"].append("armhf")
        info['primary_arch'] = "armhf"

    if Path('/lib/ld-linux-aarch64.so.1').exists():
        info["capabilities"].append("aarch64")
        info['primary_arch'] = "aarch64"

    if Path('/lib/ld-linux.so.2').exists():
        info["capabilities"].append("x86")
        info['primary_arch'] = "x86"

    if (
            Path('/lib/ld-linux-x86-64.so.2').exists() or
            Path('/lib64/ld-linux-x86-64.so.2').exists() or
            Path('/usr/lib/x86_64-linux-gnu/ld-linux-x86-64.so.2').exists()):
        info["capabilities"].append("x86_64")
        info['primary_arch'] = "x86_64"

    if HM_TESTING or 'primary_arch' not in info:
        info["capabilities"].append("armhf")
        info["capabilities"].append("aarch64")
        info['primary_arch'] = "aarch64"


_GLIBC_VER=None
def get_glibc_version():
    global _GLIBC_VER

    lib_paths = [
        # Most likely
        '/lib/',
        '/lib64/',
        '/lib/aarch64-linux-gnu/',
        '/lib32/',
        '/lib/arm-linux-gnueabihf/',
        # Least likely
        '/usr/lib/',
        '/usr/lib64/',
        '/usr/lib32/',
        ]

    if _GLIBC_VER is None:
        for lib_path in lib_paths:
            libc_path = Path(lib_path) / 'libc.so.6'

            if not libc_path.is_file():
                continue
    
            try:
                result = subprocess.run(
                    [str(libc_path), "--version"],
                    capture_output=True, text=True, check=True)

                # The first line contains the glibc version
                _GLIBC_VER = result.stdout.splitlines()[0].strip().split(' ')[-1].rstrip('.')

            except Exception as e:
                logger.error(f"Error retrieving glibc version: {e}")
                # Failsafe
                _GLIBC_VER = GLIBC_INFO['default']

            break

        else:
            _GLIBC_VER = GLIBC_INFO['default']

    return _GLIBC_VER


def safe_cat(file_name):
    if isinstance(file_name, str):
        file_name = pathlib.Path(file_name)

    elif not isinstance(file_name, pathlib.PurePath):
        raise ValueError(file_name)

    if str(file_name).startswith('~/'):
        file_name = file_name.expanduser()

    if not file_name.is_file():
        return ''

    return file_name.read_text()


def file_exists(file_name):
    return Path(file_name).exists()


def nice_device_to_device(raw_device):
    raw_device = raw_device.split('\0', 1)[0].lower()

    pattern_to_device = (
        ('sun50iw9',  'rg35xx-h'),
        ('sun50iw10', 'trimui-smart-pro'),

        ('hardkernel odroid-go-ultra',  'ogu'),
        ('odroid-go advance*',          'oga'),
        ('odroid-go super*',            'ogs'),

        ('powkiddy rgb10 max 3 pro', 'rgb10max3pro'),
        ('powkiddy rgb10 max 3',     'rgb10max3'),
        ('powkiddy rgb30',           'rgb30'),
        ('powkiddy rk2023',          'rk2023'),
        ('powkiddy x55',             'x55'),

        ('anbernic rg28xx*',      'rg28xx'),
        ('anbernic rg34xx*',      'rg34xx-h'),
        ('anbernic rg35xx h*',    'rg35xx-h'),
        ('anbernic rg35xx sp*',   'rg35xx-sp'),
        ('anbernic rg35xx plus*', 'rg35xx-plus'),
        ('anbernic rg40xx h*',    'rg40xx-h'),
        ('anbernic rg40xx v*',    'rg40xx-v'),

        ('anbernic rg40xx*',      'rg40xx-h'),
        ('anbernic rg35xx*',      'rg35xx-h'),

        ('miyoo rk3566 355 v10*', 'miyoo-flip'),

        ('anbernic rg351mp*', 'rg351mp'),
        ('anbernic rg351v*',  'rg351v'),
        ('anbernic rg351*',   'rg351p'),
        ('anbernic rg353m*',  'rg353m'),
        ('anbernic rg353v*',  'rg353v'),
        ('anbernic rg353p*',  'rg353p'),
        ('anbernic rg552',    'rg552'),

        ('gameforce ace',     'ace'),

        ('magicx xu10',       'xu10'),

        ('retroid pocket 5',    'rp5'),
        ('retroid pocket mini', 'rpmini'),
        )

    for pattern, device in pattern_to_device:
        # logger.debug(f'{raw_device} -> {pattern}')
        if fnmatch.fnmatch(raw_device, pattern):
            raw_device = device
            break
    else:
        raw_device = raw_device.lower()

    if raw_device not in HW_INFO:
        logger.debug(f"nice_device_to_device -->> {raw_device!r} <<--")
        raw_device = 'default'

    return raw_device.lower()


def new_device_info():
    if HM_TESTING:
        return {
            'name': platform.system(),
            'version': platform.release(),
            'device': 'default',
            }

    info = {}

   # Works on RetroDECK if flatplack deployed to $HOME folder.
    retrodeck_version = safe_cat('/var/config/retrodeck/retrodeck.cfg')
    if retrodeck_version == '':
        retrodeck_version = safe_cat('~/.var/app/net.retrodeck.retrodeck/config/retrodeck/retrodeck.cfg')

    if retrodeck_version != '':
        info['name'] = 'RetroDECK'
        info['version'] = ' '.join(re.findall(r'version=(.*)', retrodeck_version))
        info['device'] = 'retrodeck'

    ## Works on muOS (obviously)
    muos_version = safe_cat('/opt/muos/config/version.txt')
    if muos_version != '':
        info['name'] = 'muOS'
        info['version'] = muos_version.strip().split('\n')[0]

    muos_device = safe_cat('/opt/muos/config/device.txt')
    if muos_device != '':
        info['device'] = muos_device.lower().replace(' ', '-').split('\n')[0]

    # Works on TrimUI Smart Pro
    if Path('/usr/trimui').is_dir():
        info['name'] = 'TrimUI'
        info['version'] = safe_cat("/etc/version")

    # Works on ArkOS
    config_device = safe_cat('~/.config/.DEVICE')
    if config_device != '':
        info['device'] = config_device.strip().lower()

    # Works on ArkOS
    plymouth = safe_cat('/usr/share/plymouth/themes/text.plymouth')
    if plymouth != '':
        for result in re.findall(r'^title=(.*?) \(([^\)]+)\)', plymouth, re.I | re.M):
            info['name'] = result[0].split(' ', 1)[0]
            info['version'] = result[1]

    # Miyoo!
    miyoo_version = safe_cat('/usr/miyoo/version')
    if miyoo_version != '':
        info['name'] = 'Miyoo'
        info['version'] = miyoo_version.strip()

    # Works on uOS / JELOS / AmberELEC / muOS / ROCKNIX
    sfdbm = safe_cat('/sys/firmware/devicetree/base/model')
    if sfdbm != '':
        device = nice_device_to_device(sfdbm)
        if device != 'default':
            info.setdefault('device', device)

    # Works on AmberELEC rg351mp image.
    stcd = safe_cat('/storage/.config/device')
    if info.get('device') == 'rg351mp' and stcd != '':
        info['device'] = stcd

    # Works on AmberELEC / uOS / JELOS / ROCKNIX
    os_release = safe_cat('/etc/os-release')
    for result in re.findall(r'^([a-z0-9_]+)="([^"]+)"$', os_release, re.I | re.M):
        if result[0] in ('NAME', 'VERSION', 'OS_NAME', 'OS_VERSION', 'HW_DEVICE', 'COREELEC_DEVICE'):
            key = result[0].rsplit('_', 1)[-1].lower()
            value = result[1].strip()
            if key == 'device':
                value = nice_device_to_device(value)

            info.setdefault(key, value)

    # Works on Batocera
    batocera_version = safe_cat('/usr/share/batocera/batocera.version')
    if batocera_version != '':
        info.setdefault('name', 'Batocera')
        info['version'] = subprocess.getoutput('batocera-version').strip().split(' ', 1)[0]
        info['device'] = safe_cat('/boot/boot/batocera.board').strip()

    # REG Linux
    reglinux_version = safe_cat('/usr/share/reglinux/system.version')
    if reglinux_version != '':
        info.setdefault('name', 'REGLinux')
        info['version'] = subprocess.getoutput('system-version').strip().split(' ', 1)[0]
        info['device'] = safe_cat('/boot/boot/system.board').strip()

    if 'device' not in info:
        info['device'] = old_device_info()

    usr_trimui_res_enlang = safe_cat('/usr/trimui/res/lang/en.lang')
    if 'Dpad to Analog Key(hold)' in usr_trimui_res_enlang:
        info['device'] = 'trimui-brick'

    info['device'] = info['device'].lower().replace(' ', '-')

    info.setdefault('name', 'Unknown')
    info.setdefault('version', '0.0.0')

    logger.info(info)

    return info


def old_device_info():
    # Abandon all hope, ye who enter. 

    # From PortMaster/control.txt
    if file_exists('/dev/input/by-path/platform-ff300000.usb-usb-0:1.2:1.0-event-joystick'):
        if file_exists('/boot/rk3326-rg351v-linux.dtb') or safe_cat("/storage/.config/.OS_ARCH").strip().casefold() == "rg351v":
            # RG351V
            return "rg351v"

        # RG351P/M
        return "rg351p"

    elif file_exists('/dev/input/by-path/platform-odroidgo2-joypad-event-joystick'):
        if "190000004b4800000010000001010000" in safe_cat('/etc/emulationstation/es_input.cfg'):
            return "oga"
        else:
            return "rk2020"

        return "rgb10s"

    elif file_exists('/dev/input/by-path/platform-odroidgo3-joypad-event-joystick'):
        if ("rgb10max" in safe_cat('/etc/emulationstation/es_input.cfg').strip().casefold()):
            return "rgb10max"

        if file_exists('/opt/.retrooz/device'):
            device = safe_cat("/opt/.retrooz/device").strip().casefold()
            if "rgb10max2native" in device:
                return "rgb10max"

            if "rgb10max2top" in device:
                return "rgb10max"

        return "ogs"

    elif file_exists('/dev/input/by-path/platform-gameforce-gamepad-event-joystick'):
        return "chi"

    return 'unknown'


def _merge_info(info, new_info):
    for key, value in new_info.items():
        if key not in info:
            if isinstance(value, (list, tuple)):
                value = value[:]

            elif isinstance(value, dict):
                value = dict(value)

            info[key] = value
            continue

        if isinstance(value, list):
            info[key] = list(set(info[key]) | set(value))

        elif isinstance(value, (str, tuple, int)):
            info[key] = value

    return info


def mem_limits():
    # Lets not go crazy, who gives a fuck over 16gb
    MAX_RAM = 16

    if not hasattr(os, 'sysconf_names'):
        memory = 2

    elif 'SC_PAGE_SIZE' not in os.sysconf_names:
        memory = 2

    elif 'SC_PHYS_PAGES' not in os.sysconf_names:
        memory = 2

    else:
        memory = min(MAX_RAM, math.ceil((os.sysconf('SC_PAGE_SIZE') * os.sysconf('SC_PHYS_PAGES')) / (1024**3)))

    return memory * 1024


def find_device_by_resolution(resolution):
    for device, information in HW_INFO.items():
        if resolution == information['resolution']:
            return device

    return 'default'


def expand_info(info, override_resolution=None, override_ram=None, use_old_cpu_info=False):
    """
    This turns fetches device info and expands out the capabilities based on that device/cfw.
    """

    _merge_info(info, HW_INFO.get(info['device'], HW_INFO['default']))

    if not use_old_cpu_info:
        cpu_info_v2(info)

    else:
        if f"{info['cpu']}-{info['device']}" in CPU_INFO:
            _merge_info(info, CPU_INFO[f"{info['cpu']}-{info['device']}"])

        elif info['cpu'] in CPU_INFO:
            _merge_info(info, CPU_INFO[info['cpu']])

    if f"{info['name'].lower()}-{info['device']}" in CFW_INFO:
        _merge_info(info, CFW_INFO[f"{info['name'].lower()}-{info['device']}"])

    elif info['name'].lower() in CFW_INFO:
        _merge_info(info, CFW_INFO[info['name'].lower()])

    if override_resolution is not None:
        info['resolution'] = override_resolution

    if override_ram is not None:
        info['ram'] = override_ram

    if use_old_cpu_info:
        _name, _device = info['name'].lower(), info['device'].lower()
        if f"{_name}-{_device}" in GLIBC_INFO:
            info['glibc'] = GLIBC_INFO[f"{_name}-{_device}"]

        elif f"{_name}-*" in GLIBC_INFO:
            info['glibc'] = GLIBC_INFO[f"{_name}-*"]

        elif f"*-{_device}" in GLIBC_INFO:
            info['glibc'] = GLIBC_INFO[f"*-{_device}"]

        else:
            info['glibc'] = GLIBC_INFO['default']

    else:
        info['glibc'] = get_glibc_version()

    display_gcd = math.gcd(info['resolution'][0], info['resolution'][1])
    display_ratio = f"{info['resolution'][0] // display_gcd}:{info['resolution'][1] // display_gcd}"

    if display_ratio == "8:5":
        ## HACK
        info['capabilities'].append("16:9")
        display_ratio = "16:10"

    info['capabilities'].append('restore')

    info['capabilities'].append(display_ratio)
    info['capabilities'].append(f"{info['resolution'][0]}x{info['resolution'][1]}")

    info['capabilities'].append(info['name'])
    info['capabilities'].append(info['device'])

    for i in range(info['analogsticks']+1):
        info['capabilities'].append(f"analog_{i}")

    if info['resolution'][1] < 480:
        info['capabilities'].append("lowres")

    elif info['resolution'][1] > 480:
        info['capabilities'].append("hires")

    if info['resolution'][0] > 640:
        if "hires" not in info['capabilities']:
            info['capabilities'].append("hires")

        if info['resolution'][0] > info['resolution'][1]:
            info['capabilities'].append("wide")

    results = []
    max_memory = info.get('ram', 1024)
    memory = 1024
    while memory <= max_memory:
        info['capabilities'].append(f"{memory // 1024}gb")
        memory *= 2

    return info


__root_info = None
def device_info(override_device=None, override_resolution=None):
    global __root_info
    if override_device is None and override_resolution is None and __root_info is not None:
        return __root_info

    # Best guess at what device we are running on, and what it is capable of.
    info = new_device_info()

    if override_device is not None:
        info['device'] = override_device

    override_ram = mem_limits()

    if info['device'] in ('rg353v', 'rg353p') and override_ram == 1024:
        info['device'] += 's'

    expand_info(info, override_resolution, override_ram)

    logger.info(f"DEVICE INFO: {info}")
    __root_info = info
    return info


__all__ = (
    'device_info',
    'expand_info',
    'find_device_by_resolution',
    'HW_INFO',
    'DEVICES',
    )
