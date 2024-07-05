
# System imports
import pathlib
import platform
import os
import subprocess
import textwrap
import re

from pathlib import Path

# Included imports

from loguru import logger


################################################################################
## Override this for custom tools/ports directories

HM_TOOLS_DIR=None
HM_PORTS_DIR=None
HM_SCRIPTS_DIR=None
HM_UPDATE_FREQUENCY=(60 * 60 * 1)  # Only check automatically once per hour.

HM_TESTING=False
HM_PERFTEST=False

################################################################################
## The following code is a simplification of the PortMaster toolsloc and whichsd code.
HM_DEFAULT_PORTS_DIR = Path("/roms/ports")
HM_DEFAULT_SCRIPTS_DIR = Path("/roms/ports")
HM_DEFAULT_TOOLS_DIR = Path("/roms/ports")

if 'XDG_DATA_HOME' not in os.environ:
    os.environ['XDG_DATA_HOME'] = str(Path().home() / '.local' / 'share')

if (Path().cwd() / '..' / '.git').is_dir():
    os.chdir(Path().cwd() / '..')

if (Path().cwd() / '.git').is_dir():
    ## For testing
    HM_DEFAULT_TOOLS_DIR = Path('.').absolute()
    HM_DEFAULT_PORTS_DIR = Path('ports/').absolute()
    HM_DEFAULT_SCRIPTS_DIR = Path('ports/').absolute()
    HM_TESTING=True

elif Path("/mnt/SDCARD/Apps/PortMaster").is_dir():
    ## TrimUI Smart Pro
    HM_DEFAULT_TOOLS_DIR   = Path("/mnt/SDCARD/Apps/PortMaster")

    if Path("/mnt/SDCARD/Ports").is_dir():
        HM_DEFAULT_PORTS_DIR = Path("/mnt/SDCARD/Ports")
    else:
        HM_DEFAULT_PORTS_DIR   = Path("/mnt/SDCARD/ports")

    HM_DEFAULT_SCRIPTS_DIR = Path("/mnt/SDCARD/Roms/PORTS")

elif Path("/userdata/roms/ports").is_dir():
    ## Batocera
    HM_DEFAULT_TOOLS_DIR   = Path("/userdata/roms/ports")
    HM_DEFAULT_PORTS_DIR   = Path("/userdata/roms/ports")
    HM_DEFAULT_SCRIPTS_DIR = Path("/userdata/roms/ports")

elif Path("/opt/muos").is_dir():
    ## muOS
    HM_DEFAULT_TOOLS_DIR   = Path("/mnt/mmc/MUOS")
    HM_DEFAULT_PORTS_DIR   = Path("/mnt/mmc/ports")
    HM_DEFAULT_SCRIPTS_DIR = Path("/mnt/mmc/ROMS/Ports")

    if '/mnt/sdcard' in subprocess.getoutput(['df']):
        HM_DEFAULT_PORTS_DIR   = Path("/mnt/sdcard/ports")
        HM_DEFAULT_SCRIPTS_DIR = Path("/mnt/sdcard/ROMS/Ports")

elif Path("/opt/system/Tools").is_dir():
    if Path("/roms2/tools").is_dir():
        HM_DEFAULT_TOOLS_DIR = Path("/roms2/tools")
        HM_DEFAULT_PORTS_DIR = Path("/roms2/ports")
        HM_DEFAULT_SCRIPTS_DIR = Path("/roms2/ports")

    else:
        HM_DEFAULT_TOOLS_DIR = Path("/roms/tools")
        HM_DEFAULT_PORTS_DIR = Path("/roms/ports")
        HM_DEFAULT_SCRIPTS_DIR = Path("/roms/ports")

elif Path("/opt/tools/PortMaster").is_dir():
    HM_DEFAULT_TOOLS_DIR = Path("/opt/tools")
    HM_DEFAULT_PORTS_DIR = Path("/roms/ports")
    HM_DEFAULT_SCRIPTS_DIR = Path("/roms/ports")

elif Path("/storage/roms/ports_scripts").is_dir():
    HM_DEFAULT_TOOLS_DIR = Path("/storage/roms/ports")
    HM_DEFAULT_PORTS_DIR = Path("/storage/roms/ports")
    HM_DEFAULT_SCRIPTS_DIR = Path("/storage/roms/ports_scripts")

elif Path("/storage/roms/ports").is_dir():
    HM_DEFAULT_TOOLS_DIR = Path("/storage/roms/ports")
    HM_DEFAULT_PORTS_DIR = Path("/storage/roms/ports")
    HM_DEFAULT_SCRIPTS_DIR = Path("/storage/roms/ports")

## Check if retrodeck.cfg exists. Chose this file/location as platform independent from were retrodeck is installed.
elif (Path.home() / ".var/app/net.retrodeck.retrodeck/config/retrodeck/retrodeck.cfg").is_file():
    retrodeck_roms_path = retrodeck_roms_path = (Path.home() / ".var/app/net.retrodeck.retrodeck/config/retrodeck/retrodeck.cfg").read_text()
    if retrodeck_roms_path != '':
        retrodeck_roms_path = retrodeck_roms_path.join(re.findall(r'roms_folder=(.*)', retrodeck_roms_path)) + "/ports"
        HM_DEFAULT_TOOLS_DIR   = Path(retrodeck_roms_path)
        HM_DEFAULT_PORTS_DIR   = Path(retrodeck_roms_path)
        HM_DEFAULT_SCRIPTS_DIR = Path(retrodeck_roms_path)

else:
    HM_DEFAULT_TOOLS_DIR = Path("/roms/ports")

logger.debug(f"HM_DEFAULT_TOOLS_DIR:   {HM_DEFAULT_TOOLS_DIR}")
logger.debug(f"HM_DEFAULT_PORTS_DIR:   {HM_DEFAULT_PORTS_DIR}")
logger.debug(f"HM_DEFAULT_SCRIPTS_DIR: {HM_DEFAULT_SCRIPTS_DIR}")

## Default TOOLS_DIR
if HM_TOOLS_DIR is None:
    if 'HM_TOOLS_DIR' in os.environ:
        HM_TOOLS_DIR = Path(os.environ['HM_TOOLS_DIR'])
    else:
        HM_TOOLS_DIR = HM_DEFAULT_TOOLS_DIR
elif isinstance(HM_TOOLS_DIR, str):
    HM_TOOLS_DIR = Path(HM_TOOLS_DIR).resolve()
elif isinstance(HM_TOOLS_DIR, pathlib.PurePath):
    # This is good.
    pass
else:
    logger.error(f"{HM_TOOLS_DIR!r} is set to something weird.")
    exit(255)


## Default PORTS_DIR
if HM_PORTS_DIR is None:
    if 'HM_PORTS_DIR' in os.environ:
        HM_PORTS_DIR = Path(os.environ['HM_PORTS_DIR']).resolve()
    else:
        HM_PORTS_DIR = HM_DEFAULT_PORTS_DIR
elif isinstance(HM_PORTS_DIR, str):
    HM_PORTS_DIR = Path(HM_PORTS_DIR).resolve()
elif isinstance(HM_PORTS_DIR, pathlib.PurePath):
    # This is good.
    pass
else:
    logger.error(f"{HM_PORTS_DIR!r} is set to something weird.")
    exit(255)

## Default TOOLS_DIR
if HM_SCRIPTS_DIR is None:
    if 'HM_SCRIPTS_DIR' in os.environ:
        HM_SCRIPTS_DIR = Path(os.environ['HM_SCRIPTS_DIR'])
    else:
        HM_SCRIPTS_DIR = HM_DEFAULT_SCRIPTS_DIR
elif isinstance(HM_SCRIPTS_DIR, str):
    HM_SCRIPTS_DIR = Path(HM_SCRIPTS_DIR).resolve()
elif isinstance(HM_SCRIPTS_DIR, pathlib.PurePath):
    # This is good.
    pass
else:
    logger.error(f"{HM_SCRIPTS_DIR!r} is set to something weird.")
    exit(255)


if 'HM_PERFTEST' in os.environ:
    HM_PERFTEST=True


HM_SOURCE_DEFAULTS = {
    "020_portmaster.source.json": textwrap.dedent("""
    {
        "prefix": "pm",
        "api": "PortMasterV3",
        "name": "PortMaster",
        "url": "https://github.com/PortsMaster/PortMaster-New/releases/latest/download/ports.json",
        "last_checked": null,
        "version": 1,
        "data": {}
    }
    """),
    "021_portmaster.multiverse.source.json": textwrap.dedent("""
    {
        "prefix": "pmmv",
        "api": "PortMasterV3",
        "name": "PortMaster Multiverse",
        "url": "https://github.com/PortsMaster-MV/PortMaster-MV-New/releases/latest/download/ports.json",
        "last_checked": null,
        "version": 4,
        "data": {}
    }
    """),
    }


HM_GENRES = [
    "action",
    "adventure",
    "arcade",
    "casino/card",
    "fps",
    "platformer",
    "puzzle",
    "racing",
    "rhythm",
    "rpg",
    "simulation",
    "sports",
    "strategy",
    "visual novel",
    "other",
    ]


HM_SORT_ORDER = [
    "alphabetical",
    "recently_added",
    "recently_updated",
    ]


__all__ = (
    'HM_DEFAULT_PORTS_DIR',
    'HM_DEFAULT_TOOLS_DIR',
    'HM_DEFAULT_SCRIPTS_DIR',
    'HM_GENRES',
    'HM_PERFTEST',
    'HM_PORTS_DIR',
    'HM_SCRIPTS_DIR',
    'HM_SORT_ORDER',
    'HM_SOURCE_DEFAULTS',
    'HM_TESTING',
    'HM_TOOLS_DIR',
    'HM_UPDATE_FREQUENCY',
    )
