
import contextlib
import datetime
import functools
import hashlib
import json
import platform
import shutil
import re
import subprocess
import sys
import tempfile
import time

from gettext import gettext as _
from pathlib import Path

import loguru
import pathlib
import requests
import utility

from loguru import logger
from utility import cprint, cstrip

from .config import *


################################################################################
## Exceptions
class HarbourException(Exception):
    ...


################################################################################
## Utils
def json_safe_loads(*args):
    try:
        return json.loads(*args)
    except json.JSONDecodeError as err:
        logger.error(f"Unable to load json_data {err.doc}:{err.pos}:{err.lineno}:{err.colno}")
        return None


def json_safe_load(*args):
    try:
        return json.load(*args)
    except json.JSONDecodeError as err:
        logger.error(f"Unable to load json_data {err.doc}:{err.pos}:{err.lineno}:{err.colno}")
        return None


def fetch(url):
    r = requests.get(url, timeout=20)
    if r.status_code != 200:
        logger.error(f"Failed to download {url!r}: {r.status_code}")
        return None

    return r


def fetch_data(url):
    r = fetch(url)
    if r is None:
        return None

    return r.content


def fetch_json(url):
    r = fetch(url)
    if r is None:
        return None

    return r.json()


def fetch_text(url):
    r = fetch(url)
    if r is None:
        return None

    # fixes a weird bug
    r.encoding = 'utf-8'

    return r.text


def nice_size(size):
    """
    Make nicer data sizes.
    """

    suffixes = ('B', 'KB', 'MB', 'GB', 'TB')
    for suffix in suffixes:
        if size < 768:
            break

        size /= 1024

    if suffix == 'B':
        return f"{size:.0f} {suffix}"

    return f"{size:.02f} {suffix}"


def oc_join(strings):
    """
    Oxford comma join
    """
    if len(strings) == 0:
        return ""

    elif len(strings) == 1:
        return strings[0]

    elif len(strings) == 2:
        return f"{strings[0]} and {strings[1]}"

    else:
        oxford_comma_list = ", ".join(strings[:-1]) + ", and " + strings[-1]
        return oxford_comma_list


@functools.lru_cache(maxsize=512)
def version_parse(version):
    result = []

    i = 0
    while i < len(version):
        number = ""
        suffix = ""
        while i < len(version):
            if not version[i].isnumeric():
                break

            number += version[i]
            i += 1

        if number != "":
            result.append(int(number))

        while i < len(version):
            if version[i].isnumeric():
                break

            c = version[i]
            i += 1

            if c not in '()[],_.-':
                suffix += c

        if suffix != "":
            result.append(suffix)

    return tuple(result)


@functools.lru_cache(maxsize=512)
def name_cleaner(text):
    temp = re.sub(r'[^a-zA-Z0-9 _\-\.]+', '', text.strip().lower())
    return re.sub(r'[ \.]+', '.', temp)


def load_pm_signature(file_name):
    ## Adds the portmaster signature to a bash script.
    if isinstance(file_name, str):
        file_name = pathlib.Path(file_name)

    elif not isinstance(file_name, pathlib.PurePath):
        raise ValueError(file_name)

    if not file_name.is_file():
        return None

    if file_name.suffix.lower() not in ('.sh', ):
        return None

    try:
        with open(file_name, 'rb') as fh:
            data = fh.read(1024)

            for line in data.decode('utf-8').split('\n'):
                if not line.strip().startswith('#'):
                    continue

                if 'PORTMASTER:' not in line:
                    continue

                return [
                    item.strip()
                    for item in line.split(':', 1)[1].strip().split(',', 1)]

    except UnicodeDecodeError as err:
        logger.error(f"Error loading {file_name}: {err}")
        return None

    except Exception as err:
        # Bad but we will live.
        logger.error(f"Error loading {file_name}: {err}")
        return None

    return None

def add_pm_signature(file_name, info):
    ## Adds the portmaster signature to a bash script.

    if isinstance(file_name, str):
        file_name = pathlib.Path(file_name)

    elif not isinstance(file_name, pathlib.PurePath):
        raise ValueError(file_name)

    if not file_name.is_file():
        return

    if file_name.suffix.lower() not in ('.sh', ):
        return

    # See if it has some info already.
    old_info = load_pm_signature(file_name)

    try:
        if old_info is not None:
            # Info is the same, ignore it
            if old_info == info:
                return

            file_data = [
                line
                for line in file_name.read_text().split('\n')
                if not (line.strip().startswith('#') and 'PORTMASTER:' in line)]

        else:
            file_data = [
                line
                for line in file_name.read_text().split('\n')]

    except UnicodeDecodeError as err:
        logger.error(f"Error loading {file_name}: {err}")
        return

    except Exception as err:
        # Bad but we will live.
        logger.error(f"Error loading {file_name}: {err}")
        return

    file_data.insert(1, f"# PORTMASTER: {', '.join(info)}")

    with file_name.open('w') as fh:
        fh.write("\n".join(file_data))

def remove_pm_signature(file_name):
    ## Removes the portmaster signature to a bash script.

    if isinstance(file_name, str):
        file_name = pathlib.Path(file_name)

    elif not isinstance(file_name, pathlib.PurePath):
        raise ValueError(file_name)

    if not file_name.is_file():
        return

    if file_name.suffix.casefold() not in ('.sh', ):
        return

    # See if it has some info already.
    old_info = load_pm_signature(file_name)
    if old_info is None:
        return

    file_data = [
        line
        for line in file_name.read_text().split('\n')
        if not (line.strip().startswith('#') and 'PORTMASTER:' in line)]

    with file_name.open('w') as fh:
        fh.write("\n".join(file_data))


def hash_file(file_name):
    if isinstance(file_name, str):
        file_name = pathlib.Path(file_name)
    elif not isinstance(file_name, pathlib.PurePath):
        raise ValueError(file_name)

    if not file_name.is_file():
        return None

    md5 = hashlib.md5()
    with file_name.open('rb') as fh:
        for data in iter(lambda: fh.read(1024 * 1024 * 10), b''):
            md5.update(data)

    return md5.hexdigest()


def runtime_nicename(runtime):
    if runtime.startswith("frt"):
        return ("Godot/FRT {version}").format(version=runtime.split('_', 1)[1].rsplit('.', 1)[0])

    if runtime.startswith("solarus"):
        return ("Solarus {version}").format(version=runtime.split('-', 1)[1].rsplit('.', 1)[0])

    if runtime.startswith("mono"):
        return ("Mono {version}").format(version=runtime.split('-', 1)[1].rsplit('-', 1)[0])

    if "jdk" in runtime and runtime.startswith("zulu11"):
        return ("JDK {version}").format(version=runtime.split('-')[2][3:])

    return runtime


def download(file_name, file_url, md5_source=None, md5_result=None, callback=None, no_check=False):
    """
    Download a file from file_url into file_name, checks the md5sum of the file against md5_source if given.

    returns file_name if successful, otherwise None.
    """
    if md5_result is None:
        md5_result = [None]

    try:
        r = requests.get(file_url, stream=True, timeout=(30, 10))

        if r.status_code != 200:
            if callback is not None:
                callback.message_box(_("Unable to download file. [{status_code}]").format(status_code=r.status_code))

            logger.error(f"Unable to download file: {file_url!r} [{r.status_code}]")
            return None

        total_length = r.headers.get('content-length')
        if total_length is None:
            total_length = None
            total_length_mb = "???? MB"
        else:
            total_length = int(total_length)
            total_length_mb = nice_size(total_length)

        md5 = hashlib.md5()

        if callback is not None:
            callback.message(_("Downloading {file_url} - ({total_length_mb})").format(file_url=file_url, total_length_mb=total_length_mb))
        else:
            cprint(f"Downloading <b>{file_url!r}</b> - <b>{total_length_mb}</b>")

        length = 0
        with file_name.open('wb') as fh:
            for data in r.iter_content(chunk_size=104096, decode_unicode=False):
                md5.update(data)
                fh.write(data)
                length += len(data)

                if callback is not None:
                    callback.progress(_("Downloading file."), length, total_length, 'data')
                else:
                    if total_length is None:
                        sys.stdout.write(f"\r[{'?' * 40}] - {nice_size(length)} / {total_length_mb} ")
                    else:
                        amount = int(length / total_length * 40)
                        sys.stdout.write(f"\r[{'|' * amount}{' ' * (40 - amount)}] - {nice_size(length)} / {total_length_mb} ")

                    sys.stdout.flush()

            if callback is None:
                cprint("\n")

            if callback is not None:
                callback.progress(_("Downloading file."), length, total_length, 'data')

    except requests.RequestException as err:
        if file_name.is_file():
            file_name.unlink()

        logger.error(f"Requests error: {err}")

        if callback is not None:
            callback.message_box(_("Download failed: {err}").format(err=str(err)))

        return None

    md5_file = md5.hexdigest()
    if not no_check:
        if md5_source is not None:
            if md5_file != md5_source:
                file_name.unlink()
                logger.error(f"File doesn't match the md5 file: {md5_file} != {md5_source}")

                if callback is not None:
                    callback.message_box(_("Download validation failed."))

                return None
            else:

                if callback is not None:
                    callback.message(_("Passed file validation."))
                else:
                    cprint(f"<b,g,>Passed md5 check.</b,g,>")
        else:
            if callback is not None:
                callback.message(_("Unable to validate download."))

            logger.warning(f"No md5 to check against: {md5_file}")

    if callback is not None:
        callback.progress(None, None, None)

    md5_result[0] = md5_file

    return file_name


def datetime_compare(time_a, time_b=None):
    if isinstance(time_a, str):
        time_a = datetime.datetime.fromisoformat(time_a)

    if time_b is None:
        time_b = datetime.datetime.now()
    elif isinstance(time_b, str):
        time_b = datetime.datetime.fromisoformat(time_b)

    return (time_b - time_a).total_seconds()


def add_list_unique(base_list, value):
    if value not in base_list:
        base_list.append(value)


def add_dict_list_unique(base_dict, key, value):
    if key not in base_dict:
        base_dict[key] = value
        return

    if isinstance(base_dict[key], str):
        if base_dict[key] == value:
            return

        base_dict[key] = [base_dict[key]]

    if value not in base_dict[key]:
        base_dict[key].append(value)


def get_dict_list(base_dict, key):
    if key not in base_dict:
        return []

    result = base_dict[key]
    if isinstance(result, str):
        return [result]

    if result is None:
        ## CEBION STRIKES AGAIN
        return []

    return result

def remove_dict_list(base_dict, key, value):
    if key not in base_dict:
        return

    result = base_dict[key]
    if isinstance(result, str):
        if value == result:
            del base_dict[key]

        return

    if value in result:
        result.remove(value)

        if len(result) == 0:
            del base_dict[key]

        elif len(result) == 1:
            base_dict[key] = result[0]

def get_path_fs(path):
    """
    Get the fs type of the specified path.
    """

    if HM_TESTING:
        return None

    if isinstance(path, pathlib.PurePath):
        if not path.exists():
            return None
    elif isinstance(path, str):
        if not Path(path).exists():
            return None
    else:
        return None

    try:
        lines = subprocess.check_output(['df', '-PT', str(path)]).decode().split('\n')
    except subprocess.CalledProcessError as err:
        return None

    if len(lines) < 2:
        return None

    if lines[1].strip() == '':
        return None

    sections = re.split(r'\s+', lines[1])
    if len(sections) < 2:
        return None

    return sections[1]


def timeit(func):
    if not HM_PERFTEST:
        return func

    @functools.wraps(func)
    def timeit_wrapper(*args, **kwargs):
        start_time = time.perf_counter()
        result = func(*args, **kwargs)
        end_time = time.perf_counter()
        total_time = end_time - start_time
        logger.debug(f'TIME: {func.__name__}({args}, {kwargs}): Took {total_time:.4f} seconds')
        return result

    return timeit_wrapper


def port_sort_alphabetical(port_info):
    return port_info.get('attr', {}).get('title', port_info['name']).casefold()


def port_sort_date_added(port_info):
    return port_info.get('source', {}).get('date_added', '1970-01-01')


def port_sort_date_updated(port_info):
    return port_info.get('source', {}).get('date_updated', '1970-01-01')


PORT_SORT_FUNCS = {
    'alphabetical': port_sort_alphabetical,
    'recently_added':   port_sort_date_added,
    'recently_updated': port_sort_date_updated,
    }


for sort_by in HM_SORT_ORDER:
    if sort_by not in PORT_SORT_FUNCS:
        raise RuntimeError(f'{sort_by} missing.')


@contextlib.contextmanager
def make_temp_directory():
    temp_dir = tempfile.mkdtemp()
    try:
        yield Path(temp_dir)

    finally:
        shutil.rmtree(temp_dir)


def match_requirements(capabilities, requirements):
    """
    Matches hardware capabilities to port requirements.
    """
    if len(requirements) == 0:
        return True

    passed = True
    for requirement in requirements:
        match_not = True

        ## Fixes empty requirement bug
        if requirement == "":
            continue

        if requirement.startswith('!'):
            match_not = False
            requirement = requirement[1:]

        if '|' in requirement:
            passed = any(
                req in capabilities
                for req in requirement.split('|')) == match_not

        else:
            if requirement in capabilities:
                passed = match_not
            else:
                passed = not match_not

        if not passed:
            break

    return passed


class CancelEvent(HarbourException):
    pass


class Callback:
    """
    This is a simple class that is used by harbourmaster to cooperate with gui code.
    """
    def __init__(self):
        self.was_cancelled = False

    def progress(self, message, amount, total=None, fmt=None):
        pass

    def messages_begin(self):
        pass

    def messages_end(self):
        pass

    def message(self, message):
        pass

    def message_box(self, message):
        pass

    def do_cancel(self):
        pass

    @contextlib.contextmanager
    def enable_messages(self):
        try:
            self.was_cancelled = False
            yield

        finally:
            pass

    @contextlib.contextmanager
    def enable_cancellable(self, cancellable=False):
        try:
            yield

        finally:
            pass


__all__ = (
    'Callback',
    'CancelEvent',
    'HarbourException',
    'add_dict_list_unique',
    'add_list_unique',
    'add_pm_signature',
    'datetime_compare',
    'download',
    'fetch_data',
    'fetch_json',
    'fetch_text',
    'get_dict_list',
    'get_path_fs',
    'hash_file',
    'json_safe_load',
    'json_safe_loads',
    'load_pm_signature',
    'make_temp_directory',
    'match_requirements',
    'name_cleaner',
    'nice_size',
    'oc_join',
    'remove_dict_list',
    'remove_pm_signature',
    'runtime_nicename',
    'timeit',
    'version_parse',
    'PORT_SORT_FUNCS',
    )
