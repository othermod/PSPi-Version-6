
# SPDX-License-Identifier: MIT

# System imports
import pathlib

# Included imports
import utility

from loguru import logger

# Module imports
from .config import *
from .util import *

################################################################################
## Port Information
PORT_INFO_ROOT_ATTRS = {
    'version': 4,
    'name': None,
    'items': None,
    'items_opt': None,
    'attr': {},
    }


PORT_INFO_ATTR_ATTRS = {
    'title': "",
    'desc': "",
    'inst': "",
    'genres': [],
    'porter': [],
    'image': {},
    'rtr': False,
    'exp': False,
    'runtime': [],
    'min_glibc': "",
    'reqs': [],
    'arch': [],
    }


PORT_INFO_OPTIONAL_ROOT_ATTRS = [
    'status',
    'files',
    'source',
    ]


def port_info_load(raw_info, source_name=None, do_default=False):
    if isinstance(raw_info, pathlib.PurePath):
        source_name = str(raw_info)

        with raw_info.open('r') as fh:
            info = json_safe_load(fh)
            if info is None or not isinstance(info, dict):
                if do_default:
                    info = {}
                else:
                    return None

    elif isinstance(raw_info, str):
        if raw_info.strip().startswith('{') and raw_info.strip().endswith('}'):
            if source_name is None:
                source_name = "<str>"

            info = json_safe_loads(info)
            if info is None or not isinstance(info, dict):
                if do_default:
                    info = {}
                else:
                    return None

        elif Path(raw_info).is_file():
            source_name = raw_info

            with open(raw_info, 'r') as fh:
                info = json_safe_load(fh)
                if info is None or not isinstance(info, dict):
                    if do_default:
                        info = {}
                    else:
                        return None

        else:
            if source_name is None:
                source_name = "<str>"

            logger.error(f'Unable to load port_info from {source_name!r}: {raw_info!r}')
            if do_default:
                info = {}
            else:
                return None

    elif isinstance(raw_info, dict):
        if source_name is None:
            source_name = "<dict>"

        info = raw_info

    else:
        logger.error(f'Unable to load port_info from {source_name!r}: {raw_info!r}')
        if do_default:
            info = {}
        else:
            return None

    # This is a bizzare one, it turns out some versions are strings?!
    if isinstance(info.get('version', None), str):
        info['version'] = int(info['version'])

    if 'version' in info and info['version'] > PORT_INFO_ROOT_ATTRS['version']:
        logger.error(f'Unable to load port_info with newer version from {source_name!r}: {info}')

        if do_default:
            info = {}
        else:
            return None

    if info.get('version', None) == 1:
        # Update older json version to the newer one.
        info = info.copy()
        if 'source' in info and isinstance(info['source'], str):
            info['name'] = info['source'].rsplit('/', 1)[-1]
            del info['source']

        info['version'] = 2

        if info.get('md5', None) is not None:
            info['status'] = {
                'source': "Unknown",
                'md5': info['md5'],
                'status': "Unknown",
                }
            del info['md5']

    if info.get('version', None) == 2:
        info['version'] = 3

    # WHOOPS! :O
    if info.get('attr', {}).get('runtime', None) == "blank":
        info['attr']['runtime'] = None

    if isinstance(info.get('attr', {}).get('porter'), str):
        info['attr']['porter'] = [info['attr']['porter']]

    if isinstance(info.get('attr', {}).get('reqs', None), dict):
        info['attr']['reqs'] = [
            key
            for key in info['attr']['reqs']]

    # Version 3 to 4
    if info.get('version', None) == 3:
        info['version'] = 4

        if info['attr']['runtime'] is None:
            info['attr']['runtime'] = []

        elif isinstance(info['attr']['runtime'], str):
            info['attr']['runtime'] = [ info['attr']['runtime'] ]

    # Catch errors because who fucking uses version numbers.
    if info.get('attr', {}).get('runtime', []) == None:
        info['attr']['runtime'] = []

    if isinstance(info.get('attr', {}).get('runtime', []), str):
        info['attr']['runtime'] = [ info['attr']['runtime'] ]

    # This strips out extra stuff
    port_info = {}

    for attr, attr_default in PORT_INFO_ROOT_ATTRS.items():
        if isinstance(attr_default, (dict, list)):
            attr_default = attr_default.copy()

        port_info[attr] = info.get(attr, attr_default)

    for attr, attr_default in PORT_INFO_ATTR_ATTRS.items():
        if isinstance(attr_default, (dict, list)):
            attr_default = attr_default.copy()

        port_info['attr'][attr] = info.get('attr', {}).get(attr, attr_default)

    for attr in PORT_INFO_OPTIONAL_ROOT_ATTRS:
        if attr in info:
            port_info[attr] = info[attr]

    if isinstance(port_info['items'], list):
        i = 0
        while i < len(port_info['items']):
            item = port_info['items'][i]
            if item.startswith('/'):
                logger.error(f"port_info['items'] contains bad name {item!r}")
                del port_info['items'][i]
                continue

            if item.startswith('../'):
                logger.error(f"port_info['items'] contains bad name {item!r}")
                del port_info['items'][i]
                continue

            if '/../' in item:
                logger.error(f"port_info['items'] contains bad name {item!r}")
                del port_info['items'][i]
                continue

            if item == "":
                logger.error(f"port_info['items'] contains bad name {item!r}")
                del port_info['items'][i]

            i += 1

    if isinstance(port_info['items_opt'], list):
        i = 0
        while i < len(port_info['items_opt']):
            item = port_info['items_opt'][i]
            if item.startswith('/'):
                logger.error(f"port_info['items_opt'] contains bad name {item}")
                del port_info['items_opt'][i]
                continue

            if item.startswith('../'):
                logger.error(f"port_info['items_opt'] contains bad name {item}")
                del port_info['items_opt'][i]
                continue

            if '/../' in item:
                logger.error(f"port_info['items_opt'] contains bad name {item}")
                del port_info['items_opt'][i]
                continue

            if item == "":
                logger.error(f"port_info['items'] contains bad name {item!r}")
                del port_info['items_opt'][i]

            i += 1

        if port_info['items_opt'] == []:
            port_info['items_opt'] = None

    if isinstance(port_info['attr'].get('genres', None), list):
        genres = port_info['attr']['genres']
        port_info['attr']['genres'] = []

        for genre in genres:
            if genre.casefold() in HM_GENRES:
                port_info['attr']['genres'].append(genre.casefold())

    return port_info


@timeit
def port_info_merge(port_info, other):
    if isinstance(other, (str, pathlib.PurePath)):
        other_info = port_info_load(other)
    elif isinstance(other, dict):
        other_info = other
    else:
        logger.error(f"Unable to merge {other!r}")
        return None

    for attr, attr_default in PORT_INFO_ROOT_ATTRS.items():
        if attr == 'attr':
            continue

        value_a = port_info[attr]
        value_b = other_info[attr]

        if value_a is None or value_a == "" or value_a == []:
            port_info[attr] = value_b
            continue

        if value_b in (True, False) and value_a in (True, False, None):
            port_info[attr] = value_b
            continue

        if isinstance(value_b, str) and value_a in ("", None):
            port_info[attr] = value_b
            continue

        if isinstance(value_b, list) and value_a in ([], None):
            port_info[attr] = value_b[:]
            continue

        if isinstance(value_b, dict) and value_a in ({}, None):
            port_info[attr] = value_b.copy()
            continue

    for attr in PORT_INFO_OPTIONAL_ROOT_ATTRS:
        if attr not in other_info:
            continue

        value_a = port_info.get(attr)
        value_b = other_info[attr]

        if isinstance(value_b, str) and value_a in ("", None):
            port_info[attr] = value_b
            continue

        if isinstance(value_b, list) and value_a in ([], None):
            port_info[attr] = value_b[:]
            continue

        if isinstance(value_b, dict) and value_a in ({}, None):
            port_info[attr] = value_b.copy()
            continue

    for key_b, value_b in other_info['attr'].items():
        if key_b not in port_info['attr']:
            continue

        if value_b in (True, False) and port_info['attr'][key_b] in (True, False, None):
            port_info['attr'][key_b] = value_b
            continue

        if isinstance(value_b, str) and port_info['attr'][key_b] in ("", None):
            port_info['attr'][key_b] = value_b
            continue

        if isinstance(value_b, list) and port_info['attr'][key_b] in ([], None):
            port_info['attr'][key_b] = value_b[:]
            continue

        if isinstance(value_b, dict) and port_info['attr'][key_b] in ({}, None):
            port_info['attr'][key_b] = value_b.copy()
            continue

    return port_info


__all__ = (
    'port_info_load',
    'port_info_merge',
    )
