
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
    MOVE_PM_BASH = False
    MOVE_PM_BASH_DIR = None
    ES_NAME = None

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

    BLANK_GAMELIST_XML = """<?xml version='1.0' encoding='utf-8'?>\n<gameList />\n"""

    def __init__(self, hm):
        self.hm = hm
        self.added_ports = set()
        self.removed_ports = set()

    def loaded(self):
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

                for child in gameinfo_element:
                    # Check if the child element is in the predefined list
                    if child.tag in self.XML_ELEMENT_MAP:
                        gamelist_element = gamelist_update.find(self.XML_ELEMENT_MAP[child.tag])

                        if gamelist_element is None:
                            gamelist_element = ET.SubElement(gamelist_update, self.XML_ELEMENT_MAP[child.tag])

                        gamelist_element.text = child.text

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
    ...


class PlatformBatocera(PlatformBase):
    MOVE_PM_BASH = True
    ES_NAME = "batocera-es"

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


class PlatformPhasmidOS(PlatformBatocera):
    ...


class PlatformArkOS(PlatformGCD_PortMaster, PlatformBase):
    MOVE_PM_BASH = True
    ES_NAME = 'emulationstation'

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
        return self.hm.ports_dir / 'gamelist.xml'


class PlatformRetroDECK(PlatformBase):
    MOVE_PM_BASH = False
    ES_NAME = 'es-de'

    def gamelist_file(self):
        return self.hm.ports_dir / 'gamelist.xml'

    def first_run(self):
        self.portmaster_install()

    def portmaster_install(self):
        """
        Move files into place.
        """

        RD_DIR = self.hm.tools_dir / "PortMaster" / "retrodeck"
        PM_DIR = self.hm.tools_dir / "PortMaster"

        # ACTIVATE THE RetroDECK CONTROL
        logger.debug(f'Copy {RD_DIR / "control.txt"} -> {PM_DIR / "control.txt"}')
        shutil.copy(RD_DIR / "control.txt", PM_DIR / "control.txt")

        CONTROL_HACK = Path(Path.home() / ".var/app/net.retrodeck.retrodeck/data/PortMaster/")
        if not CONTROL_HACK.parent.is_dir():
            CONTROL_HACK.parent.mkdir(parents=True)
        
        logger.debug(f'Copy {RD_DIR / "control.txt"} -> {CONTROL_HACK}')
        shutil.copy(RD_DIR / "control.txt", CONTROL_HACK)

        # PEBKAC RD
        logger.debug(f'Move {RD_DIR / "PortMaster.txt"} -> {PM_DIR / "PortMaster.sh"}')
        shutil.copy(RD_DIR / "PortMaster.txt", PM_DIR / "PortMaster.sh")

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

        if not Path("/opt/graphicsmagick").is_dir():
            return

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

                        target_file = INFO_BOX_DIR / (path_merge + image_file.suffix)
                        logger.debug(f"copying {str(image_file)} to {str(target_file)}")
                        shutil.copy(image_file, target_file)

                        screenshot_file = None
                        if (image_file.parent / 'screenshot.jpg').is_file():
                            screenshot_file = (image_file.parent / 'screenshot.jpg')

                        elif (image_file.parent / 'screenshot.png').is_file():
                            screenshot_file = (image_file.parent / 'screenshot.png')

                        if screenshot_file:
                            target_file = INFO_PREVIEW_DIR / (path_merge + image_file.suffix)
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
        logger.debug(f'Move {TU_DIR / "PortMaster.txt"} -> {self.hm.tools_dir / ".." / "launch.sh"}')
        shutil.copy(TU_DIR / "PortMaster.txt", self.hm.tools_dir / '..' / "launch.sh")

        TASK_SET = Path(PM_DIR / "tasksetter")
        if TASK_SET.is_file():
            TASK_SET.unlink()

        TASK_SET.touch()

    def gamelist_file(self):
        return SPECIAL_GAMELIST_CODE

    def gamelist_add(self, gameinfo_file):
        if not gameinfo_file.is_file():
            return

        INFO_PREVIEW_DIR = Path("/mnt/SDCARD/Imgs/PORTS")

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

                        target_file = INFO_PREVIEW_DIR / (path_merge + image_file.suffix)
                        logger.debug(f"copying {str(image_file)} to {str(target_file)}")
                        shutil.copy(image_file, target_file)

            # HAHA THIS IS FUCKED
            self.added_ports.add('GAMELIST UPDATER')


class PlatformTesting(PlatformBase):
    WANT_XBOX_FIX = False

    def gamelist_file(self):
        return self.hm.ports_dir / 'gamelist.xml'


HM_PLATFORMS = {
    'arkos':     PlatformArkOS,
    'amberelec': PlatformAmberELEC,
    'emuelec':   PlatformEmuELEC,
    'unofficialos': PlatformUOS,
    'jelos':     PlatformJELOS,
    'rocknix':   PlatformROCKNIX,
    'batocera':  PlatformBatocera,
    'phasmidos': PlatformPhasmidOS,
    'muos':      PlatformmuOS,
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

