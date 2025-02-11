
# System imports
import datetime
import json
import re
import zipfile

from gettext import gettext as _
from pathlib import Path
from urllib.parse import urlparse, urlunparse

# Included imports

from loguru import logger
from utility import cprint, cstrip

# Module imports
from .config import *
from .info import *
from .util import *

################################################################################
## APIS
class BaseSource():
    VERSION = 0

    def __init__(self, hm, file_name, config):
        self.hm = hm
        self._file_name = file_name
        self._config = config
        self._prefix = config['prefix']
        self._did_update = False
        self._wants_update = None
        self._images_dir = self.hm.cfg_dir / f"images_{self._prefix}"
        self._images_md5_file = self._images_dir / "images.md5"
        self._images_json_file = self._images_dir / "images.json"
        self._images_md5 = None

        if not self._images_dir.is_dir():
            self._images_dir.mkdir(0o777)

        if self._images_md5_file.is_file():
            self._images_md5 = self._images_md5_file.read_text().strip()

        if config['version'] != self.VERSION:
            self._wants_update = _("Cache out of date.")
            if config['version'] < 4:
                self._images_md5 = None

        elif self._config['last_checked'] is None:
            self._wants_update = _("First check.")

        elif datetime_compare(self._config['last_checked']) > HM_UPDATE_FREQUENCY:
            self._wants_update = _("Auto Update.")

        if not self.hm.config['no-check'] and not self.hm.config['offline']:
            self.auto_update()
        else:
            self.load()

    @property
    def name(self):
        return self._config['name']

    def auto_update(self):
        if self._wants_update is not None:
            # cprint(f"<b>{self._config['name']}</b>: {self._wants_update}")
            if self.hm.callback is not None:
                self.hm.callback.message(f" - {self._config['name']}: {self._wants_update}")

            self.update()
            self._wants_update = None

        else:
            self.load()

    def load(self):
        raise NotImplementedError()

    def save(self):
        raise NotImplementedError()

    def update(self):
        raise NotImplementedError()

    def clean_name(self, text):
        return name_cleaner(text)

class GitHubRawReleaseV1(BaseSource):
    VERSION = 4

    def load(self):
        self._data = self._config.setdefault('data', {}).setdefault('data', {})
        self.ports = self._config.setdefault('data', {}).setdefault('ports', [])
        self.utils = self._config.setdefault('data', {}).setdefault('utils', [])
        self._load()
        self._load_images()

    def save(self):
        with self._file_name.open('w') as fh:
            json.dump(self._config, fh, indent=4)

    def _load_images(self):
        self.images = {}
        all_ports = set(self.ports)
        seen_ports = set()

        for file_name in self._images_dir.iterdir():
            if file_name.suffix.casefold() not in ('.jpg', '.png'):
                continue

            if file_name.name.count('.') < 2:
                continue

            port_name, image_type, image_suffix = file_name.name.casefold().rsplit('.', 2)
            port_name = self.clean_name(port_name + '.zip')

            if port_name not in all_ports:
                logger.warning(f"Port image {port_name} - {image_type} for unknown port.")
            elif image_type == 'screenshot':
                seen_ports.add(port_name)

            self.images.setdefault(self.clean_name(port_name), {})[image_type] = file_name.name

        for port_name in (all_ports - seen_ports):
            logger.warning(f"Port image {port_name}: missing.")

    def _load(self):
        """
        Overload to add additional loading.
        """
        ...

    def _update(self):
        """
        Overload to add additional updating.
        """
        ...

    def _clear(self):
        """
        Overload to add additional clearing.
        """
        ...

    def update(self):
        # cprint(f"<b>{self._config['name']}</b>: updating")
        if self.hm.callback is not None:
            self.hm.callback.message(" - {}".format(_("Updating")))

        # Scrap the rest
        self._clear()
        self._data = {}
        self.ports = []
        self.utils = []
        self.images = {}

        if self._did_update:
            # cprint(f"- <b>{self._config['name']}</b>: up to date already.")
            self.hm.callback.message(" - {}".format(_("Up to date already")))
            return

        # cprint(f"- <b>{self._config['name']}</b>: Fetching latest ports")
        if self.hm.callback is not None:
            self.hm.callback.message("  - {}".format(_("Fetching latest info")))

        data = fetch_json(self._config['url'])
        if data is None:
            return

        ## Load data from the assets.
        for asset in data['assets']:
            result = {
                'name': asset['name'],
                'size': asset['size'],
                'url': asset['browser_download_url'],
                }

            self._data[self.clean_name(asset['name'])] = result

            if asset['name'].lower().endswith('.squashfs'):
                self.utils.append(self.clean_name(asset['name']))

        self._update()

        self._load_images()

        self._config['version'] = self.VERSION

        self._config['data']['ports'] = self.ports
        self._config['data']['utils'] = self.utils
        self._config['data']['data']  = self._data

        self._config['last_checked'] = datetime.datetime.now().isoformat()

        self.save()
        self._did_update = True
        # cprint(f"- <b>{self._config['name']}:</b> Done.")
        self.hm.callback.message("  - {}".format(_("Done.")))

    def download(self, port_name, temp_dir=None, md5_result=None):
        if md5_result is None:
            md5_result = [None]

        if port_name not in self._data:
            logger.error(f"Unable to find port {port_name}")
            self.hm.callback.message_box(_("Unable to find {port_name}.").format(port_name=port_name))
            return None

        if temp_dir is None:
            temp_dir = self.hm.temp_dir

        if (port_name + '.md5') in self._data:
            md5_file = port_name + '.md5'
        elif (port_name + '.md5sum') in self._data:
            md5_file = port_name + '.md5sum'
        else:
            self.hm.callback.message_box(_("Unable to find verification info for {port_name}.").format(port_name=port_name))
            logger.error(f"Unable to find md5 for {port_name}")
            return None

        md5_source = fetch_text(self._data[md5_file]['url'])
        if md5_source is None:
            logger.error(f"Unable to download md5 file: {self._data[md5_file]['url']!r}")
            self.hm.callback.message_box(_("Unable to download verification info for {port_name}.").format(port_name=port_name))
            return None

        md5_source = md5_source.strip().split(' ', 1)[0]

        zip_file = download(temp_dir / port_name, self._data[port_name]['url'], md5_source, callback=self.hm.callback)

        if zip_file is not None:
            # cprint("<b,g,>Success!</b,g,>")

            self.hm.callback.message("  - {}".format(_("Success!")))

        md5_result[0] = md5_source

        return zip_file

    def port_info(self, port_name):
        port_name = self.clean_name(port_name)

        if port_name not in getattr(self, '_info', {}):
            return {}

        return self._info[port_name]

    def port_download_size(self, port_name, check_runtime=True):
        port_name = self.clean_name(port_name)

        if port_name not in getattr(self, '_data', {}):
            return 0

        size = self._data[port_name]['size']

        if check_runtime and port_name in getattr(self, '_info', {}):
            port_info = self._info[port_name]

            if port_info['attr'].get('runtime', None) is not None:
                runtime = port_info['attr']['runtime']

                runtime_file = (self.hm.libs_dir / runtime)
                if not runtime_file.exists():
                    size += self.hm.port_download_size(runtime)

        return size

    def port_download_url(self, port_name):
        port_name = self.clean_name(port_name)

        if port_name not in getattr(self, '_data', {}):
            return None

        return self._data[port_name]['url']


class PortMasterV1(GitHubRawReleaseV1):
    VERSION = 4

    def _load(self):
        self._info = self._config.setdefault('data', {}).setdefault('info', {})

    def _clear(self):
        self._info = {}

    def _update(self):

        # cprint(f"- <b>{self._config['name']}</b>: Fetching info")
        self.hm.callback.message("  - {}".format(_("Fetching info")))

        # portsmd_url = "https://raw.githubusercontent.com/kloptops/PortMaster/main/ports.md"
        portsmd_url = self._data['ports.md']['url']
        for line in fetch_text(portsmd_url).split('\n'):
            line = line.strip()
            if line == '':
                continue

            port_info = self._portsmd_to_portinfo(line)

            self._info[port_info['name']] = port_info

            self.ports.append(port_info['name'])

        self._config['data']['info']  = self._info

        ## Download latest images.zip if needed.
        ## Uncomment after images has been added to PortMaster.
        if 'images.zip' not in self._data:
            return
        images_url_md5 = self._data['images.zip.md5']['url']
        images_url_zip = self._data['images.zip']['url']
        # images_url_md5 = "https://raw.githubusercontent.com/kloptops/pugwash/main/pugwash/data/images.zip.md5"
        # images_url_zip = "https://raw.githubusercontent.com/kloptops/pugwash/main/pugwash/data/images.zip"

        images_md5 = fetch_text(images_url_md5).strip()
        if self._images_md5 is None or images_md5 != self._images_md5:
            logger.debug(f"images_md5={images_md5}, self.images_md5={self._images_md5}")
            images_zip = download(self.hm.temp_dir / "images.zip", images_url_zip, images_md5, callback=self.hm.callback)
            if images_zip is None:
                logger.debug(f"Unable to download {images_url_zip}")
                return

            images_to_delete = [
                file_name
                for file_name in self._images_dir.iterdir()
                if file_name.suffix in ('.png', '.jpg')]

            with zipfile.ZipFile(images_zip, 'r') as zf:
                for zip_name in zf.namelist():
                    if zip_name.casefold().rsplit('.')[-1] not in ('jpg', 'png'):
                        continue

                    file_name = self._images_dir / self.clean_name(zip_name.rsplit('/', 1)[-1])
                    if file_name not in images_to_delete:
                        logger.debug(f"adding {file_name}")

                    with open(file_name, 'wb') as fh:
                        fh.write(zf.read(zip_name))

                    if file_name in images_to_delete:
                        images_to_delete.remove(file_name)

            for image_to_delete in images_to_delete:
                logger.debug(f"removing {image_to_delete}")
                image_to_delete.unlink()

            self._images_md5_file.write_text(images_md5)
            self._images_md5 = images_md5

    def _portsmd_to_portinfo(self, text):
        # Super jank
        raw_info = {
            'title': '',
            'desc': '',
            'locat': '',
            'porter': '',
            'reqs': [],
            'rtr': False,
            'runtime': None,
            'genres': [],
            }

        for key, value in re.findall(r'(?:^|\s)(\w+)=\"(.+?)"(?=\s+\w+=|$)', text.strip()):
            key = key.casefold()
            if key == 'title_f':
                raw_info['reqs'].append('opengl')
                key = 'title'
            elif key == 'title_p':
                raw_info['reqs'].append('power')
                key = 'title'

            if key == 'title':
                value = value[:-2].replace('_', ' ')

            # Zips with spaces in their names get replaced with '.'
            if '%20' in value:
                value = value.replace('%20', '.')
                value = value.replace('..', '.')

            # Special keys
            if key == 'runtype':
                key, value = "rtr", True
            elif key == "mono":
                key, value = "runtime", "mono-6.12.0.122-aarch64.squashfs"
            elif key == "genres":
                value = value.split(',')

            raw_info[key] = value

        port_info = port_info_load({})

        port_info['name'] = self.clean_name(raw_info['locat'])

        ports_info = self.hm.ports_info()

        port_info['items'] = ports_info['ports'].get(port_info['name'], {'items': []})['items']
        port_info['attr']['title']   = raw_info['title']
        port_info['attr']['porter']  = ports_info['portsmd_fix'].get(raw_info['porter'].lower(), [raw_info['porter']])
        port_info['attr']['desc']    = raw_info['desc']
        port_info['attr']['rtr']     = raw_info['rtr']
        port_info['attr']['reqs']    = raw_info['reqs']
        port_info['attr']['runtime'] = raw_info['runtime']
        port_info['attr']['genres']  = []

        ## Fixes genres to a fixed list.
        for genre in raw_info['genres']:
            genre = genre.casefold().strip()
            if genre in HM_GENRES:
                port_info['attr']['genres'].append(genre)

        return port_info

    def download(self, port_name, temp_dir=None, md5_result=None):
        if md5_result is None:
            md5_result = [None]

        zip_file = super().download(port_name, temp_dir, md5_result)

        if zip_file is None:
            return None

        if port_name in self.utils:
            ## Utils
            return zip_file

        zip_info = port_info_load({})

        zip_info['name'] = port_name
        zip_info['status'] = {
            'source': self._config['name'],
            'md5':    md5_result[0],
            'status': 'downloaded',
            }
        zip_info['zip_file'] = zip_file

        port_info = self.port_info(port_name)
        port_info_merge(zip_info, port_info)

        return zip_info


class PortMasterV2(GitHubRawReleaseV1):
    VERSION = 4

    def _load(self):
        self._info = self._config.setdefault('data', {}).setdefault('info', {})

    def _clear(self):
        self._info = {}

    def _update(self):
        # cprint(f"- <b>{self._config['name']}</b>: Fetching info")
        self.hm.callback.message("  - {}".format(_("Fetching info")))

        portsjson_url = self._data['ports.json']['url']
        data = fetch_json(portsjson_url)

        for port_name in data['ports']:
            port_info = data['ports'][port_name]

            if 'md5' in port_info:
                port_info['source'] = {
                    "source": "PortMaster",
                    "date_added": port_info['date_added'],
                    "date_updated": port_info['date_updated'],
                    "url": port_info['download_url'],
                    "size": port_info['download_size'],
                    "md5": port_info['md5'],
                    }

                del port_info['date_added']
                del port_info['date_updated']
                del port_info['download_url']
                del port_info['download_size']
                del port_info['md5']

            self._info[self.clean_name(port_name)] = port_info
            self.ports.append(self.clean_name(port_name))
            self._data[self.clean_name(port_name)]['md5'] = port_info['source']['md5']

        for util_name in data['utils']:
            self._data[self.clean_name(util_name)]['md5'] = data['utils'][util_name]['md5']

        self._config['data']['info']  = self._info

        ## Download latest images.zip if needed.
        ## Uncomment after images has been added to PortMaster.
        if 'images.zip' not in self._data:
            return

        images_url_zip = self._data['images.zip']['url']

        if 'md5' in self._data['images.zip']:
            images_md5 = self._data['images.zip']['md5']

        else:
            images_url_md5 = self._data['images.zip.md5']['url']
            images_md5 = fetch_text(images_url_md5).strip().split(' ', 1)[0]

        if self._images_md5 is None or images_md5 != self._images_md5:
            logger.debug(f"images_md5={images_md5}, self.images_md5={self._images_md5}")
            images_zip = download(self.hm.temp_dir / "images.zip", images_url_zip, images_md5, callback=self.hm.callback)
            if images_zip is None:
                logger.debug(f"Unable to download {images_url_zip}")
                return

            images_to_delete = [
                file_name
                for file_name in self._images_dir.iterdir()
                if file_name.suffix in ('.png', '.jpg')]

            with zipfile.ZipFile(images_zip, 'r') as zf:
                for zip_name in zf.namelist():
                    if zip_name.casefold().rsplit('.')[-1] not in ('jpg', 'png'):
                        continue

                    file_name = self._images_dir / self.clean_name(zip_name.rsplit('/', 1)[-1])
                    if file_name not in images_to_delete:
                        logger.debug(f"adding {file_name}")

                    with open(file_name, 'wb') as fh:
                        fh.write(zf.read(zip_name))

                    if file_name in images_to_delete:
                        images_to_delete.remove(file_name)

            for image_to_delete in images_to_delete:
                logger.debug(f"removing {image_to_delete}")
                image_to_delete.unlink()

            self._images_md5_file.write_text(images_md5)
            self._images_md5 = images_md5

    def download(self, port_name, temp_dir=None, md5_result=None):
        if md5_result is None:
            md5_result = [None]

        if port_name not in self._data:
            logger.error(f"Unable to find port {port_name}")
            self.hm.callback.message_box(_("Unable to find {port_name}.").format(port_name=port_name))
            return None

        if temp_dir is None:
            temp_dir = self.hm.temp_dir

        md5_result[0] = self._data[port_name]['md5']
        zip_file = download(temp_dir / port_name, self._data[port_name]['url'], self._data[port_name]['md5'], callback=self.hm.callback)

        if zip_file is None:
            return None

        if port_name in self.utils:
            ## Utils
            return zip_file

        zip_info = port_info_load({})

        zip_info['name'] = port_name
        zip_info['status'] = {
            'source': self._config['name'],
            'md5':    md5_result[0],
            'status': 'downloaded',
            }
        zip_info['zip_file'] = zip_file

        port_info = self.port_info(port_name)
        port_info_merge(zip_info, port_info)

        return zip_info


class GitHubRepoV1(GitHubRawReleaseV1):
    VERSION = 2

    def _load(self):
        """
        Overload to add additional loading.
        """
        self._info = self._config.setdefault('data', {}).setdefault('info', {})

    def update(self):
        # cprint(f"<b>{self._config['name']}</b>: updating")
        if self._did_update:
            # cprint(f"- <b>{self._config['name']}</b>: up to date already.")
            return

        self._clear()
        self._data = {}
        self._info = {}
        self.ports = []
        self.utils = []

        user_name = self._config['config']['user_name']
        repo_name = self._config['config']['repo_name']
        branch_name = self._config['config']['branch_name']
        sub_folder = self._config['config']['sub_folder']

        git_url = f"https://api.github.com/repos/{user_name}/{repo_name}/git/trees/{branch_name}?recursive=true"

        # cprint(f"- <b>{self._config['name']}</b>: Fetching latest ports")
        self.hm.callback.message("  - {}".format(_("{source_name}: Fetching latest ports").format(source_name=self._config['name'])))

        git_info = fetch_json(git_url)
        if git_info is None:
            return None

        ports_json_file = None

        for item in git_info['tree']:
            path = item["path"]
            if not path.startswith(sub_folder):
                continue

            name = path.rsplit('/', 1)[1]

            if not (path.endswith('.zip') or
                    path.endswith('.md5') or
                    path.endswith('.squashfs') or
                    path.endswith('.md5sum') or
                    name == 'ports.json'):
                continue

            result = {
                'name': name,
                'size': item['size'],
                'url': f"https://github.com/{user_name}/{repo_name}/raw/{branch_name}/{path}",
                }

            name = self.clean_name(name)
            self._data[name] = result

            if name.endswith('.squashfs'):
                self.utils.append(self.clean_name(asset['name']))

            if name == 'ports.json':
                ports_json_file = name

        if ports_json_file is not None:
            # cprint(f"- <b>{self._config['name']}:</b> Fetching info.")
            self.hm.callback.message("  - {}".format(_("Fetching info.")))
            ports_json = fetch_json(self._data[ports_json_file]['url'])

            for port_info in ports_json['ports']:
                port_name = port_info['name']

                port_name = self.clean_name(port_name)

                # Clean it up.
                self._info[port_name] = port_info_load(port_info)

                self.ports.append(port_name)

        self._config['version'] = self.VERSION

        self._config['data']['ports'] = self.ports
        self._config['data']['utils'] = self.utils
        self._config['data']['data']  = self._data
        self._config['data']['info']  = self._info

        self._config['last_checked'] = datetime.datetime.now().isoformat()

        self.save()
        self._did_update = True
        # cprint(f"- <b>{self._config['name']}:</b> Done.")
        self.hm.callback.message(f"  - Done.")


    def download(self, port_name, temp_dir=None, md5_result=None):
        if md5_result is None:
            md5_result = [None]

        zip_file = super().download(port_name, temp_dir, md5_result)

        if zip_file is None:
            return None

        if port_name in self.utils:
            ## Utils
            return zip_file

        zip_info = port_info_load({})

        zip_info['name'] = name_cleaner(port_name)
        zip_info['status'] = {
            'source': self._config['name'],
            'md5':    md5_result[0],
            'status': 'downloaded',
            }
        zip_info['zip_file'] = zip_file

        port_info = self.port_info(port_name)
        port_info_merge(zip_info, port_info)

        return zip_info

## The plan is to deprecate the above.
class PortMasterV3(BaseSource):
    VERSION = 2

    def load(self):
        self._data = self._config.setdefault('data', {}).setdefault('data', {})
        self.ports = self._config.setdefault('data', {}).setdefault('ports', [])
        self.utils = self._config.setdefault('data', {}).setdefault('utils', [])
        self._info = self._config.setdefault('data', {}).setdefault('info', {})
        self._load_images()

    def save(self):
        with self._file_name.open('w') as fh:
            json.dump(self._config, fh, indent=4)

    def _load_images(self):
        self.images = {}
        all_ports = set(self.ports)
        seen_ports = set()

        for file_name in self._images_dir.iterdir():
            if file_name.suffix.casefold() not in ('.jpg', '.png'):
                continue

            if file_name.name.count('.') < 2:
                continue

            port_name, image_type, image_suffix = file_name.name.casefold().rsplit('.', 2)
            port_name = self.clean_name(port_name + '.zip')

            if port_name not in all_ports:
                logger.warning(f"Port image {port_name} - {image_type} for unknown port.")
            elif image_type == 'screenshot':
                seen_ports.add(port_name)

            self.images.setdefault(self.clean_name(port_name), {})[image_type] = file_name.name

        for port_name in (all_ports - seen_ports):
            logger.warning(f"Port image {port_name}: missing.")

    def _update2(self):
        ## The new images.xxx.zip system.
        img_id = 0

        images_data = None

        if self._images_json_file.is_file():
            with open(self._images_json_file, 'r') as fh:
                images_data = json_safe_load(fh)

        if images_data is None:
            images_data = {}

        # Find all the current images.
        images_to_delete = [
            file_name
            for file_name in self._images_dir.iterdir()
            if file_name.suffix in ('.png', '.jpg')]

        for img_id in range(1000):
            zip_xxx_name = f'images.{img_id:03d}.zip'

            if zip_xxx_name not in self._data:
                break

            images_zip_url = self._data[zip_xxx_name]['url']
            images_zip_md5 = self._data[zip_xxx_name]['md5']

            # Has this zip been updated?
            images_local_md5 = images_data.get(zip_xxx_name, {}).get('md5', None)
            if images_local_md5 == images_zip_md5:
                # This zip file hasn't been updated, mark all images from this zip as okay.
                for image_name in images_data[zip_xxx_name]['images']:
                    file_name = (self._images_dir / image_name)

                    images_to_delete.remove(file_name)

                continue

            logger.debug(f"images_zip_md5={images_zip_md5} != images_local_md5={images_local_md5}")

            # fetch the new archive
            images_zip = download(self.hm.temp_dir / zip_xxx_name, images_zip_url, images_zip_md5, callback=self.hm.callback)
            if images_zip is None:
                logger.debug(f"Unable to download {images_zip_url}")
                return

            images_data[zip_xxx_name] = {}
            images_data[zip_xxx_name]['md5'] = images_zip_md5
            images_data[zip_xxx_name]['images'] = []

            # unzip the files, keep only png & jpg files
            with zipfile.ZipFile(images_zip, 'r') as zf:
                for zip_name in zf.namelist():
                    if zip_name.casefold().rsplit('.')[-1] not in ('jpg', 'png'):
                        continue

                    clean_name = self.clean_name(zip_name.rsplit('/', 1)[-1])

                    # Keep track of the files in this zip
                    images_data[zip_xxx_name]['images'].append(clean_name)

                    file_name = self._images_dir / clean_name
                    if file_name not in images_to_delete:
                        logger.debug(f"adding {file_name}")

                    with open(file_name, 'wb') as fh:
                        fh.write(zf.read(zip_name))

                    # Mark the files for keeping.
                    if file_name in images_to_delete:
                        images_to_delete.remove(file_name)

            # delete the sucker.
            images_zip.unlink()

        # delete any images not listed in any zip file.
        for image_to_delete in images_to_delete:
            logger.debug(f"removing {image_to_delete}")
            image_to_delete.unlink()

        with open(self._images_json_file, 'w') as fh:
            json.dump(images_data, fh, indent=4, sort_keys=True)

    def _update(self):
        # cprint(f"- <b>{self._config['name']}</b>: Fetching info")
        self.hm.callback.message("  - {}".format(_("Fetching info")))

        ## Download latest images.zip if needed.
        if 'images.000.zip' in self._data:
            return self._update2()

        if 'images.zip' not in self._data:
            return

        images_url_zip = self._data['images.zip']['url']

        if 'md5' in self._data['images.zip']:
            images_md5 = self._data['images.zip']['md5']

        else:
            images_url_md5 = self._data['images.zip.md5']['url']
            images_md5 = fetch_text(images_url_md5).strip().split(' ', 1)[0]

        if self._images_md5 is None or images_md5 != self._images_md5:
            logger.debug(f"images_md5={images_md5}, self.images_md5={self._images_md5}")
            images_zip = download(self.hm.temp_dir / "images.zip", images_url_zip, images_md5, callback=self.hm.callback)
            if images_zip is None:
                logger.debug(f"Unable to download {images_url_zip}")
                return

            images_to_delete = [
                file_name
                for file_name in self._images_dir.iterdir()
                if file_name.suffix in ('.png', '.jpg')]

            with zipfile.ZipFile(images_zip, 'r') as zf:
                for zip_name in zf.namelist():
                    if zip_name.casefold().rsplit('.')[-1] not in ('jpg', 'png'):
                        continue

                    file_name = self._images_dir / self.clean_name(zip_name.rsplit('/', 1)[-1])
                    if file_name not in images_to_delete:
                        logger.debug(f"adding {file_name}")

                    with open(file_name, 'wb') as fh:
                        fh.write(zf.read(zip_name))

                    if file_name in images_to_delete:
                        images_to_delete.remove(file_name)

            for image_to_delete in images_to_delete:
                logger.debug(f"removing {image_to_delete}")
                image_to_delete.unlink()

            self._images_md5_file.write_text(images_md5)
            self._images_md5 = images_md5

    def _load(self):
        ...

    def _clear(self):
        ...

    def update(self):
        # cprint(f"<b>{self._config['name']}</b>: updating")
        if self.hm.callback is not None:
            self.hm.callback.message(" - {}".format(_("Updating")))

        changed = False
        # Scrap the rest
        self._data = {}
        self._info = {}
        self.ports = []
        self.utils = []
        self.images = {}

        if self._did_update:
            # cprint(f"- <b>{self._config['name']}</b>: up to date already.")
            self.hm.callback.message(" - {}".format(_("Up to date already")))
            return

        # cprint(f"- <b>{self._config['name']}</b>: Fetching latest ports")
        if self.hm.callback is not None:
            self.hm.callback.message("  - {}".format(_("Fetching latest info")))

        data = fetch_json(self._config['url'])
        if data is None:
            return

        ## Load data from the assets.
        for key, asset in data['ports'].items():
            result = {
                'name': asset['name'],
                'size': asset['source']['size'],
                'md5': asset['source']['md5'],
                'url': asset['source']['url'],
                }

            self.ports.append(self.clean_name(key))
            self._info[self.clean_name(key)] = asset
            self._data[self.clean_name(key)] = result

        for key, asset in data['utils'].items():
            result = {
                'name': asset['name'],
                'size': asset['size'],
                'md5': asset['md5'],
                'url': asset['url'],
                }

            if key.endswith('.squashfs'):
                if 'runtime_name' in asset:
                    key=asset['runtime_name']
                    arch=asset['runtime_arch']
                    self.hm.runtimes_info.setdefault(key, {}).setdefault('remote', {})[arch] = result.copy()

                else:
                    self.hm.runtimes_info.setdefault(key, {}).setdefault('remote', {})['aarch64'] = result.copy()

                if 'name' in self.hm.runtimes_info[key]['remote']:
                    del self.hm.runtimes_info[key]['remote']['name']
                    del self.hm.runtimes_info[key]['remote']['size']
                    del self.hm.runtimes_info[key]['remote']['md5']
                    del self.hm.runtimes_info[key]['remote']['url']

                self.hm.runtimes_info[key]['name'] = result['name']
                self.hm.runtimes_info[key].setdefault('status', 'Unknown')
                changed = True

            self._data[self.clean_name(key)] = result
            if key.lower() in ('images.zip', 'portmaster.zip'):
                continue

            self.utils.append(self.clean_name(key))

        if changed:
            self.hm.list_runtimes()
            self.hm.save_config()

        self._update()

        self._load_images()

        self._config['version'] = self.VERSION

        self._config['data']['ports'] = self.ports
        self._config['data']['utils'] = self.utils
        self._config['data']['data']  = self._data
        self._config['data']['info']  = self._info

        self._config['last_checked'] = datetime.datetime.now().isoformat()

        self.save()
        self._did_update = True
        # cprint(f"- <b>{self._config['name']}:</b> Done.")
        self.hm.callback.message("  - {}".format(_("Done.")))

    def download(self, port_name, temp_dir=None, md5_result=None):
        if md5_result is None:
            md5_result = [None]

        if port_name not in self._data:
            logger.error(f"Unable to find port {port_name}")
            self.hm.callback.message_box(_("Unable to find {port_name}.").format(port_name=port_name))
            return None

        if temp_dir is None:
            temp_dir = self.hm.temp_dir

        md5_result[0] = self._data[port_name]['md5']
        zip_file = download(temp_dir / port_name, self._data[port_name]['url'], self._data[port_name]['md5'], callback=self.hm.callback)

        if zip_file is None:
            return None

        if port_name in self.utils:
            ## Utils
            return zip_file

        zip_info = port_info_load({})

        zip_info['name'] = port_name
        zip_info['status'] = {
            'source': self._config['name'],
            'md5':    md5_result[0],
            'status': 'downloaded',
            }
        zip_info['zip_file'] = zip_file

        port_info = self.port_info(port_name)
        port_info_merge(zip_info, port_info)

        return zip_info

    def port_info(self, port_name):
        port_name = self.clean_name(port_name)

        if port_name not in getattr(self, '_info', {}):
            return {}

        return self._info[port_name]

    def port_download_size(self, port_name, check_runtime=True):
        port_name = self.clean_name(port_name)

        if port_name not in getattr(self, '_data', {}):
            return 0

        size = self._data[port_name]['size']

        if check_runtime and port_name in getattr(self, '_info', {}):
            port_info = self._info[port_name]

            if port_info['attr'].get('runtime', None) is not None:
                runtime = port_info['attr']['runtime']

                runtime_file = (self.hm.libs_dir / runtime)
                if not runtime_file.exists():
                    size += self.hm.port_download_size(runtime)

        return size

    def port_download_url(self, port_name):
        port_name = self.clean_name(port_name)

        if port_name not in getattr(self, '_data', {}):
            return None

        return self._data[port_name]['url']


################################################################################
## Raw Downloader

def raw_download(save_path, file_url, callback=None, file_name=None, md5_source=None):
    """
    This is a bit of a hack, this acts as a source of ports, but for raw urls.
    This only supports downloading so not bothering to add it as a full blown source.
    """
    original_url = file_url
    url_info = urlparse(file_url)

    if file_name is None:
        file_name = url_info.path.rsplit('/', 1)[1]

    if file_name.endswith('.md5') or file_name.endswith('.md5sum'):
        ## If it is an md5 file, we assume the actual zip is sans the md5/md5sum
        md5_source = fetch_text(file_url)
        if md5_source is None:
            if callback is not None:
                callback.message_box(_("Unable to download verification file."))
            logger.error(f"Unable to download file: {file_url!r} [{r.status_code}]")
            return None

        md5_source = md5_source.strip().split(' ', 1)[0]

        file_name = file_name.rsplit('.', 1)[0]
        file_url = urlunparse(url_info._replace(path=url_info.path.rsplit('.', 1)[0]))

    if not file_name.endswith('.zip'):
        if callback is not None:
            callback.message_box(_("Unable to download non zip files."))

        logger.error(f"Unable to download file: {file_url!r} [doesn't end with '.zip']")
        return None

    file_name = file_name.replace('%20', '.').replace('+', '.').replace('..', '.')

    md5_result = [None]
    zip_file = download(save_path / file_name, file_url, md5_source, md5_result, callback=callback)

    if zip_file is None:
        return None

    zip_info = port_info_load({})

    zip_info['name'] = name_cleaner(zip_file.name)
    zip_info['zip_file'] = zip_file
    zip_info['status'] = {
        'source': 'url',
        'md5': md5_result[0],
        'url': original_url,
        'status': 'downloaded',
        }

    # print(f"-- {zip_info} --")

    # cprint("<b,g,>Success!</b,g,>")
    return zip_info


HM_SOURCE_APIS = {
    'GitHubRawReleaseV1': GitHubRawReleaseV1,
    'PortMasterV1': PortMasterV1,
    'PortMasterV2': PortMasterV2,
    'PortMasterV3': PortMasterV3,
    'GitHubRepoV1': GitHubRepoV1,
    }

__all__ = (
    'BaseSource',
    'raw_download',
    'HM_SOURCE_APIS',
    )

