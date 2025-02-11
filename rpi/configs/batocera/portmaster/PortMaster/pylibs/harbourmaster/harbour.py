
# System imports
import datetime
import fnmatch
import functools
import hashlib
import json
import os
import pathlib
import shutil
import subprocess
import zipfile

from pathlib import Path
from gettext import gettext as _

# Included imports
import utility

from loguru import logger
from utility import cprint

# Module imports
from .config import *
from .hardware import *
from .util import *
from .info import *
from .source import *
from .platform import *
from .captain import *

################################################################################
## Config loading
class HarbourMaster():
    __PORTS_INFO = None
    __PORTERS = None

    CONFIG_VERSION = 2
    DEFAULT_CONFIG = {
        'version': CONFIG_VERSION,
        'first-run': True,
        'ports_info_checked': None,
        'porters_checked': None,
        'show_experimental': False,
        }

    INFO_CHECK_INTERVAL = (60 * 60 * 1)

    PORT_INFO_URL      = "https://github.com/PortsMaster/PortMaster-Info/raw/main/"
    PORTS_INFO_URL     = PORT_INFO_URL + "ports_info.json"
    FEATURED_PORTS_URL = PORT_INFO_URL + "featured_ports.json"
    PORTERS_URL        = PORT_INFO_URL + "porters.json"
    SOURCES_URL        = PORT_INFO_URL + "sources.json"

    def __init__(self, config, *, tools_dir=None, ports_dir=None, scripts_dir=None, temp_dir=None, callback=None):
        """
        config = load_config()
        """
        self.__PORT_INFO_CACHE = {}

        if tools_dir is None:
            tools_dir = HM_TOOLS_DIR

        if ports_dir is None:
            ports_dir = HM_PORTS_DIR

        if scripts_dir is None:
            scripts_dir = HM_SCRIPTS_DIR

        if isinstance(tools_dir, str):
            tools_dir = Path(tools_dir)
        elif not isinstance(tools_dir, pathlib.PurePath):
            raise ValueError('tools_dir')

        if isinstance(ports_dir, str):
            ports_dir = Path(ports_dir)
        elif not isinstance(ports_dir, pathlib.PurePath):
            raise ValueError('ports_dir')

        if callback is None:
            callback = Callback()

        self.temp_dir   = temp_dir
        self.tools_dir  = tools_dir
        self.cfg_dir    = tools_dir / "PortMaster" / "config"
        self.libs_dir   = tools_dir / "PortMaster" / "libs"
        self.themes_dir = tools_dir / "PortMaster" / "themes"
        self.ports_dir  = ports_dir
        self.scripts_dir  = scripts_dir
        self.cfg_file     = self.cfg_dir / "config.json"
        self.runtimes_file = self.cfg_dir / "runtimes.json"

        self.sources = {}
        self.config = {
            'no-check': config.get('no-check', False),
            'offline': config.get('offline', False),
            'quiet': config.get('quiet', False),
            'debug': config.get('debug', False),
            }

        self.device = device_info()

        if self.device['name'].lower() in HM_PLATFORMS:
            self.platform = HM_PLATFORMS[self.device['name'].lower()](self)
        else:
            self.platform = HM_PLATFORMS['default'](self)

        self.callback = callback
        self.ports = []
        self.utils = []

        self.ports_dir.mkdir(0o755, parents=True, exist_ok=True)
        self.scripts_dir.mkdir(0o755, parents=True, exist_ok=True)
        self.themes_dir.mkdir(0o755, parents=True, exist_ok=True)
        self.libs_dir.mkdir(0o755, parents=True, exist_ok=True)

        with self.callback.enable_messages():
            self.callback.message(_("Loading..."))

            if not self.cfg_file.is_file():
                self.cfg_data = self.DEFAULT_CONFIG.copy()
            else:
                with open(self.cfg_file, 'r') as fh:
                    self.cfg_data = json.load(fh)

            if self.cfg_data.get('first-run', True) or not self.cfg_dir.is_dir():
                self.cfg_dir.mkdir(0o755, parents=True, exist_ok=True)

                for source_name in HM_SOURCE_DEFAULTS:
                    with (self.cfg_dir / source_name).open('w') as fh:
                        fh.write(HM_SOURCE_DEFAULTS[source_name])

            if self.cfg_data.get('first-run', True):
                self.platform.first_run()

                self.cfg_data['first-run'] = False

            if 'theme' not in self.cfg_data:
                self.cfg_data['theme'] = 'default_theme'

            self.cfg_data.setdefault('show_experimental', False)

            if self.cfg_data.get('version', 1) != self.CONFIG_VERSION:
                self.update_config()
                self.cfg_data['version'] = self.CONFIG_VERSION

            self.load_info()

            self.load_sources()

            self.load_ports()

            self.platform.loaded()

            self.save_config()

    def update_config(self):
        version = self.cfg_data.get('version', 1)
        if version:
            # Upgrade from version 1 to 2
            logger.debug(f"Upgrading PortMaster/config/config.json: 1 -> 2")

            for image_dir in self.cfg_dir.glob("images_*"):
                if not image_dir.is_dir():
                    continue

                logger.debug(f"rmtree {image_dir}")
                shutil.rmtree(str(image_dir))

            for source_file in self.cfg_dir.glob("*portmaster*.source.json"):
                if not source_file.is_file():
                    continue

                logger.debug(f"unlink {source_file}")
                source_file.unlink()

            for source_name in HM_SOURCE_DEFAULTS:
                with (self.cfg_dir / source_name).open('w') as fh:
                    fh.write(HM_SOURCE_DEFAULTS[source_name])

                logger.debug(f"creating {source_name}")

            version = 2

    def save_config(self):
        with open(self.cfg_file, 'w') as fh:
            json.dump(self.cfg_data, fh, indent=4, sort_keys=True)

        with open(self.runtimes_file, 'w') as fh:
            json.dump(self.runtimes_info, fh, indent=4, sort_keys=True)

    def ports_info(self):
        if self.__PORTS_INFO is None:
            with open(self.cfg_dir / "ports_info.json", 'r') as fh:
                self.__PORTS_INFO = json_safe_load(fh)

            if self.__PORTS_INFO is None:
               self.__PORTS_INFO = {"items": {}, "md5": {}, "ports": {}, "portsmd_fix": {}}

        return self.__PORTS_INFO

    def porters(self):
        if self.__PORTERS is None:
            with open(self.cfg_dir / "porters.json", 'r') as fh:
                self.__PORTERS = json_safe_load(fh)

            if self.__PORTERS is None:
               self.__PORTERS = {}

        return self.__PORTERS

    def load_info(self, force_load=False):
        self.callback.message("- {}".format(_("Loading Info.")))
        info_file = self.cfg_dir / "ports_info.json"
        info_file_md5 = self.cfg_dir / "ports_info.md5"

        porters_file = self.cfg_dir / "porters.json"
        featured_ports_file = self.cfg_dir / "featured_ports.json"
        featured_ports_dir = self.cfg_dir / "featured_ports/"
        self.runtimes_info = None

        if self.runtimes_file.is_file():
            with open(self.runtimes_file, 'r') as fh:
                self.runtimes_info = json_safe_load(fh)

            self.list_runtimes()

        if self.runtimes_info is None:
            self.runtimes_info = {}

        if self.config['offline'] or self.config['no-check']:
            if not porters_file.is_file():
                with open(porters_file, 'w') as fh:
                    fh.write('{}')

            if not info_file.is_file():
                with open(info_file, 'w') as fh:
                    fh.write('{"items": {}, "md5": {}, "ports": {}, "portsmd_fix": {}}')

            if not featured_ports_file.is_file():
                with open(featured_ports_file, 'w') as fh:
                    fh.write('[]')

            return

        if force_load is True or not featured_ports_file.is_file() or (
                not self.config['no-check'] and (
                    self.cfg_data.get('featured_ports_checked') is None or
                    datetime_compare(self.cfg_data['featured_ports_checked']) >= self.INFO_CHECK_INTERVAL)):

            self.callback.message("  - {}".format(_("Fetching latest featured ports.")))
            ports_list_data = fetch_text(self.FEATURED_PORTS_URL)

            with open(featured_ports_file, 'w') as fh:
                fh.write(ports_list_data)

            self.featured_ports()

            self.cfg_data['featured_ports_checked'] = datetime.datetime.now().isoformat()

        if not info_file.is_file():
            self.callback.message("  - {}".format(_("Fetching latest info.")))
            info_md5 = fetch_text(self.PORTS_INFO_URL + '.md5')
            info_data = fetch_text(self.PORTS_INFO_URL)

            with open(info_file, 'w') as fh:
                fh.write(info_data)

            with open(info_file_md5, 'w') as fh:
                fh.write(info_md5)

            self.cfg_data['ports_info_checked'] = datetime.datetime.now().isoformat()

        elif force_load is True or not self.config['no-check'] and (
                self.cfg_data.get('ports_info_checked') is None or
                datetime_compare(self.cfg_data['ports_info_checked']) >= self.INFO_CHECK_INTERVAL):

            info_md5 = fetch_text(self.PORTS_INFO_URL + '.md5')
            if not info_file_md5.is_file() or info_md5 != info_file_md5.read_text().strip():
                self.callback.message("  - {}".format(_("Fetching latest info.")))
                info_data = fetch_text(self.PORTS_INFO_URL)

                with open(info_file, 'w') as fh:
                    fh.write(info_data)

                with open(info_file_md5, 'w') as fh:
                    fh.write(info_md5)

            self.cfg_data['ports_info_checked'] = datetime.datetime.now().isoformat()

        if force_load is True or not porters_file.is_file() or (
                not self.config['no-check'] and (
                    self.cfg_data.get('porters_checked') is None or
                    datetime_compare(self.cfg_data['porters_checked']) >= self.INFO_CHECK_INTERVAL)):

            self.callback.message("  - {}".format(_("Fetching latest porters.")))
            porters_data = fetch_text(self.PORTERS_URL)

            with open(porters_file, 'w') as fh:
                fh.write(porters_data)

            self.cfg_data['porters_checked'] = datetime.datetime.now().isoformat()

    def load_sources(self):
        source_files = list(self.cfg_dir.glob('*.source.json'))
        source_files.sort()

        self.callback.message("  - {}".format(_("Loading Sources.")))

        check_keys = {'version': None, 'prefix': None, 'api': HM_SOURCE_APIS, 'name': None, 'last_checked': None, 'data': None}
        for source_file in source_files:
            with source_file.open() as fh:
                source_data = json_safe_load(fh)

            if source_data is None:
                continue

            fail = False
            for check_key, check_value in check_keys.items():
                if check_key not in source_data:
                    logger.error(f"Missing key {check_key!r} in {source_file}.")
                    fail = True
                    break

                if check_value is not None and source_data[check_key] not in check_value:
                    logger.error(f"Unknown {check_key!r} in {source_file}: {source_data[check_key]}.")
                    fail = True
                    break

            if fail:
                continue

            # V1 to V2
            if source_data['api'] == 'PortMasterV1':
                source_data['api'] = 'PortMasterV2'
                source_data['last_checked'] = None
                source_data['data'] = {}

            # V2 to V3
            if source_data['api'] == 'PortMasterV2' and source_data['name'] == 'PortMaster':
                source_data['api'] = 'PortMasterV3'
                source_data['url'] = "https://github.com/PortsMaster/PortMaster-New/releases/latest/download/ports.json"
                source_data['last_checked'] = None
                source_data['data'] = {}

            # V2 to V3
            if source_data['api'] == 'PortMasterV2' and source_data['name'] == 'PortMaster Multiverse':
                source_data['api'] = 'PortMasterV3'
                source_data['url'] = "https://github.com/PortsMaster-MV/PortMaster-MV-New/releases/latest/download/ports.json"
                source_data['last_checked'] = None
                source_data['data'] = {}

            source = HM_SOURCE_APIS[source_data['api']](self, source_file, source_data)

            self.sources[source_data['prefix']] = source


    def _get_pm_signature(self, file_name):
        """
        Returns (file_name, original_file_name, port_name)

        This handles files being renamed, hopefully.
        """
        if not str(file_name).lower().endswith('.sh'):
            return None

        # See if the file has a signature
        pm_signature = load_pm_signature(file_name)

        if pm_signature is None:
            ports_info = self.ports_info()

            # If not look it up by name
            port_owners = get_dict_list(ports_info['items'], file_name.name)
            if len(port_owners) > 0:
                add_pm_signature(file_name, [port_owners[0], file_name.name])
                return (file_name.name, file_name.name, port_owners[0])

            # Finally try by the md5sum of the file
            md5 = hash_file(file_name)
            if md5 in ports_info['md5']:
                other_name = ports_info['md5'][md5]

                port_owners = get_dict_list(ports_info['items'], other_name)

                if len(port_owners) > 0:
                    add_pm_signature(file_name, [port_owners[0], other_name])
                    return (other_name, file_name.name, port_owners[0])

            return (file_name.name, file_name.name, None)

        return (file_name.name, pm_signature[1], pm_signature[0])

    def _load_port_info(self, port_file):
        """
        Loads a <blah>.port.json file.

        It will try its best to recover the data into a usable state.

        returns None if it is unusuable.
        """
        port_info = port_info_load(port_file, do_default=True)

        ports_info = self.ports_info()
        changed = False

        # Its possible for the port_info to be in a bad way, lets try and fix it.
        if port_info.get('name', None) is None:
            # No name, check the items and see if it matches our internal database, we can get the port name from a script.
            logger.error(f"No 'name' in {port_file!r}")
            if port_info.get('items', None) is None:
                # Can't do shit if the items is empty. :(
                logger.error(f"Unable to load {port_file}, missing 'name' and 'items' keys.")
                return None

            for item in port_info['items']:
                port_temp = ports_info['items'].get(item.casefold(), None)
                if isinstance(port_temp, str):
                    break
            else:
                # Couldn't find the port.
                logger.error(f"Unable to load {port_file}, unknown items.")
                return None

            changed = True
            port_info['name'] = name_cleaner(port_temp[0])

        # Force the port_info['name'] to be lowercase/casefolded.
        if port_info['name'] != name_cleaner(port_info['name']):
            port_info['name'] = name_cleaner(port_info['name'])
            changed = True

        if port_info.get('items', None) is None:
            # This shouldn't happen, but we can restore it.
            logger.error(f"No 'items' in {port_info!r} for {port_file}")

            if port_info['name'] not in ports_info['ports']:
                # Sorry, cant work it out.
                logger.error(f"Unable to figure it out, unknown port {port_info['name']}")
                return None

            changed = True
            port_info['items'] = ports_info['ports'][port_info['name']]['items'][:]

        if port_info['attr']['title'] in ("", None):
            for item in port_info['items']:
                if item.casefold().endswith('.sh'):
                    port_info['attr']['title'] = item[:-3]
                    changed = True
                    break

        if port_info.get('status', None) is None:
            changed = True
            port_info['status'] = {
                'source': 'Unknown',
                'md5': None,
                'status': 'Unknown',
                }

        if port_info.get('source', None) is not None:
            changed = True
            del port_info['source']

        port_info['changed'] = changed

        return port_info

    def _iter_ports_dir(self):
        if self.ports_dir != self.scripts_dir:
            yield from self.scripts_dir.iterdir()

        yield from self.ports_dir.iterdir()

    def _ports_dir_exists(self, file_name):
        if (self.scripts_dir / file_name).exists():
            return True

        return (self.ports_dir / file_name).exists()

    def _ports_dir_is_file(self, file_name):
        if (self.scripts_dir / file_name).is_file():
            return True

        return (self.ports_dir / file_name).is_file()

    def _ports_dir_is_dir(self, file_name):
        if (self.scripts_dir / file_name).is_dir():
            return True

        return (self.ports_dir / file_name).is_dir()

    def _ports_dir_relative_to(self, path):
        try:
            return path.relative_to(self.scripts_dir)

        except ValueError:
            return path.relative_to(self.ports_dir)

    def _ports_dir_file(self, file_name, is_script=False):
        if is_script:
            return (self.scripts_dir / file_name)

        return (self.ports_dir / file_name)

    @timeit
    def load_ports(self):
        """
        Find all installed ports, because ports can be installed by zips we need to recheck every time.
        """
        port_files = list(self.ports_dir.glob('*/*.port.json')) + list(self.ports_dir.glob('*/port.json'))
        port_files.sort()

        self.installed_ports = {}
        self.broken_ports = {}
        self.unknown_ports = []
        all_items = {}
        unknown_files = []

        all_ports = {}
        ports_files = {}
        file_renames = {}

        ports_info = self.ports_info()
        self.__PORT_INFO_CACHE.clear()

        self.callback.message("  - {}".format(_("Loading Ports.")))

        """
        This is a bit of a heavy function but it does the following.

        Phase 1:
        - Load all *.port.json files, fix any issues with them
    
        Phase 2:
        - Check all files/dirs in the ports_dir, see if they are "owned" by a port, find any renamed files.

        Phase 3:
        - Find any new ports, create the port.json files as necessary.

        Phase 4:
        - Finalise any data, figure out if the ports are broken etc.

        DONE.

        """

        ## Rename old <portname>.port.json to port.json.
        port_dirs = {}

        for port_file in port_files:
            port_dir = port_file.parent.name

            port_dirs.setdefault(port_dir, {})[port_file.name] = port_file

        changes = False
        for port_dir in port_dirs:
            if port_dir == 'alephone':
                continue

            # Rename the port.json
            port_jsons = list(port_dirs[port_dir].keys())

            if len(port_jsons) == 1:
                if 'port.json' not in port_jsons:
                    port_dir_path = port_dirs[port_dir][port_jsons[0]].parent

                    ## Rename
                    logger.debug(f"rename {port_dir_path / port_jsons[0]} to {port_dir_path / 'port.json'}")
                    (port_dir_path / port_jsons[0]).rename(port_dir_path / 'port.json')
                    changes = True

            elif len(port_jsons) == 2:
                if 'port.json' not in port_jsons:
                    ## HRMMmmmmm
                    logger.debug(f'Multiple port.json files in {port_dir}: {port_jsons}')
                    continue

                else:
                    # Remove the old one.
                    port_jsons.remove('port.json')
                    port_dir_path = port_dirs[port_dir][port_jsons[0]].parent
                    logger.debug(f"unlink {port_dir_path / port_jsons[0]}")
                    (port_dir_path / port_jsons[0]).unlink()
                    changes = True

            else:
                if 'port.json' not in port_jsons:
                    ## HRMMmmmmm
                    logger.debug(f'Multiple port.json files in {port_dir}: {port_jsons}')
                    continue

        del port_dirs

        if changes:
            # Reload the port_files list.
            port_files = list(self.ports_dir.glob('*/*.port.json')) + list(self.ports_dir.glob('*/port.json'))


        ## Phase 1: Load all the known ports with port.json files
        for port_file in port_files:
            port_info = self._load_port_info(port_file)

            if port_info is None:
                continue

            # The files attribute keeps track of file renames.
            if port_info.get('files', None) is None:
                port_info['files'] = {
                    'port.json': str(self._ports_dir_relative_to(port_file)),
                    }
                port_info['changed'] = True

            if 'port.json' not in port_info['files']:
                port_info['files']['port.json'] = str(self._ports_dir_relative_to(port_file))
                port_info['changed'] = True

            if port_info['attr']['porter'] is None:
                port_info['attr']['porter'] = ['Unknown']
                port_info['changed'] = True

            if isinstance(port_info['attr']['porter'], str):
                port_info['attr']['porter'] = ports_info['portsmd_fix'].get(port_info['attr']['porter'].lower(), port_info['attr']['porter'])
                port_info['changed'] = True

            # Add all the root dirs/scripts in the port
            for item in port_info['items']:
                add_dict_list_unique(all_items, item, port_info['name'])

                if self._ports_dir_exists(item):
                    if item not in get_dict_list(port_info['files'], item):
                        add_dict_list_unique(port_info['files'], item, item)
                        port_info['changed'] = True

            # And any optional ones.
            for item in get_dict_list(port_info, 'items_opt'):
                add_dict_list_unique(all_items, item, port_info['name'])

                if self._ports_dir_exists(item):
                    if item not in get_dict_list(port_info['files'], item):
                        add_dict_list_unique(port_info['files'], item, item)
                        port_info['changed'] = True

            all_ports[port_info['name']] = port_info
            ports_files[port_info['name']] = port_file

        ## Phase 2: Check all files
        for file_item in self._iter_ports_dir():
            ## Skip these
            if file_item.name.lower() in (
                    'gamelist.xml',
                    'gamelist.xml.old',
                    'harbourmaster',
                    'images',
                    'manuals',
                    'portmaster',
                    'portmaster.sh',
                    'thememaster',
                    'thememaster.sh',
                    'videos',
                    ):
                continue

            file_name = file_item.name
            if file_item.is_dir():
                file_name += '/'

            elif file_item.suffix.casefold() not in ('.sh', ):
                # Ignore non bash files.
                continue

            if file_item.is_file() and b"PORTMASTER NO TOUCHY" in file_item.read_bytes():
                logger.debug(f"NO TOUCHY {file_name}")
                continue

            port_owners = get_dict_list(all_items, file_name)

            if len(port_owners) > 0:
                # We know what port this file belongs to.
                # Add signature to files
                if file_item.suffix.casefold() in ('.sh', ):
                    pm_signature = load_pm_signature(file_item)

                    if pm_signature is None:
                        logger.debug(f"add_pm_signature({file_item!r}, [{port_owners[0]!r}, {file_name!r}])")
                        add_pm_signature(file_item, [port_owners[0], file_name])
                        continue

                    if pm_signature[0] in all_ports:
                        port_info = all_ports[pm_signature[0]]
                        # print(file_name, pm_signature)
                        if file_name not in get_dict_list(port_info['files'], pm_signature[1]):
                            add_dict_list_unique(port_info['files'], pm_signature[1], file_name)
                            print("added")
                            port_info["changed"] = True

                continue

            if not file_name.endswith('/'):
                # See if the file has been renamed, thanks Christian!
                pm_signature = self._get_pm_signature(file_item)
                if pm_signature is None:
                    # Shouldn't happen
                    unknown_files.append(file_name)
                    continue

                if pm_signature[0] != pm_signature[1]:
                    # We atleast know the file is renamed.
                    file_renames[pm_signature[1]] = pm_signature[0]

                if pm_signature[2] is None:
                    # Unknown port?
                    unknown_files.append(file_name)
                    continue

                if pm_signature[2] in all_ports:
                    port_info = all_ports[pm_signature[2]]
                    add_dict_list_unique(all_items, pm_signature[0], pm_signature[2])

                    if pm_signature[0] not in get_dict_list(port_info['files'], pm_signature[1]):
                        add_dict_list_unique(port_info['files'], pm_signature[1], pm_signature[0])
                        port_info["changed"] = True

                    continue

            unknown_files.append(file_name)

        # from pprint import pprint
        # pprint(all_items)
        # pprint(file_renames)
        # pprint(unknown_files)

        ## Create new ports.
        new_ports = []
        for unknown_file in unknown_files:
            port_owners = get_dict_list(ports_info['items'], unknown_file)

            if len(port_owners) == 1:
                add_list_unique(new_ports, port_owners[0])

            elif len(port_owners) == 0:
                if unknown_file.casefold().endswith('.sh'):
                    re_name = file_renames.get(unknown_file, None)
                    if re_name is not None:
                        port_owners = get_dict_list(ports_info['items'], re_name)

                        if len(port_owners) == 1:
                            if port_owners[0] in all_ports:
                                port_info = all_ports[port_owners[0]]
                                if unknown_file not in get_dict_list(port_info['files'], re_name):
                                    add_dict_list_unique(port_info['files'], re_name, unknown_file)
                                    port_info['changed'] = True

                            else:
                                add_list_unique(new_ports, port_owners[0])

                            continue

                    ## Keep track of unknown bash scripts.
                    logger.info(f"Unknown port: {unknown_file}")
                    self.unknown_ports.append(unknown_file)

        ## Create new port.json files for any new ports, these only contain the most basic of information.
        for new_port in new_ports:
            port_info_raw = ports_info['ports'][new_port]

            port_info = port_info_load(port_info_raw)

            port_file = self._ports_dir_file(port_info_raw['file'])

            ## Load extra info
            for source in self.sources.values():
                port_name = source.clean_name(port_info['name'])

                if port_name in source.ports:
                    port_info_merge(port_info, source.port_info(port_name))
                    break

            if port_info['attr']['title'] in ("", None):
                for item in port_info['items']:
                    if item.casefold().endswith('.sh'):
                        port_info['attr']['title'] = item[:-3]
                        break

            if port_info['attr']['porter'] is None:
                port_info['attr']['porter'] = ['Unknown']

            if isinstance(port_info['attr']['porter'], str):
                port_info['attr']['porter'] = ports_info['portsmd_fix'].get(
                    port_info['attr']['porter'].lower(),
                    port_info['attr']['porter'])

            if port_info.get('status', None) is None:
                port_info['status'] = {}

            port_info['name'] = port_info['name'].casefold()

            port_info['status']['source'] = "Unknown"
            port_info['status']['md5'] = None
            port_info['status']['status'] = "Unknown"

            port_info['files'] = {
                'port.json': port_info_raw['file'],
                }

            # Add all the root dirs/scripts in the port
            for item in port_info['items']:
                if self._ports_dir_exists(item):
                    if item not in get_dict_list(port_info['files'], item):
                        add_dict_list_unique(port_info['files'], item, item)
                        port_info['changed'] = True

                if item in file_renames:
                    item_rename = file_renames[item]
                    if self._ports_dir_exists(item_rename):
                        if item_rename not in get_dict_list(port_info['files'], item):
                            add_dict_list_unique(port_info['files'], item, item_rename)
                            port_info['changed'] = True

            # And any optional ones.
            for item in get_dict_list(port_info, 'items_opt'):
                if self._ports_dir_exists(item):
                    if item not in get_dict_list(port_info['files'], item):
                        add_dict_list_unique(port_info['files'], item, item)
                        port_info['changed'] = True

                if item in file_renames:
                    item_rename = file_renames[item]
                    if self._ports_dir_exists(item_rename):
                        if item_rename not in get_dict_list(port_info['files'], item):
                            add_dict_list_unique(port_info['files'], item, item_rename)
                            port_info['changed'] = True

            port_info['changed'] = True

            all_ports[port_info['name']] = port_info
            ports_files[port_info['name']] = port_file

        for port_name in all_ports:
            port_info = all_ports[port_name]

            bad = False
            for port_file in list(port_info['files']):
                file_names = get_dict_list(port_info['files'], port_file)

                for file_name in list(file_names):
                    if not self._ports_dir_exists(file_name):
                        remove_dict_list(port_info['files'], port_file, file_name)
                        port_info['changed'] = True

            for item in port_info['items']:
                if len(get_dict_list(port_info['files'], item)) == 0:
                    logger.error(f"Port {port_name} missing {item}.")
                    bad = True

            if bad:
                if port_info['status'].get('status', 'Unknown') != 'Broken':
                    port_info['status']['status'] = 'Broken'
                    port_info['changed'] = True

                self.broken_ports[port_name] = port_info

            else:
                if port_info['status'].get('status', 'Unknown') != 'Installed':
                    port_info['status']['status'] = 'Installed'
                    port_info['changed'] = True

                self.installed_ports[port_name] = port_info

            changed = port_info['changed']
            del port_info['changed']

            if 'source' in port_info:
                del port_info['source']
                changed = True

            if changed:
                if ports_files[port_name].parent.is_dir():
                    logger.debug(f"Dumping {str(ports_files[port_name])}: {port_info}")
                    with ports_files[port_name].open('wt') as fh:
                        json.dump(port_info, fh, indent=4)
                else:
                    logger.warning(f"Unable to dump {str(ports_files[port_name])}: {port_info}")

    def port_info_attrs(self, port_info):
        runtime_fix = {
            'frt':  'godot',
            'mono': 'mono',
            'solarus': 'solarus',
            'jdk11': 'jre',
            }

        attrs = []
        runtime = port_info.get('attr', {}).get('runtime', None)
        if runtime is not None:
            for runtime_key, runtime_attr in runtime_fix.items():
                if runtime_key in runtime:
                    add_list_unique(attrs, runtime_attr)

        for genre in port_info.get('attr', {}).get('genres', []):
            add_list_unique(attrs, genre.casefold())

        for porter in port_info.get('attr', {}).get('porter', []):
            add_list_unique(attrs, porter.casefold())

        rtr = port_info.get('attr', {}).get('rtr', False)
        if rtr:
            add_list_unique(attrs, 'rtr')

        exp = port_info.get('attr', {}).get('exp', False)
        if exp:
            add_list_unique(attrs, 'exp')

        if port_info['name'].casefold() in self.installed_ports:
            add_list_unique(attrs, 'installed')

        if port_info['name'].casefold() in self.broken_ports:
            add_list_unique(attrs, 'installed')
            add_list_unique(attrs, 'broken')

        if 'source' in port_info and 'status' in port_info:
            source_md5 = port_info['source'].get('md5', None)
            status_md5 = port_info['status'].get('md5', None)
            if status_md5 is not None and source_md5 != status_md5:
                add_list_unique(attrs, 'update available')

        # print(f"{port_info['name']}: {exp!r} {attrs}")

        return attrs

    def match_filters(self, port_filters, port_info):
        port_attrs = self.port_info_attrs(port_info)

        if not self.cfg_data['show_experimental'] and 'exp' in port_attrs:
            return False

        for port_filter in port_filters:
            if port_filter.casefold() not in port_attrs:
                return False

        return True

    def match_requirements(self, port_info):
        """
        Matches hardware capabilities to port requirements.
        """
        if not hasattr(self, '_TESTING'):
            self._TESTING = {}

        show = False
        capabilities = self.device['capabilities']

        requirements = port_info.get('attr', {}).get('reqs', [])[:]

        runtime = port_info.get('attr', {}).get('runtime', None)

        if runtime is not None:
            if not runtime.endswith('.squashfs'):
                runtime += '.squashfs'

            requirements.append('|'.join(self.runtimes_info.get(runtime, {}).get('remote', {}).keys()))
            show = True

        else:
            arch = port_info.get('attr', {}).get('arch', [])

            if isinstance(arch, list) and len(arch) > 0:
                requirements.append('|'.join(arch))

        if self.cfg_data.get('show_all', False):
            requirements = []

        result = match_requirements(capabilities, requirements)
        if PORTMASTER_DEBUG and port_info['name'] not in self._TESTING:
            if show:
                print(f"{port_info['name']}: {capabilities}, {requirements}: {result}")
            self._TESTING[port_info['name']] = True

        return result

    def list_ports(self, filters=[], sort_by='alphabetical', reverse=False):
        ## Filters can be genre, runtime
        if sort_by not in HM_SORT_ORDER:
            sort_by = HM_SORT_ORDER[0]

        sort_by_reverse_order = ('recently_added', 'recently_updated')
        if sort_by in sort_by_reverse_order:
            reverse = not reverse

        tmp_ports = {}
        not_installed = 'not installed' in filters
        if not_installed:
            filters = list(filters)
            filters.remove('not installed')

        if not not_installed and 'installed' in filters:
            for port_name in self.installed_ports:
                if name_cleaner(port_name) in tmp_ports:
                    continue

                new_port_info = self.port_info(port_name, installed=True)

                if not self.match_filters(filters, new_port_info):
                    continue

                tmp_ports[name_cleaner(port_name)] = new_port_info

            for port_name, port_info in self.broken_ports.items():
                if name_cleaner(port_name) in tmp_ports:
                    continue

                new_port_info = self.port_info(port_name, installed=True)

                if not self.match_filters(filters, new_port_info):
                    continue

                tmp_ports[name_cleaner(port_name)] = new_port_info

        for source_prefix, source in self.sources.items():
            for port_name in source.ports:
                if not_installed and (
                        name_cleaner(port_name) in self.installed_ports.keys() or
                        name_cleaner(port_name) in self.broken_ports.keys()):
                    continue

                if name_cleaner(port_name) in tmp_ports:
                    # print(f"- {port_name} skipping (1)")
                    continue

                new_port_info = self.port_info(port_name, installed=False)

                if not self.match_filters(filters, new_port_info):
                    # print(f"- {port_name} skipping (2)")
                    continue

                if not self.match_requirements(new_port_info):
                    # print(f"- {port_name} skipping (3)")
                    continue

                tmp_ports[name_cleaner(port_name)] = new_port_info

        ports = {
            port_name: port_info
            for port_name, port_info in sorted(
                tmp_ports.items(),
                key=lambda x: (PORT_SORT_FUNCS[sort_by](x[1]), x[0].casefold()),
                reverse=reverse)
            }

        return ports

    def featured_ports(self, pre_load=False):
        featured_ports_file = self.cfg_dir / "featured_ports.json"
        featured_ports_dir = self.cfg_dir / "featured_ports/"

        if not featured_ports_dir.is_dir():
            featured_ports_dir.mkdir(0o755)

        if not featured_ports_file.is_file():
            return []

        with featured_ports_file.open('r') as fh:
            featured_ports = json_safe_load(fh)

        if not isinstance(featured_ports, list):
            return []

        results = []
        for idx, port_list in enumerate(featured_ports):
            if not isinstance(port_list, dict):
                continue

            if port_list.get('name', None) in (None, ""):
                if pre_load:
                    logger.error(f"Bad featured_ports[{idx}]: Missing title info")
                continue

            if port_list.get('ports', None) is None:
                if pre_load:
                    logger.error(f"Bad featured_ports[{idx}]: Missing ports info")
                continue

            if not isinstance(port_list.get('ports', None), list):
                if pre_load:
                    logger.error(f"Bad featured_ports[{idx}]: bad ports item")
                continue

            port_list_image = port_list.get('image', None)
            if port_list_image is not None and port_list_image != "":
                port_list_image_url = self.PORT_INFO_URL + port_list_image
                port_list_image_file = featured_ports_dir / port_list_image.rsplit('/', 1)[-1]

                if not port_list_image_file.is_file():
                    download_info = download(port_list_image_file, port_list_image_url, callback=self.callback, no_check=True)

                    if download_info is None:
                        port_list_image = None

            if port_list_image is None:
                port_list_image_file = ""

            port_list_ports = {}
            for idx2, port_name in enumerate(port_list['ports']):
                port_info = self.port_info(port_name)
                if port_info is None:
                    if pre_load:
                        logger.error(f"Bad featured_ports[{idx}]['ports'][{idx}]: unknown port {port_name}")
                    continue

                # Only show ports in here that are possible to install.
                if not self.match_requirements(port_info):
                    continue

                port_list_ports[port_info['name']] = port_info

            if len(port_list_ports) == 0:
                # Don't show empty featured ports.
                continue

            full_port_list = {
                'name': port_list['name'],
                'image': port_list_image_file,
                'description': port_list.get('description', ""),
                'ports': port_list_ports,
                }

            results.append(full_port_list)

        return results

    def list_utils(self):

        utils = []

        for source_prefix, source in self.sources.items():
            for util_name in source.utils:
                if util_name in utils:
                    continue

                utils.append(util_name)

        return utils

    def port_images(self, port_name):
        for source_prefix, source in self.sources.items():
            if name_cleaner(port_name) in getattr(source, 'images', {}):
                return {
                    image_type: (source._images_dir / image_file)
                    for image_type, image_file in source.images[name_cleaner(port_name)].items()}

        return None

    def porters_list(self):
        return list(self.porters().keys())

    def port_info(self, port_name, installed=False):
        result = None

        port_key = (name_cleaner(port_name), installed)
        if port_key in self.__PORT_INFO_CACHE:
            return self.__PORT_INFO_CACHE[port_key]

        if installed:
            if port_name in self.installed_ports:
                result = port_info_load(self.installed_ports[name_cleaner(port_name)])

            elif port_name in self.broken_ports:
                result = port_info_load(self.broken_ports[name_cleaner(port_name)])

        for source_prefix, source in self.sources.items():
            if source.clean_name(port_name) in source.ports:
                if result is not None:
                    port_info_merge(result, source.port_info(port_name))

                else:
                    result = port_info_load(source.port_info(port_name))

        if result is None:
            self.__PORT_INFO_CACHE[port_key] = result
            return None

        if not installed:
            if port_name in self.installed_ports:
                 port_info_merge(result, self.installed_ports[name_cleaner(port_name)])

            elif port_name in self.broken_ports:
                 port_info_merge(result, self.broken_ports[name_cleaner(port_name)])

        self.__PORT_INFO_CACHE[port_key] = result
        return result

    def port_download_size(self, port_name, check_runtime=True):
        for source_prefix, source in self.sources.items():
            clean_name = source.clean_name(port_name)
            if clean_name not in source.ports:
                if clean_name not in source.utils:
                    continue

            return source.port_download_size(port_name, check_runtime)

        return 0

    def port_download_url(self, port_name):
        for source_prefix, source in self.sources.items():
            clean_name = source.clean_name(port_name)
            if clean_name not in source.ports:
                if clean_name not in source.utils:
                    continue

            return source.port_download_url(port_name)

        return None

    def list_runtimes(self):
        result = []
        changed = False
        for runtime_name, runtime_data in self.runtimes_info.items():
            runtime_file = self.libs_dir / runtime_name

            # FIX IT
            if 'remote' in runtime_data and 'name' in runtime_data['remote']:
                temp = runtime_data['remote']
                runtime_data['remote'] = {}
                runtime_data['remote']['aarch64'] = temp
                changed = True

            if 'local' not in runtime_data:
                changed = True
                runtime_file = (self.libs_dir / runtime_name)
                runtime_md5 = None
                runtime_md5_file = (self.libs_dir / (runtime_name + '.md5'))
                runtime_local_arch = None

                if runtime_file.is_file():
                    runtime_status = 'Unverified'

                    runtime_md5_check = hash_file(runtime_file)

                    if runtime_md5_file.is_file():
                        runtime_md5 = runtime_md5_file.read_text().strip().split(' ')[0]
                        if runtime_md5_check == runtime_md5:
                            runtime_status = 'Verified'
                            runtime_local_arch = 'aarch64'

                    else:
                        for runtime_arch in runtime_data['remote']:
                            runtime_md5 = runtime_data['remote'][runtime_arch]['md5']

                            if runtime_md5_check == runtime_md5:

                                runtime_status = 'Verified'
                                runtime_local_arch = runtime_arch
                                break

                        else:
                            runtime_status = 'Broken'

                else:
                    runtime_status = 'Not Installed'

                runtime_data['local'] = {
                    'status': runtime_status,
                    'md5': runtime_md5,
                    'arch': runtime_local_arch,
                    }

            else:
                if not runtime_file.is_file():
                    changed = True
                    runtime_data['local'] = {
                        'status': 'Not Installed',
                        'md5': None,
                        'arch': None,
                        }

            result.append((runtime_name, runtime_data))

        if changed:
            self.save_config()

        return result

    def set_gcd_mode(self, mode='standard'):
        self.platform.set_gcd_mode(mode)

    def get_gcd_mode(self):
        return self.platform.get_gcd_mode()

    def get_gcd_modes(self):
        return self.platform.get_gcd_modes()

    def _fix_permissions(self, path_check=None):
        if path_check is None:
            path_check = self.ports_dir

        path_fs = get_path_fs(path_check)
        logger.debug(f"path_fs={path_fs}")

        if path_fs not in ('ext4', 'ext3', 'overlay'):
            return

        try:
            logger.info(f"Fixing permissions for {path_check}.")
            subprocess.check_output(['chmod', '-R', '777', str(path_check)])

        except subprocess.CalledProcessError as err:
            logger.error(f"Failed to fix permissions: {err}")
            return

    def _install_theme(self, download_file):
        """
        Installs a theme file.
        """
        logger.info(f"Installing theme: {download_file.name}")

        if not self.themes_dir.is_dir():
            self.themes_dir.mkdir(0o755)

        theme_dir = self.themes_dir / download_file.name.rsplit('.', 2)[0]
        if not theme_dir.is_dir():
            theme_dir.mkdir(0o755)

        with zipfile.ZipFile(download_file, 'r') as zf:
            self.callback.message(_("Installing Theme {download_name}.").format(download_name=download_file.name))

            total_files = len(zf.infolist())
            for file_number, file_info in enumerate(zf.infolist()):
                if file_info.filename.endswith('/'):
                    continue

                self.callback.progress(_("Installing"), file_number+1, total_files, '%')
                self.callback.message(f"- {file_info.filename}")

                file_name = theme_dir / file_info.filename.rsplit('/', 1)[-1]
                with open(file_name, 'wb') as fh:
                    fh.write(zf.read(file_info.filename))

        with open(theme_dir / "theme.md5", 'w') as fh:
            fh.write(hash_file(download_file))

        self.callback.message_box(_("Theme {download_name!r} installed successfully.").format(download_name=download_file.name))

        return 0

    def _install_portmaster(self, download_file):
        """
        Installs a new version of PortMaster
        """
        logger.info("Installing PortMaster.zip")
        # if HM_TESTING:
        #     logger.error("Unable to install PortMaster.zip in testing environment.")
        #     return 255

        move_bash = self.platform.MOVE_PM_BASH

        try:
            gcd_mode = self.get_gcd_mode()

            # Hahaha... undo this mistake. :D
            if (self.cfg_dir / "PortMaster.sh").is_file():
                (self.cfg_dir / "PortMaster.sh").unlink()

            with zipfile.ZipFile(download_file, 'r') as zf:
                self.callback.message(_("Installing {download_name}.").format(download_name="PortMaster"))

                total_files = len(zf.infolist())
                for file_number, file_info in enumerate(zf.infolist()):
                    if file_info.file_size == 0:
                        compress_saving = 100
                    else:
                        compress_saving = file_info.compress_size / file_info.file_size * 100

                    self.callback.progress(_("Installing"), file_number+1, total_files, '%')
                    self.callback.message(f"- {file_info.filename}")

                    dest_file = self.tools_dir / file_info.filename

                    # cprint(f"- <b>{file_info.filename!r}</b> <d>[{nice_size(file_info.file_size)} ({compress_saving:.0f}%)]</d>")
                    zf.extract(file_info, path=self.tools_dir)

                    if move_bash and dest_file.name.lower().endswith('.sh'):
                        move_bash_dir = self.platform.MOVE_PM_BASH_DIR
                        if move_bash_dir is None or not move_bash_dir.is_dir():
                            move_bash_dir = self.ports_dir

                        self.callback.message(f"- moving {dest_file} to {move_bash_dir / dest_file.name}")
                        shutil.move(dest_file, move_bash_dir / dest_file.name)

            self.set_gcd_mode(gcd_mode)

            self.platform.portmaster_install()

            self.callback.message_box(_("Port {download_name!r} installed successfully.").format(download_name="PortMaster"))

            self._fix_permissions(self.tools_dir)

        finally:
            ...

        return 0

    def _install_port(self, download_info):
        """
        Installs a port.

        We collect a list of top level scripts/directories, this is added to the port.json file.
        """

        undo_data = []
        is_successs = False

        port_nice_name = download_info.get('attr', {}).get('title', download_info['name'])
        port_info = {}
        logger.info(f"Installing {port_nice_name}")

        try:
            extra_info = {}
            port_info = check_port(download_info['name'], download_info['zip_file'], extra_info)

            # Extra fix
            port_info_file_old = None

            if extra_info['port_info_file'] != 'port.json':
                if 'alephone/' not in port_info['items'] and 'alephone' not in port_info['items']:
                    # FUCK THESE GAMES. :D
                    port_info_file_old = self.ports_dir / extra_info['port_info_file']
                    extra_info['port_info_file'] = extra_info['port_info_file'].rsplit('/', 1)[0] + '/port.json'

            port_info_file = self.ports_dir / extra_info['port_info_file']

            with zipfile.ZipFile(download_info['zip_file'], 'r') as zf:
                ## TODO: keep a list of installed files for uninstalling?
                # At this point the port will be installed
                # Extract all the files to the specified directory
                # zf.extractall(self.ports_dir)
                self.callback.message(_("Installing {download_name}.").format(download_name=port_nice_name))

                total_files = len(zf.infolist())
                for file_number, file_info in enumerate(zf.infolist()):
                    if file_info.file_size == 0:
                        compress_saving = 100
                    else:
                        compress_saving = file_info.compress_size / file_info.file_size * 100

                    self.callback.progress(_("Installing"), file_number+1, total_files, '%')
                    self.callback.message(f"- {file_info.filename}")

                    is_script = (
                        file_info.filename.endswith('.sh') and
                        file_info.filename.count('/') == 0)

                    dest_file = path = self._ports_dir_file(file_info.filename, is_script)
                    dest_dir = (is_script and self.scripts_dir or self.ports_dir)

                    if dest_file == port_info_file_old:
                        dest_file = port_info_file
                        if not dest_file.exists():
                            add_list_unique(undo_data, dest_file)

                        continue

                    if not file_info.filename.endswith('/'):
                        if not dest_file.parent.is_dir():
                            add_list_unique(undo_data, dest_file.parent)

                    if not dest_file.exists():
                        add_list_unique(undo_data, dest_file)

                    # cprint(f"- <b>{file_info.filename!r}</b> <d>[{nice_size(file_info.file_size)} ({compress_saving:.0f}%)]</d>")
                    zf.extract(file_info, path=dest_dir)

            # print(f"Port Info: {port_info}")
            # print(f"Download Info: {download_info}")

            port_info_merge(port_info, download_info)

            ## These two are always overriden.
            port_info['name'] = name_cleaner(download_info['zip_file'].name)
            port_info['status'] = download_info['status'].copy()
            port_info['status']['status'] = 'Installed'

            # This doesnt need to be stored.
            if 'source' in port_info:
                del port_info['source']

            port_info['files'] = {
                'port.json': str(self._ports_dir_relative_to(port_info_file)),
                }

            # Add all the root dirs/scripts in the port
            for item in port_info['items']:
                if self._ports_dir_exists(item):
                    if item not in get_dict_list(port_info['files'], item):
                        add_dict_list_unique(port_info['files'], item, item)

                    if item.casefold().endswith('.sh'):
                        add_pm_signature(self.ports_dir / item, [port_info['name'], item])

            # And any optional ones.
            for item in get_dict_list(port_info, 'items_opt'):
                if self._ports_dir_exists(item):
                    if item not in get_dict_list(port_info['files'], item):
                        add_dict_list_unique(port_info['files'], item, item)

                    if item.casefold().endswith('.sh'):
                        add_pm_signature(self.ports_dir / item, [port_info['name'], item])
            # print(f"Merged Info: {port_info}")

            if not port_info_file.is_file():
                add_list_unique(undo_data, port_info_file)

            print(f"-> {port_info_file}")
            with open(port_info_file, 'w') as fh:
                json.dump(port_info, fh, indent=4)

            # Remove the zip file if it is in the self.temp_dir
            if str(download_info['zip_file']).startswith(str(self.temp_dir)):
                download_info['zip_file'].unlink()

            is_successs = True

            self.platform.port_install(port_info['name'], port_info, undo_data)

            if extra_info['gameinfo_xml'] is not None:
                if self.cfg_data.get('gamelist_update', True):
                    gameinfo_xml = self._ports_dir_file(extra_info['gameinfo_xml'])

                    if gameinfo_xml.is_file():
                        self.platform.gamelist_add(gameinfo_xml)

        except HarbourException as err:
            is_successs = False
            pass

        finally:
            if not is_successs:
                if len(undo_data) > 0:
                    logger.error("Installation failed, removing installed files.")
                    self.callback.message(_("Installation failed, removing files..."))

                    for undo_file in undo_data[::-1]:
                        logger.info(f"Removing {undo_file.relative_to(self.ports_dir)}")
                        self.callback.message(f"- {str(undo_file.relative_to(self.ports_dir))}")

                        if undo_file.is_file():
                            undo_file.unlink()

                        elif undo_file.is_dir():
                            shutil.rmtree(undo_file)

                self.callback.message_box(_("Port {download_name} installed failed.").format(download_name=port_nice_name))
                return 255

        self._fix_permissions()

        # logger.debug(port_info)
        if port_info['attr'].get('runtime', None) is not None:
            runtime_name = runtime_nicename(port_info['attr']['runtime'])

            self.callback.progress(None, None, None)
            result = self.check_runtime(port_info['attr']['runtime'], in_install=True)
            if result == 0:
                self.callback.message_box(_("Port {download_name!r} and {runtime_name!r} installed successfully.").format(
                    download_name=port_nice_name,
                    runtime_name=runtime_name))

            else:
                self.callback.message_box(_("Port {download_name!r} installed sucessfully, but {runtime_name!r} failed to install!!\n\nEither reinstall to try again, or check the wiki for help.").format(
                    download_name=port_nice_name,
                    runtime_name=runtime_name))

        else:
            self.callback.message_box(_("Port {download_name!r} installed successfully.").format(download_name=port_nice_name))

        return 0

    def check_runtime(self, runtime, port_name=None, in_install=False):
        if not isinstance(runtime, str):
            return 255

        if '/' in runtime:
            if not in_install:
                self.callback.message_box(_("Port {runtime} contains a bad runtime, game may not run correctly.").format(
                    runtime=runtime))

            logger.error(f"Bad runtime {runtime}")
            return 255

        if not self.libs_dir.is_dir():
            self.libs_dir.mkdir(0o777)

        if not runtime.endswith('.squashfs'):
            runtime += '.squashfs'

        if runtime not in self.runtimes_info:
            if not in_install:
                self.callback.message_box(_("Port {runtime} contains an unknown runtime, game may not run correctly.").format(
                    runtime=runtime))

            logger.error(f"Unknown runtime {runtime}")
            return 255

        # Fixes some stuff.
        self.list_runtimes()

        runtime_info = self.runtimes_info[runtime]
        runtime_name = runtime_info['name']
        runtime_file = (self.libs_dir / runtime)
        runtime_md5 = runtime_info.get('local', {}).get('md5', None)
        runtime_status = 'Not Installed'
        runtime_md5sum = None

        status_language = {
            'Not Installed':    _('Not Installed'),
            'Update Available': _('Update Available'),
            'Verified':         _('Verified'),
            'Unverified':       _('Unverified'),
            'Broken':           _('Broken'),
            }

        logger.info(f"Installing {runtime_name}")

        if self.config['offline']:
            cprint(f"Unable to download {runtime} when offline")
            self.callback.message_box(_("Unable do download a runtime when in offline mode."))
            return 0

        if runtime_file.is_file():
            runtime_status = 'Unverified'

            self.callback.message(_("Verifying runtime {runtime}").format(
                runtime=runtime_name))

            with open(runtime_file, 'rb') as fh:
                total_size = runtime_file.stat().st_size
                process_size = 0

                md5obj = hashlib.md5()

                self.callback.progress(_('Verifying'), process_size, total_size)

                for data in iter(lambda: fh.read(1024 * 1024 * 10), b''):
                    self.callback.progress(_('Verifying'), process_size, total_size)
                    process_size += len(data)
                    md5obj.update(data)

                self.callback.progress(None, None, None)

                runtime_md5sum = md5obj.hexdigest()

            if runtime_md5 is None:
                # runtime_md5.write_text(runtime_md5sum)
                runtime_status = 'Unverified'

            elif runtime_md5 == runtime_md5sum:
                runtime_status = 'Verified'

            else:
                runtime_status = 'Broken'

            runtime_info['local']['status'] = runtime_status

        else:
            runtime_status = 'Not Installed'

        if runtime not in self.runtimes_info:
            if not in_install:
                self.callback.message_box(_("Unable to find a download for {runtime}.").format(runtime=runtime))

            logger.error(f"Unable to find suitable source for {runtime}.")
            return 255

        if self.device['primary_arch'] not in self.runtimes_info[runtime]['remote']:
            self.callback.message_box(_("Unable to download {runtime} in {device_arch}.").format(
                runtime=runtime_name,
                device_arch=self.device['primary_arch']))

            logger.error(f"Unable to download {runtime} in {self.device['primary_arch']}.")
            return 255

        runtime_remote_info = self.runtimes_info[runtime]['remote'][self.device['primary_arch']]

        if runtime_remote_info['md5'] == runtime_md5sum:
            runtime_status = 'Verified'

        else:
            runtime_status = {
                'Verified': 'Update Available',
                'Unverified': 'Broken',
                'Not Installed': 'Not Installed',
                }[runtime_status]

        if runtime_status == 'Verified':
            if not in_install:
                self.callback.message_box(_("Verified {runtime} successfully.").format(
                    runtime=runtime_name))
            else:
                self.callback.message(_("Verified {runtime}.").format(
                    runtime=runtime_name))

            return 0

        elif runtime_status == 'Update Available':
            self.callback.message(_("Updating {runtime}.").format(
                    runtime=runtime_name))

        elif runtime_status == 'Broken':
            self.callback.message(_("Runtime {runtime} is broken, reinstalling.").format(
                    runtime=runtime_name))

        else:
            self.callback.message(_("Downloading runtime {runtime}.").format(
                runtime=runtime_name))

        download_successfull = False
        try:
            with self.callback.enable_cancellable(True):
                md5_result = [None]
                runtime_url = runtime_remote_info['url']
                runtime_md5 = runtime_remote_info['md5']

                runtime_file = download(runtime_file, runtime_url, md5_source=runtime_md5, callback=self.callback)

                self.runtimes_info[runtime]['local'] = {
                    "arch": self.device['primary_arch'],
                    "md5": runtime_md5,
                    "status": "Verified"
                    }

                download_successfull = True

                self.platform.runtime_install(runtime, [runtime_file])

                self.save_config()

            if self.callback.was_cancelled or not download_successfull:
                if runtime_file.is_file():
                    runtime_file.unlink()

                if not in_install:
                    self.callback.message_box(_("Unable to download {runtime}, game may not run correctly.").format(runtime=runtime))

                return 255

        except Exception as err:
            ## We need to catch any errors and delete the file if it fails,
            ## here we are not using the temp file auto deletion.
            logger.error(err)

            if not in_install:
                self.callback.message_box(_("Unable to download {runtime}, game may not run correctly.").format(runtime=runtime))

            return 255

        finally:
            if not download_successfull and runtime_file.is_file():
                runtime_file.unlink()

        if not in_install:
            self.callback.message_box(_("Successfully downloaded {runtime}.").format(runtime=runtime))

        return 0

    def install_port(self, port_name, md5_source=None):
        # Special HTTP download code.
        if port_name.startswith('http'):
            if self.config['offline']:
                cprint(f"Unable to download {port_name} when offline")
                self.callback.message_box(_("Unable do download a port when in offline mode."))
                return 255

            download_info = raw_download(self.temp_dir, port_name, callback=self.callback, md5_source=md5_source)

            if download_info is None:
                return 255

            with self.callback.enable_cancellable(False):
                if name_cleaner(download_info['name']).endswith('.theme.zip'):
                    return self._install_theme(download_info['zip_file'])

                elif name_cleaner(download_info['name']) == 'portmaster.zip':
                    return self._install_portmaster(download_info['zip_file'])

                else:
                    return self._install_port(download_info)

        # Special case for a local file.
        if port_name.startswith('./') or port_name.startswith('../') or port_name.startswith('/'):
            port_file = Path(port_name)
            if not port_file.is_file():
                logger.error(f"Unable to find local file {port_name} for installation.")
                return 255

            md5_result = hash_file(port_file)
            port_info = port_info_load({})

            port_info['name'] = name_cleaner(port_file.name)
            port_info['zip_file'] = port_file
            port_info['status'] = {
                'source': 'file',
                'md5': md5_result,
                'status': 'downloaded',
                }

            with self.callback.enable_cancellable(False):
                if name_cleaner(port_info['name']).endswith('.theme.zip'):
                    return self._install_theme(port_info['zip_file'])

                elif name_cleaner(port_info['name']) == 'portmaster.zip':
                    return self._install_portmaster(port_info['zip_file'])

                return self._install_port(port_info)

        if '/' in port_name:
            repo, port_name = port_name.split('/', 1)
        else:
            repo = '*'

        # Otherwise:
        for source_prefix, source in self.sources.items():
            if not fnmatch.fnmatch(source_prefix, repo):
                continue

            check_okay = False
            # is it a valid port?
            if not check_okay and (
                    source.clean_name(port_name) in source.ports):
                check_okay = True

            # is it PortMaster.zip from the Official PortMaster repo?
            if not check_okay and (
                    source.name in ("PortMaster", ) and
                    source.clean_name(port_name) == 'portmaster.zip' and
                    source.clean_name(port_name) in source._data):
                check_okay = True

            # is it a theme?
            if not check_okay and (
                    source.clean_name(port_name).endswith('.theme.zip') and
                    source.clean_name(port_name) in source._data):
                check_okay = True

            if not check_okay:
                continue

            if self.config['offline']:
                cprint(f"Unable to download {port_name} when offline")
                self.callback.message_box(_("Unable do download a port when in offline mode."))
                return 255

            download_info = source.download(source.clean_name(port_name))

            if download_info is None:
                return 255

            # print(f"Download Info: {download_info.to_dict()}")
            with self.callback.enable_cancellable(False):
                if source.clean_name(port_name).endswith('.theme.zip'):
                    return self._install_theme(download_info)

                elif source.clean_name(port_name) == 'portmaster.zip':
                    return self._install_portmaster(download_info)

                return self._install_port(download_info)

        self.callback.message_box(_("Unable to find a source for {port_name}").format(port_name=port_name))

        cprint(f"Unable to find a source for <b>{port_name}</b>")
        return 255

    def uninstall_port(self, port_name):
        port_info = self.installed_ports.get(port_name.casefold(), None)
        port_loc = self.installed_ports

        if port_info is None:
            port_info = self.broken_ports.get(port_name.casefold(), None)
            port_loc = self.broken_ports

            if port_info is None:
                self.callback.message_box(_("Unknown port {port_name}").format(port_name=port_name))
                logger.error(f"Unknown port {port_name}")
                return 255

        port_info_name = port_info.get("attr", {}).get("title", port_name)

        all_items = {}

        # We need to build up a list of all associated files
        # so we only delete the ones that will no longer be associaed with any ports.
        for item_name, item_info in self.installed_ports.items():
            # Add all the root dirs/scripts in the port
            for item in item_info['files']:
                if item in ('port.json', ):
                    continue

                for name in get_dict_list(item_info['files'], item):
                    add_dict_list_unique(all_items, name, item_name)

        for item_name, item_info in self.broken_ports.items():
            # Add all the root dirs/scripts in the port
            for item in item_info['files']:
                if item in ('port.json', ):
                    continue

                for name in get_dict_list(item_info['files'], item):
                    add_dict_list_unique(all_items, name, item_name)

        # from pprint import pprint
        # pprint(all_items)

        # cprint(f"{all_items}")
        cprint(f"Uninstalling <b>{port_info_name}</b>")
        self.callback.message(_("Removing {port_name}").format(port_name=port_info_name))

        all_port_items = []
        for port_file in port_info['files']:
            all_port_items.extend(get_dict_list(port_info['files'], port_file))

        ports_dir = self.ports_dir

        uninstall_items = [
            item
            for item in all_port_items
            # Only delete files/scripts with only 1 owner.
            if len(get_dict_list(all_items, item)) == 1]

        self.platform.port_uninstall(port_name, port_info, all_port_items)

        for item in uninstall_items:
            item_path = self.ports_dir / item

            if item_path.exists():
                cprint(f"- removing {item}")
                self.callback.message(f"- {item}")

                if item_path.is_dir():
                    shutil.rmtree(item_path)

                elif item_path.is_file():
                    item_path.unlink()

            item_path = self.scripts_dir / item

            if item_path.exists():
                cprint(f"- removing {item}")
                self.callback.message(f"- {item}")

                if item_path.is_dir():
                    shutil.rmtree(item_path)

                elif item_path.is_file():
                    item_path.unlink()

        self.callback.message_box(_("Successfully uninstalled {port_name}").format(port_name=port_info_name))

        del port_loc[port_name.casefold()]
        return 0

    def portmd(self, port_info):
        def nice_value(value):
            if value is None:
                return ""
            if value == "None":
                return ""
            return value

        output = []

        if 'opengl' in port_info["attr"]["reqs"]:
            output.append(f'<r>Title_F</r>="<y>{port_info["attr"]["title"].replace(" ", "_")} .</y>"')
        elif 'power' in port_info["attr"]['reqs']:
            output.append(f'<r>Title_P</r>="<y>{port_info["attr"]["title"].replace(" ", "_")} .</y>"')
        else:
            output.append(f'<r>Title</r>="<y>{port_info["attr"]["title"].replace(" ", "_")} .</y>"')

        output.append(f'<r>Desc</r>="<y>{nice_value(port_info["attr"]["desc"])}</y>"')
        output.append(f'<r>porter</r>="<y>{oc_join(port_info["attr"]["porter"])}</y>"')
        output.append(f'<r>locat</r>="<y>{nice_value(port_info["name"])}</y>"')
        if port_info["attr"]['rtr']:
            output.append(f'<r>runtype</r>="<e>rtr</e>"')
        if port_info["attr"]['runtime'] == "mono-6.12.0.122-aarch64.squashfs":
            output.append(f'<r>mono</r>="<e>y</e>"')

        output.append(f'<r>genres</r>="<m>{",".join(port_info["attr"]["genres"])}</m>"')

        return ' '.join(output)

__all__ = (
    'HarbourMaster',
    )