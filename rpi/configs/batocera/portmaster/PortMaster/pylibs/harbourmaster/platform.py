
# SPDX-License-Identifier: MIT

# System imports
import contextlib
import datetime
import json
import os
import re
import shutil
import subprocess
import xml.etree.ElementTree as ET
import zipfile

from gettext import gettext as _
from pathlib import Path

# Included imports

from loguru import logger
from utility import cprint, cstrip

# Module imports
from .config import *
from .hardware import *
from .util import *

SPECIAL_GAMELIST_CODE = object()

class PlatformBase():
    WANT_XBOX_FIX = False
    WANT_SWAP_BUTTONS = False

    MOVE_PM_BASH = False
    MOVE_PM_BASH_DIR = None
    ES_NAME = None
    ROMS_REFRESH_TEXT = ""

    XML_ELEMENT_MAP = {
        'path': 'path',
        'name': 'name',
        'image': 'image',
        'desc': 'desc',
        'releasedate': 'releasedate',
        'developer': 'developer',
        'publisher': 'publisher',
        'players': 'players',
        'genre': 'genre',
        }

    XML_ELEMENT_CALLBACK = {
        }

    XML_PATH_FIX = [
        'image',
        ]

    BLANK_GAMELIST_XML = """<?xml version='1.0' encoding='utf-8'?>\n<gameList />\n"""

    def __init__(self, hm):
        self.hm = hm
        self.added_ports = set()
        self.removed_ports = set()

    def loaded(self):
        ...

    def do_move_ports(self):
        ...

    def gamelist_file(self):
        return None

    @contextlib.contextmanager
    def gamelist_backup(self):
        if not hasattr(self, '_GAMELIST_BACKUP'):
            self._GAMELIST_BACKUP = 0

        gamelist_xml = self.gamelist_file()

        if gamelist_xml in (None, SPECIAL_GAMELIST_CODE):
            try:
                yield gamelist_xml

            finally:
                return

        gamelist_xml = self.gamelist_file()
        gamelist_bak = gamelist_xml.with_name(gamelist_xml.name + '.bak')

        broken = False
        if not gamelist_xml.is_file():
            if gamelist_bak.is_file():
                logger.debug(f"Restore {gamelist_bak} to {gamelist_xml}")
                shutil.copy(gamelist_bak, gamelist_xml)

            else:
                broken = True

        elif gamelist_xml.is_file() and gamelist_xml.stat().st_size == 0:
            if gamelist_bak.is_file():
                logger.debug(f"Restore {gamelist_bak} to {gamelist_xml}")
                shutil.copy(gamelist_bak, gamelist_xml)

            else:
                broken = True

        if broken:
            logger.debug(f"Creating empty {gamelist_xml}")
            with open(gamelist_xml, 'w') as fh:
                print(self.BLANK_GAMELIST_XML, file=fh)

        try:
            if self._GAMELIST_BACKUP == 0:
                logger.debug(f"Backing up {gamelist_xml} to {gamelist_bak}")
                shutil.copy(gamelist_xml, gamelist_bak)

            self._GAMELIST_BACKUP += 1

            yield gamelist_xml

        except:
            if self._GAMELIST_BACKUP == 1:
                logger.debug(f"Restoring {gamelist_bak} to {gamelist_xml}")
                shutil.copy(gamelist_bak, gamelist_xml)

            raise

        finally:
            self._GAMELIST_BACKUP -= 1
            return

    def gamelist_add(self, gameinfo_file):
        if not gameinfo_file.is_file():
            return

        FIX_PATH = self.hm.ports_dir != self.hm.scripts_dir

        with self.gamelist_backup() as gamelist_xml:
            if gamelist_xml is None:
                return

            gamelist_tree = ET.parse(gamelist_xml)
            gamelist_root = gamelist_tree.getroot()

            gameinfo_tree = ET.parse(gameinfo_file)
            gameinfo_root = gameinfo_tree.getroot()

            for gameinfo_element in gameinfo_tree.findall('game'):
                path_merge = gameinfo_element.find('path').text

                gamelist_update = gamelist_root.find(f'.//game[path="{path_merge}"]')
                if gamelist_update is None:
                    # Create a new game element
                    gamelist_update = ET.SubElement(gamelist_root, 'game')

                logger.info(f'{path_merge}: ')

                for child in gameinfo_element:
                    # Check if the child element is in the predefined list
                    if child.tag in self.XML_ELEMENT_MAP:
                        gamelist_element = gamelist_update.find(self.XML_ELEMENT_MAP[child.tag])

                        if gamelist_element is None:
                            gamelist_element = ET.SubElement(gamelist_update, self.XML_ELEMENT_MAP[child.tag])

                        if FIX_PATH and child.tag in self.XML_PATH_FIX:
                            new_path = child.text.strip()
                            if new_path.startswith('./'):
                                new_path = new_path[2:]

                            gamelist_element.text = str(self.hm.ports_dir / new_path)

                        else:
                            gamelist_element.text = child.text

                for child in gameinfo_element:
                    if child.tag in self.XML_ELEMENT_CALLBACK:
                        if FIX_PATH and child.tag in self.XML_PATH_FIX:
                            new_path = child.text.strip()
                            if new_path.startswith('./'):
                                new_path = new_path[2:]

                            child.text = str(self.hm.ports_dir / new_path)

                        self.XML_ELEMENT_CALLBACK[child.tag](path_merge, gamelist_update, child)

            if hasattr(ET, 'indent'):
                ET.indent(gamelist_root, space="  ", level=0)

            with open(gamelist_xml, 'w') as fh:
                print("<?xml version='1.0' encoding='utf-8'?>", file=fh)
                print("", file=fh)
                print(ET.tostring(gamelist_root, encoding='unicode'), file=fh)

            self.added_ports.add('GAMELIST UPDATER')

    def ports_changed(self):
        return (len(self.added_ports) > 0 or len(self.removed_ports) > 0)

    def first_run(self):
        """
        Called on first run, this can be used to add custom sources for your platform.
        """
        logger.debug(f"{self.__class__.__name__}: First Run")

    def port_install(self, port_name, port_info, port_files):
        """
        Called on after a port is installed, this can be used to check permissions, possibly augment the bash scripts.
        """
        logger.debug(f"{self.__class__.__name__}: Port Install {port_name}")

        if port_name in self.removed_ports:
            self.removed_ports.remove(port_name)
        else:
            self.added_ports.add(port_name)

    def runtime_install(self, runtime_name, runtime_files):
        """
        Called on after a port is installed, this can be used to check permissions, possibly augment the bash scripts.
        """
        logger.debug(f"{self.__class__.__name__}: Runtime Install {runtime_name}")

    def port_uninstall(self, port_name, port_info, port_files):
        """
        Called on after a port is uninstalled, this can be used clean up special files.
        """
        logger.debug(f"{self.__class__.__name__}: Port Uninstall {port_name}")

        if port_name in self.added_ports:
            self.added_ports.remove(port_name)
        else:
            self.removed_ports.add(port_name)

    def portmaster_install(self):
        """
        Called on after portmaster is updated, this can be used clean up special files.
        """
        logger.debug(f"{self.__class__.__name__}: PortMaster Install")

    def set_gcd_mode(self, mode=None):
        logger.info(f"{self.__class__.__name__}: Set GCD Mode {mode}")

    def get_gcd_modes(self):
        return tuple()

    def get_gcd_mode(self):
        logger.debug(f"{self.__class__.__name__}: Get GCD Mode")
        return None


class PlatformGCD_PortMaster:
    """
    gamecontrollerdb standard / xbox mode
    """

    def loaded(self):
        if self.get_gcd_mode() == 'xbox':
            self.WANT_XBOX_FIX = True

    def set_gcd_mode(self, gcd_mode=None):
        gamecontroller_file = self.hm.tools_dir / "PortMaster" / "gamecontrollerdb.txt"
        mode_files = {
            'standard': self.hm.tools_dir / "PortMaster" / ".Backup" / "donottouch.txt",
            'xbox': self.hm.tools_dir / "PortMaster" / ".Backup" / "donottouch_x.txt",
            }

        logger.info(f"{self.__class__.__name__}: Set GCD Mode: {gcd_mode}")

        if gcd_mode:
            if gcd_mode not in mode_files:
                logger.debug(f"Unknown gcd_mode {gcd_mode}")
                return

            if not mode_files[gcd_mode].is_file():
                logger.debug(f"Unknown gcd_mode {gcd_mode} file.")
                return

            shutil.copy(mode_files[gcd_mode], gamecontroller_file)

            self.hm.cfg_data['gcd-mode'] = gcd_mode
            self.hm.save_config()

        else:
            logger.debug(f"Weird {gcd_mode}")

    def get_gcd_modes(self):
        return ('standard', 'xbox')

    def get_gcd_mode(self):
        gamecontroller_file = self.hm.tools_dir / "PortMaster" / "gamecontrollerdb.txt"

        gcd_mode = self.hm.cfg_data.get('gcd-mode', None)

        if gcd_mode not in self.get_gcd_modes():
            gcd_mode = None

        if gcd_mode is None:
            if gamecontroller_file.is_file():
                if "# Xbox 360 Layout" in gamecontroller_file.read_text():
                    gcd_mode = 'xbox'

            if gcd_mode is None:
                gcd_mode = 'standard'

            self.hm.cfg_data['gcd-mode'] = gcd_mode
            self.hm.save_config()

        logger.debug(f"{self.__class__.__name__}: Get GCD Mode: {gcd_mode}")
        return gcd_mode


class PlatformUOS(PlatformGCD_PortMaster, PlatformBase):
    ES_NAME = 'emustation'

    def gamelist_file(self):
        return self.hm.ports_dir / 'gamelist.xml'


class PlatformJELOS(PlatformBase):
    ES_NAME = 'emustation'

    def gamelist_file(self):
        return self.hm.ports_dir / 'gamelist.xml'

    def first_run(self):
        self.portmaster_install()

    def portmaster_install(self):
        """
        Copy JELOS PortMaster files here.
        """

        ## Copy the JELOS portmaster stuff into the right place.
        JELOS_PM_DIR = Path("/storage/.config/PortMaster")
        PM_DIR = self.hm.tools_dir / "PortMaster"

        if not JELOS_PM_DIR.is_dir():
            shutil.copytree("/usr/config/PortMaster", JELOS_PM_DIR)

        ## Copy the files as per usual.
        shutil.copy(JELOS_PM_DIR / "control.txt", PM_DIR / "control.txt")
        # shutil.copy(JELOS_PM_DIR / "gptokeyb", PM_DIR / "gptokeyb")
        shutil.copy(JELOS_PM_DIR / "gamecontrollerdb.txt", PM_DIR / "gamecontrollerdb.txt")
        shutil.copy(JELOS_PM_DIR / "mapper.txt", PM_DIR / "mapper.txt")

        for oga_control in JELOS_PM_DIR.glob("oga_controls*"):
            shutil.copy(oga_control, PM_DIR / oga_control.name)


class PlatformROCKNIX(PlatformJELOS):
    ES_NAME = 'weston'


class PlatformBatocera(PlatformBase):
    MOVE_PM_BASH = True
    ES_NAME = "batocera-es"

    """
    Taken from Mikhailzrick's getInvertButtonsValue
    https://github.com/Mikhailzrick/batocera.linux/blob/43930d59a682953049c90833175c710f8f6fc018/package/batocera/core/batocera-configgen/configgen/configgen/generators/libretro/libretroConfig.py#L24
    """
    # Return value for es invertedbuttons
    def get_invert_buttons_value(self):  
        ES_SETTINGS = Path('/userdata/system/configs/emulationstation/es_settings.cfg')

        if not ES_SETTINGS.is_file():
            return False

        tree = ET.parse(str(ES_SETTINGS))

        root = tree.getroot()
        # Find the InvertButtons element and return value
        elem = root.find(".//bool[@name='InvertButtons']")

        if elem is not None:
            return elem.get('value') == 'true'

        return False  # Return False if not found 

    def loaded(self):
        self.WANT_SWAP_BUTTONS = not self.get_invert_buttons_value()
        # if self.WANT_SWAP_BUTTONS:
            # self.WANT_XBOX_FIX = not self.WANT_XBOX_FIX

    def gamelist_file(self):
        return self.hm.ports_dir / 'gamelist.xml'

    def first_run(self):
        self.portmaster_install()

        REBOOT_FILE = self.hm.tools_dir / ".pugwash-reboot"
        REBOOT_FILE.touch()

    def portmaster_install(self):
        """
        Move files into place.
        """
        TL_DIR = self.hm.tools_dir / "PortMaster"
        BC_DIR = TL_DIR / "batocera"

        # ACTIVATE THE CONTROL
        logger.debug(f'Copy {BC_DIR / "control.txt"} -> {TL_DIR / "control.txt"}')
        shutil.copy(BC_DIR / "control.txt", TL_DIR / "control.txt")

        TASK_SET = TL_DIR / "tasksetter"
        if TASK_SET.is_file():
            TASK_SET.unlink()

        TASK_SET.touch()


class PlatformREGLinux(PlatformBatocera):
    ...


class PlatformKnulli(PlatformBatocera):
    WANT_XBOX_FIX = True

    def portmaster_install(self):
        """
        Move files into place.
        """
        TL_DIR = self.hm.tools_dir / "PortMaster"
        BC_DIR = TL_DIR / "knulli"

        # ACTIVATE THE CONTROL
        logger.debug(f'Copy {BC_DIR / "control.txt"} -> {TL_DIR / "control.txt"}')
        shutil.copy(BC_DIR / "control.txt", TL_DIR / "control.txt")

        TASK_SET = TL_DIR / "tasksetter"
        if TASK_SET.is_file():
            TASK_SET.unlink()

        TASK_SET.touch()


class PlatformArkOS(PlatformGCD_PortMaster, PlatformBase):
    MOVE_PM_BASH = True
    ES_NAME = 'emulationstation'

    def __init__(self, hm):
        super().__init__(hm)

        # Fix a whoopsie :D
        BAD_SCRIPT  = self.hm.ports_dir / "PortMaster.sh"
        GOOD_SCRIPT = self.hm.tools_dir / "PortMaster.sh"

        if not BAD_SCRIPT.is_file():
            return

        if not GOOD_SCRIPT.is_file():
            logger.info(f"MV: {BAD_SCRIPT} -> {GOOD_SCRIPT}")
            shutil.move(BAD_SCRIPT, GOOD_SCRIPT)
            return

        if "pmsplash" not in GOOD_SCRIPT.read_text():
            logger.info(f"MV: {BAD_SCRIPT} -> {GOOD_SCRIPT}")
            shutil.move(BAD_SCRIPT, GOOD_SCRIPT)
            return

        logger.info(f"RM: {BAD_SCRIPT}")
        BAD_SCRIPT.unlink()

    def gamelist_file(self):
        return self.hm.ports_dir / 'gamelist.xml'


class PlatformAmberELEC(PlatformGCD_PortMaster, PlatformBase):
    MOVE_PM_BASH = True
    ES_NAME = 'emustation'

    def gamelist_file(self):
        return self.hm.ports_dir / 'gamelist.xml'


class PlatformEmuELEC(PlatformGCD_PortMaster, PlatformBase):
    MOVE_PM_BASH = True
    MOVE_PM_BASH_DIR = Path("/emuelec/scripts/")
    ES_NAME = 'emustation'

    def gamelist_file(self):
        return self.hm.scripts_dir / 'gamelist.xml'


class PlatformRetroDECK(PlatformBase):
    MOVE_PM_BASH = False
    ES_NAME = 'show-refresh'
    RD_CONFIG = None
    ROMS_REFRESH_TEXT = _("\n\nIn order to do so:\nMENU -> UTILITIES -> Rescan Rom Directory")

    XML_ELEMENT_MAP = {
        'path': 'path',
        'name': 'name',
        'desc': 'desc',
        'releasedate': 'releasedate',
        'developer': 'developer',
        'publisher': 'publisher',
        'players': 'players',
        'genre': 'genre',
        }

    def __init__(self, hm):
        super().__init__(hm)

        self.XML_ELEMENT_CALLBACK = {
            'image': self.esde_image_copy_majigger,
            }

    def get_rdconfig(self):
        if self.RD_CONFIG is None:
            rdconfig = {}

            rdconfig_file=Path("/var/config/retrodeck/retrodeck.cfg")
            if not rdconfig_file.is_file():
                rdconfig_file=(Path.home() / ".var/app/net.retrodeck.retrodeck/config/retrodeck/retrodeck.cfg")

            rdconfig['rdhome'] = None
            rdconfig['roms_folder'] = None
            rdconfig['ports_folder'] = None

            with open(rdconfig_file, 'r') as fh:
                for line in fh:
                    line = line.strip()

                    if line.startswith('rdhome='):
                        rdconfig['rdhome'] = Path(line.split('=', 1)[-1])

                    if '_folder=' in line:
                        folder_name, folder_value = line.split('=', 1)
                        rdconfig[folder_name] = Path(folder_value)

            if rdconfig['rdhome'] is None:
                logger.error(f"Unable to find the rdhome variable in {rdconfig_file}.")
                return None

            if rdconfig['roms_folder'] is None:
                rdconfig['roms_folder'] = rdconfig['rdhome'] / "roms"

            if rdconfig['ports_folder'] is None:
                rdconfig['ports_folder'] = rdconfig['rdhome'] / "PortMaster"

            self.RD_CONFIG = rdconfig

            logger.info(f"RD_CONFIG: {rdconfig}")

        return self.RD_CONFIG

    def esde_image_copy_majigger(self, port_script, game_element, image_element):
        rdconfig = self.get_rdconfig()
        if rdconfig is None:
            return None

        IMG_DIR = rdconfig['rdhome'] / 'ES-DE' / 'downloaded_media' / 'portmaster' / 'screenshots'
        # IMG_DIR = rdconfig['rdhome'] / 'downloaded_media' / 'portmaster' / 'miximages'

        IMG_DIR.mkdir(parents=True, exist_ok=True)

        SRC_IMAGE = Path(image_element.text)
        DST_IMAGE = IMG_DIR / (Path(port_script).stem + SRC_IMAGE.suffix)

        logger.info(f"COPY: {SRC_IMAGE} -> {DST_IMAGE}")
        shutil.copy(SRC_IMAGE, DST_IMAGE)

    def gamelist_file(self):
        rdconfig = self.get_rdconfig()
        if rdconfig is None:
            return None

        gamelists_dir = rdconfig['rdhome'] / 'ES-DE' / 'gamelists' / 'portmaster'

        gamelists_dir.mkdir(parents=True, exist_ok=True)

        return gamelists_dir / 'gamelist.xml'

    def first_run(self):
        self.portmaster_install()

    def portmaster_install(self):
        """
        Move files into place.
        """

        RD_DIR = self.hm.tools_dir / "PortMaster" / "retrodeck"
        PM_DIR = self.hm.tools_dir / "PortMaster"
        SC_DIR = self.hm.scripts_dir

        # ACTIVATE THE RetroDECK CONTROL
        logger.debug(f'Copy {RD_DIR / "control.txt"} -> {PM_DIR / "control.txt"}')
        shutil.copy(RD_DIR / "control.txt", PM_DIR / "control.txt")

        # PEBKAC RD
        logger.debug(f'Move {RD_DIR / "PortMaster.txt"} -> {PM_DIR / "PortMaster.sh"}')
        shutil.copy(RD_DIR / "PortMaster.txt", PM_DIR / "PortMaster.sh")

        logger.debug(f'Move {RD_DIR / "PortMaster.txt"} -> {SC_DIR / "PortMaster.sh"}')
        if (SC_DIR / "PortMaster.sh").is_symlink():
            # XARGONNNNNNNN
            (SC_DIR / "PortMaster.sh").unlink()

        shutil.copy(RD_DIR / "PortMaster.txt", SC_DIR / "PortMaster.sh")

        TASK_SET = Path(self.hm.tools_dir / "PortMaster" / "tasksetter")
        if TASK_SET.is_file():
            TASK_SET.unlink()

        TASK_SET.touch()


class PlatformmuOS(PlatformBase):
    MOVE_PM_BASH = False
    ES_NAME = "muos"

    XML_ELEMENT_MAP = {
        'image': 'image',
        'desc': 'desc',
        }

    def gamelist_file(self):
        return SPECIAL_GAMELIST_CODE

    def gamelist_add(self, gameinfo_file):
        # Xonglebongle: the sound of someone sneezing while trying to pronounce 'jungle' underwater.
        if not gameinfo_file.is_file():
            return

        if not any((
                Path("/opt/graphicsmagick").is_dir(),
                Path("/usr/bin/magick").is_file())):
            return

        INFO_CATALOG = Path("/run/muos/storage/info/catalogue/External - Ports")
        if not INFO_CATALOG.exists():
            INFO_CATALOG = Path("/mnt/mmc/MUOS/info/catalogue/External - Ports")

        INFO_BOX_DIR     = INFO_CATALOG / "box"
        INFO_PREVIEW_DIR = INFO_CATALOG / "preview"
        INFO_TEXT_DIR    = INFO_CATALOG / "text"

        with self.gamelist_backup() as gamelist_xml:
            if gamelist_xml is None:
                return

            gameinfo_tree = ET.parse(gameinfo_file)
            gameinfo_root = gameinfo_tree.getroot()

            for gameinfo_element in gameinfo_tree.findall('game'):
                path_merge = gameinfo_element.find('path').text

                if path_merge.startswith('./'):
                    path_merge = path_merge[2:]

                path_merge = path_merge.rsplit('.', 1)[0]

                for child in gameinfo_element:
                    # Check if the child element is in the predefined list
                    if child.tag not in self.XML_ELEMENT_MAP:
                        continue

                    # logger.warning(f"{child.tag}: {child.text}")

                    if child.tag == 'image':
                        text = child.text

                        if text.startswith('./'):
                            text = text[2:]

                        image_file = self.hm.ports_dir / text
                        if not image_file.is_file():
                            continue

                        target_file = INFO_BOX_DIR / (path_merge + '-pre' + image_file.suffix)
                        logger.debug(f"copying {str(image_file)} to {str(target_file)}")
                        shutil.copy(image_file, target_file)

                        screenshot_file = None
                        if (image_file.parent / 'screenshot.jpg').is_file():
                            screenshot_file = (image_file.parent / 'screenshot.jpg')

                        elif (image_file.parent / 'screenshot.png').is_file():
                            screenshot_file = (image_file.parent / 'screenshot.png')

                        if screenshot_file:
                            target_file = INFO_PREVIEW_DIR / (path_merge + '-pre' + image_file.suffix)
                            logger.debug(f"copying {str(screenshot_file)} to {str(target_file)}")
                            shutil.copy(screenshot_file, target_file)

                    elif child.tag == 'desc':
                        target_file = INFO_TEXT_DIR / (path_merge + '.txt')
                        text = child.text.strip().split('\n', 1)[0].strip()

                        logger.debug(f"creating {str(target_file)}")
                        with open(target_file, 'w') as fh:
                            print(text, file=fh)

            # HAHA THIS IS FUCKED
            self.added_ports.add('GAMELIST UPDATER')

    def first_run(self):
        self.portmaster_install()

    def portmaster_install(self):
        """
        Move files into place.
        """

        MU_DIR = self.hm.tools_dir / "PortMaster" / "muos"
        PM_DIR = self.hm.tools_dir / "PortMaster"

        # ACTIVATE THE CONTROL
        logger.debug(f'Copy {MU_DIR / "control.txt"} -> {PM_DIR / "control.txt"}')
        shutil.copy(MU_DIR / "control.txt", PM_DIR / "control.txt")

        CONTROL_HACK = Path("/roms/ports/PortMaster/control.txt")
        if not CONTROL_HACK.parent.is_dir():
            CONTROL_HACK.parent.mkdir(parents=True)

        logger.debug(f'Copy {MU_DIR / "control.txt"} -> {CONTROL_HACK}')
        shutil.copy(MU_DIR / "control.txt", CONTROL_HACK)

        # PEBKAC
        logger.debug(f'Move {MU_DIR / "PortMaster.txt"} -> {PM_DIR / "PortMaster.sh"}')
        shutil.copy(MU_DIR / "PortMaster.txt", PM_DIR / "PortMaster.sh")

        TASK_SET = Path(self.hm.tools_dir / "PortMaster" / "tasksetter")
        if TASK_SET.is_file():
            TASK_SET.unlink()

        TASK_SET.touch()

PORT_CONFIG_JSON = """
{
    "package":"{{PORTNAME}}",
    "label":"{{PORTTITLE}}",
    "icon":"icon.png",
    "themecolor":"61A8DD",
    "launch":"{{PORTSCRIPT}}",
    "description":"A Port"
}
"""

class PlatformTrimUI(PlatformBase):
    WANT_XBOX_FIX = True
    ES_NAME = "trimui"

    XML_ELEMENT_MAP = {
        'image': 'image',
        }

    def first_run(self):
        self.portmaster_install()

    def portmaster_install(self):
        """
        Move files into place.
        """

        TU_DIR = self.hm.tools_dir / "PortMaster" / "trimui"
        PM_DIR = self.hm.tools_dir / "PortMaster"

        # ACTIVATE THE CONTROL
        logger.debug(f'Copy {TU_DIR / "control.txt"} -> {PM_DIR / "control.txt"}')
        shutil.copy(TU_DIR / "control.txt", PM_DIR / "control.txt")

        CONTROL_HACK = Path("/roms/ports/PortMaster/control.txt")
        if not CONTROL_HACK.parent.is_dir():
            CONTROL_HACK.parent.mkdir(parents=True)

        logger.debug(f'Copy {TU_DIR / "control.txt"} -> {CONTROL_HACK}')
        shutil.copy(TU_DIR / "control.txt", CONTROL_HACK)

        # PEBKAC
        logger.debug(f'Move {TU_DIR / "PortMaster.txt"} -> {self.hm.tools_dir / "launch.sh"}')
        shutil.copy(TU_DIR / "PortMaster.txt", self.hm.tools_dir / "launch.sh")

        TASK_SET = Path(PM_DIR / "tasksetter")
        if TASK_SET.is_file():
            TASK_SET.unlink()

        TASK_SET.touch()

    def port_install(self, port_name, port_info, port_files):
        super().port_install(port_name, port_info, port_files)

        ## Gets called when a port is installed.
        # logger.debug(f"{port_name}: {port_files}")

        scripts_dir = '/'.join(self.hm.scripts_dir.parts)
        scripts_dir_parts = len(self.hm.scripts_dir.parts)

        for port_file in port_files:
            if not port_file.name.lower().endswith('.sh'):
                continue

            if len(port_file.parts) != (scripts_dir_parts+1):
                logger.debug(f"{len(port_file.parts)} != {(scripts_dir_parts+1)}")
                continue

            if scripts_dir != '/'.join(port_file.parts[:scripts_dir_parts]):
                logger.debug(f"{scripts_dir} != {str(port_file)}")
                continue

            self.add_port_script(port_file)

    def port_uninstall(self, port_name, port_info, port_files):
        super().port_uninstall(port_name, port_info, port_files)
        # logger.debug(f"{port_name}: {port_files}")

        for port_file in port_files:
            if port_file.endswith('.sh'):
                self.remove_port_script(self.hm.scripts_dir / port_file)

    def add_port_script(self, port_script):
        ROM_SCRIPT_DIR = Path("/mnt/SDCARD/Roms/PORTS")
        PORT_DIR       = Path("/mnt/SDCARD/Ports")

        port_mode = self.hm.cfg_data.get('trimui-port-mode', 'roms')

        if port_mode == 'roms':
            target_file = ROM_SCRIPT_DIR / (port_script.name)
            logger.debug(f"Copying {str(port_script)} to {str(target_file)}")
            shutil.copy(port_script, target_file)

        elif port_mode == 'ports':
            new_port_dir = PORT_DIR / f"portmaster-{name_cleaner(port_script.stem)}"

            new_port_dir.mkdir(0o755, parents=True, exist_ok=True)

            logger.debug(f"Creating {str(new_port_dir / 'config.json')}")
            with open(new_port_dir / "config.json", "w") as fh:
                fh.write(
                    PORT_CONFIG_JSON
                    .replace("{{PORTTITLE}}", port_script.stem)
                    .replace("{{PORTNAME}}", new_port_dir.name.lower())
                    ## A-PEH ESC-A-PEH
                    .replace("{{PORTSCRIPT}}", str(port_script).replace(' ', '\\\\ ')))

    def remove_port_script(self, port_script):
        ROM_SCRIPT_DIR = Path("/mnt/SDCARD/Roms/PORTS")
        PORT_DIR       = Path("/mnt/SDCARD/Ports")

        rom_script = (ROM_SCRIPT_DIR / port_script.name)
        if rom_script.is_file():
            logger.info(f"Removing: {str(rom_script)}")
            rom_script.unlink()

        port_dir = (PORT_DIR / f"portmaster-{name_cleaner(port_script.stem)}")
        if port_dir.is_dir():
            logger.info(f"Removing: {str(port_dir)}")
            shutil.rmtree(port_dir)

    def do_move_ports(self):
        port_mode = self.hm.cfg_data.get('trimui-port-mode', 'roms')

        ROM_IMAGE_DIR  = Path("/mnt/SDCARD/Imgs/PORTS")
        ROM_SCRIPT_DIR = Path("/mnt/SDCARD/Roms/PORTS")
        PORT_DIR       = Path("/mnt/SDCARD/Ports")

        if port_mode == 'roms':
            ## Delete port apps.
            for port_dir in PORT_DIR.glob('portmaster-*'):
                if not port_dir.is_dir():
                    continue

                shutil.rmtree(port_dir)

        elif port_mode == 'ports':
            ## Delete ports scripts.
            for port_file in ROM_SCRIPT_DIR.glob('*.sh'):
                if not port_file.is_file():
                    continue

                port_file.unlink()

        for port_script in self.hm.ports_dir.iterdir():
            # Do scripts
            if not port_script.is_file():
                continue

            self.add_port_script(port_script)

        for port_dir in self.hm.ports_dir.iterdir():
            # Fill it out with gameinfo if available.
            if not port_dir.is_dir():
                continue

            gameinfo_file = port_dir / 'gameinfo.xml'

            if not gameinfo_file.is_file():
                continue

            self.gamelist_add(gameinfo_file)

    def gamelist_file(self):
        return SPECIAL_GAMELIST_CODE

    def gamelist_add(self, gameinfo_file):
        if not gameinfo_file.is_file():
            return

        port_mode = self.hm.cfg_data.get('trimui-port-mode', 'roms')

        ROM_IMAGE_DIR  = Path("/mnt/SDCARD/Imgs/PORTS")
        ROM_SCRIPT_DIR = Path("/mnt/SDCARD/Roms/PORTS")
        PORT_DIR       = Path("/mnt/SDCARD/Ports")

        logger.debug(f"Processing {gameinfo_file}")

        self.added_ports.add('GAMELIST UPDATER')

        with self.gamelist_backup() as gamelist_xml:
            if gamelist_xml is None:
                return

            gameinfo_tree = ET.parse(gameinfo_file)
            gameinfo_root = gameinfo_tree.getroot()

            for gameinfo_element in gameinfo_tree.findall('game'):
                port_script = gameinfo_element.find('path').text

                port_script_file = self.hm.scripts_dir / port_script

                if not port_script_file.is_file():
                    logger.debug(f"Cant find {port_script}")
                    continue

                if port_script.startswith('./'):
                    port_script = port_script[2:]

                port_title = gameinfo_element.find('name')
                if port_title is None:
                    logger.debug(f"Cant find name tag for {port_script}")
                    port_title = port_script_file.stem
                else:
                    port_title = port_title.text.strip()

                port_image = gameinfo_element.find('image')
                if port_image is not None:
                    port_image = port_image.text.strip()
                    if port_image.startswith('./'):
                        port_image = port_image[2:]

                    image_file = self.hm.ports_dir / port_image
                    if not image_file.is_file():
                        logger.debug(f"Cant find image file {image_file}")
                        image_file = None

                    logger.info(f"{port_image}: {image_file}")
                else:
                    logger.debug(f"Cant find image tag.")
                    image_file = None

                logger.debug(f"{port_mode} -- {image_file}")

                if port_mode == 'roms':
                    if image_file is not None:
                        target_file = ROM_IMAGE_DIR / (port_script_file.stem + "-pre" + image_file.suffix)
                        logger.debug(f"Copying {str(image_file)} to {str(target_file)}")
                        shutil.copy(image_file, target_file)

                    target_file = ROM_SCRIPT_DIR / (port_script_file.name)
                    logger.debug(f"Copying {str(port_script_file)} to {str(target_file)}")
                    shutil.copy(port_script_file, target_file)

                elif port_mode == 'ports':
                    new_port_dir = PORT_DIR / f"portmaster-{name_cleaner(port_script_file.stem)}"

                    new_port_dir.mkdir(0o755, parents=True, exist_ok=True)

                    logger.debug(f"Creating {str(new_port_dir / 'config.json')}")
                    with open(new_port_dir / "config.json", "w") as fh:
                        fh.write(
                            PORT_CONFIG_JSON
                            .replace("{{PORTTITLE}}", port_title)
                            .replace("{{PORTNAME}}", new_port_dir.name.lower())
                            ## A-PEH ESC-A-PEH
                            .replace("{{PORTSCRIPT}}", str(port_script_file).replace(' ', '\\\\ ')))

                    if image_file is not None:
                        target_file = new_port_dir / ("icon-pre" + image_file.suffix)
                        logger.debug(f"Copying {str(image_file)} to {str(target_file)}")
                        shutil.copy(image_file, target_file)


class PlatformMiyoo(PlatformBase):
    WANT_XBOX_FIX = True

    def first_run(self):
        self.portmaster_install()

    def portmaster_install(self):
        """
        Move files into place.
        """

        MY_DIR = self.hm.tools_dir / "PortMaster" / "miyoo"
        PM_DIR = self.hm.tools_dir / "PortMaster"

        # ACTIVATE THE CONTROL
        logger.debug(f'Copy {MY_DIR / "control.txt"} -> {PM_DIR / "control.txt"}')
        shutil.copy(MY_DIR / "control.txt", PM_DIR / "control.txt")

        # ACTIVATE THE PORTMASTER
        logger.debug(f'Copy {MY_DIR / "PortMaster.txt"} -> {PM_DIR / "PortMaster.sh"}')
        shutil.copy(MY_DIR / "PortMaster.txt", PM_DIR / "PortMaster.sh")

        # CONTROL HACK
        CONTROL_HACK = Path("/root/.local/share/PortMaster/control.txt")
        if not CONTROL_HACK.parent.is_dir():
            CONTROL_HACK.parent.mkdir(parents=True)

        logger.debug(f'Copy {MY_DIR / "control.txt"} -> {CONTROL_HACK}')
        shutil.copy(MY_DIR / "control.txt", CONTROL_HACK)


class PlatformTesting(PlatformBase):
    WANT_XBOX_FIX = False
    WANT_SWAP_BUTTONS = False

    def gamelist_file(self):
        return self.hm.scripts_dir / 'gamelist.xml'


HM_PLATFORMS = {
    'arkos':     PlatformArkOS,
    'amberelec': PlatformAmberELEC,
    'emuelec':   PlatformEmuELEC,
    'unofficialos': PlatformUOS,
    'jelos':     PlatformJELOS,
    'rocknix':   PlatformROCKNIX,
    'batocera':  PlatformBatocera,
    'reglinux':  PlatformREGLinux,
    'knulli':    PlatformKnulli,
    'muos':      PlatformmuOS,
    'miyoo':     PlatformMiyoo,
    'trimui':    PlatformTrimUI,
    'retrodeck': PlatformRetroDECK,
    'darwin':    PlatformTesting,
    'default':   PlatformBase,
    # 'default': PlatformAmberELEC,
    }


__all__ = (
    'PlatformBase',
    'HM_PLATFORMS',
    )

