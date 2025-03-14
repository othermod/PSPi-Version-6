import sys
import os
import re
import zipfile
import tarfile
import io

__all__ = ["open_zipfile", "open_tarfile", "open_url", "Resources"]

# Python 3.x workarounds for the changed urllib modules.
if sys.version_info[0] >= 3:
    import urllib.parse as urlparse
    import urllib.request as urllib2
else:
    import urlparse
    import urllib2


def _validate_path(path, what, write=False):
    fullpath = os.path.abspath(path)
    fname = os.path.basename(path)
    if write:
        parent = os.path.abspath(os.path.join(fullpath, os.pardir))
        if not os.path.isdir(parent):
            e = "The given parent directory '{0}' does not exist"
            raise IOError(e.format(parent))
    else:
        if not os.path.exists(fullpath):
            e = "Could not find {0} at the given path: {1}"
            raise IOError(e.format(what, fullpath))
    return (fullpath, fname)


def open_zipfile(archive, filename, directory=None):
    """Retrieves a given file from a ZIP archive.

    Args:
        archive (:obj:`~zipfile.ZipFile`, str): The ZipFile object or path to
            the ZIP archive containing the desired file.
        filename (str): The name of the file to retrieve from the archive.
        directory (str, optional): The path to the directory within the archive
            containing the file to retrieve. Defaults to the root level of the
            archive.

    Returns:
        :obj:`~io.BytesIO`: A Python bytestream object containing the requested
        file.

    Raises:
        KeyError: If the given file could not be found within the archive.
        TypeError: If the archive is not a valid ZIP archive.

    """
    data = None
    opened = False

    if not isinstance(archive, zipfile.ZipFile):
        if not zipfile.is_zipfile(archive):
            raise TypeError("passed file does not seem to be a ZIP archive")
        else:
            archive = zipfile.ZipFile(archive, 'r')
            opened = True

    apath = filename
    if directory:
        apath = "%s/%s" % (directory, filename)

    try:
        dmpdata = archive.open(apath)
        data = io.BytesIO(dmpdata.read())
    finally:
        if opened:
            archive.close()
    return data


def open_tarfile(archive, filename, directory=None, ftype=None):
    """Retrieves a given file from a TAR archive.

    If the TAR archive uses ``.tar.gz`` or ``.tar.bz2`` compression and the
    file name does not contain either of these identifiers, the compression
    type must be manually specified.

    Args:
        archive (:obj:`~tarfile.TarFile`, str): The TarFile object or path to
            the TAR archive containing the desired file.
        filename (str): The name of the file to retrieve from the archive.
        directory (str, optional): The path to the directory within the archive
            containing the file to retrieve. Defaults to the root level of the
            archive.
        ftype (str, optional): The compression type (if any) used for the TAR
            file, can be either 'gz', 'bz2', or None (no compression). If not
            specified, will default to assuming no compression.

    Returns:
        :obj:`~io.BytesIO`: A Python bytestream object containing the requested
        file.

    Raises:
        KeyError: If the given file could not be found within the archive.
        TypeError: If the archive is not a supported TAR archive.

    """
    data = None
    opened = False

    if not isinstance(archive, tarfile.TarFile):
        if not tarfile.is_tarfile(archive):
            raise TypeError("passed file does not seem to be a TAR archive")
        else:
            file_ext = archive.split('.')[-1]
            if not ftype and file_ext in ('gz', 'bz2'):
                ftype = file_ext
            if ftype and ftype not in ('gz', 'bz2'):
                e = "invalid TAR compression type '{0}' (must be 'gz' or 'bz2')"
                raise TypeError(e.format(ftype))
            mode = 'r:{0}'.format(ftype) if ftype else 'r'
            archive = tarfile.open(archive, mode)
            opened = True

    apath = filename
    if directory:
        apath = "%s/%s" % (directory, filename)

    try:
        dmpdata = archive.extractfile(apath)
        data = io.BytesIO(dmpdata.read())
    finally:
        if opened:
            archive.close()
    return data


def open_url(filename, basepath=None):
    # Opens and reads a certain file from a web or remote location.
    # Deprecated because its argument names are confusing and because
    # users are probably better off using urllib directly.
    url = filename
    if basepath:
        url = urlparse.urljoin(basepath, filename)
    return urllib2.urlopen(url)


class Resources(object):
    """A container class for managing application resource files.
    
    This class eases access to resources by allowing access using relative
    paths, scanning archives to locate files, and more.

    Args:
        path (str, optional): The path of a resource directory with which to
            initialze the container. Defaults to ``None``.
        subdir (str, optional): Deprecated, do not use.
        excludepattern (str, optional): A regular expression indicating
            which directories (if any) to ignore if initializing the
            container with a resource path. Defaults to ``None``.

    """
    def __init__(self, path=None, subdir=None, excludepattern=None):
        self.files = {}
        if path:
            self.scan(path, subdir, excludepattern)

    def _scanzip(self, filename):
        """Scans the passed ZIP archive and indexes all the files
        contained by it.
        """
        if not zipfile.is_zipfile(filename):
            raise TypeError("file '%s' is not a valid ZIP archive" % filename)
        archname = os.path.abspath(filename)
        zipf = zipfile.ZipFile(filename, 'r')
        for path in zipf.namelist():
            fname = os.path.split(path)[1]
            if fname:
                self.files[fname] = (archname, 'zip', path)
        zipf.close()

    def _scantar(self, filename, ftype=None):
        """Scans the passed TAR archive and indexes all the files
        contained by it.
        """
        if not tarfile.is_tarfile(filename):
            raise TypeError("file '%s' is not a valid TAR archive" % filename)
        file_ext = filename.split('.')[-1]
        if not ftype and file_ext in ('gz', 'bz2'):
            ftype = file_ext
        if ftype and ftype not in ('gz', 'bz2'):
            e = "invalid TAR compression type '{0}' (must be 'gz' or 'bz2')"
            raise TypeError(e.format(ftype))
        mode = 'r:{0}'.format(ftype) if ftype else 'r'
        archname = os.path.abspath(filename)
        archtype = 'tar'
        if ftype:
            archtype = 'tar%s' % ftype
        tar = tarfile.open(filename, mode)
        for path in tar.getnames():
            fname = os.path.split(path)[1]
            self.files[fname] = (archname, archtype, path)
        tar.close()

    def add(self, filename):
        """Adds a file to the Resources container.

        If the given file is a supported archive, its contents will be scanned
        and added to the container.

        Args:
            filename (str): The filepath of the resource to add to the
                container.

        Raises:
            ValueError: If the file does not exist at the provided path.

        """
        if not os.path.exists(filename):
            raise ValueError("invalid file path")
        if zipfile.is_zipfile(filename):
            self.add_archive(filename)
        elif tarfile.is_tarfile(filename):
            self.add_archive(filename, 'tar')
        else:
            self.add_file(filename)

    def add_file(self, filename):
        """Adds a file without scanning to the Resources container.

        Unlike :meth:`add`, this method will not attempt to add the contents
        of any provided archives to the container.

        Args:
            filename (str): The filepath of the resource to add to the
                container.

        Raises:
            ValueError: If the file does not exist at the provided path.

        """
        if not os.path.exists(filename):
            raise ValueError("invalid file path")
        abspath = os.path.abspath(filename)
        fname = os.path.split(abspath)[1]
        if not fname:
            raise ValueError("invalid file path")
        self.files[fname] = (None, None, abspath)

    def add_archive(self, filename, typehint='zip'):
        """Adds a ``.zip`` or ``.tar`` archive to the container.

        This will scan the passed archive and add its contents to the
        list of available resources. Currently ``.zip``, ``.tar``,
        ``.tar.bz2``, and ``.tar.gz`` formats are supported.

        Args:
            filename (str): The filepath of the archive to scan and add to the
                container.
            typehint (str, optional): The format of the archive to add to the
                container, required if using a custom file extension. Must be
                one of ``zip``, ``tar``, ``tarbz2``, or ``targz``. Defaults to
                ``zip`` if not specified.

        Raises:
            ValueError: If the file does not exist at the provided path, or if
                the file is not a supported archive type.

        """
        if not os.path.exists(filename):
            raise ValueError("invalid file path")
        fname = os.path.basename(filename)
        if 'zip' in fname.split('.'):
            self._scanzip(filename)
        elif 'tar' in fname.split('.'):
            self._scantar(filename)
        else:
            if typehint == 'zip':
                self._scanzip(filename)
            elif typehint == 'tar':
                self._scantar(filename)
            elif typehint == 'tarbz2':
                self._scantar(filename, 'bz2')
            elif typehint == 'targz':
                self._scantar(filename, 'gz')
            else:
                raise ValueError("unsupported archive type")

    def get(self, filename):
        """Retrieves a resource file by name from the container.

        Args:
            filename (str): The file name of the resource to retrieve.

        Returns:
            :obj:`~io.BytesIO`: A Python bytestream object containing the
            retrieved resource file.

        Raises:
            KeyError: If the given file could not be found.

        """
        archive, ftype, pathname = self.files[filename]
        if archive:
            if ftype == 'zip':
                return open_zipfile(archive, pathname)
            elif ftype == 'tar':
                return open_tarfile(archive, pathname)
            elif ftype == 'tarbz2':
                return open_tarfile(archive, pathname, ftype='bz2')
            elif ftype == 'targz':
                return open_tarfile(archive, pathname, ftype='gz')
            else:
                raise ValueError("unsupported archive type")
        dmpdata = open(pathname, 'rb')
        data = io.BytesIO(dmpdata.read())
        dmpdata.close()
        return data

    def get_filelike(self, filename):
        # Deprecated, doesn't make much difference in Python 3
        archive, ftype, pathname = self.files[filename]
        if archive:
            if ftype == 'zip':
                return open_zipfile(archive, pathname)
            elif ftype == 'tar':
                return open_tarfile(archive, pathname)
            elif ftype == 'tarbz2':
                return open_tarfile(archive, pathname, ftype='bz2')
            elif ftype == 'targz':
                return open_tarfile(archive, pathname, ftype='gz')
            else:
                raise ValueError("unsupported archive type")
        return open(pathname, 'rb')

    def get_path(self, filename):
        """Gets the path of a given resource file.

        If the file is only available within an archive, a string in the form
        ``filename@archivename`` will be returned.

        Args:
            filename (str): The file name of the resource to locate.

        Returns:
            str: The absolute path of the resource file, or the archive
            identifier string if the resource is inside an archive.

        Raises:
            KeyError: If the given file could not be found.

        """
        archive, ftype, pathname = self.files[filename]
        if archive:
            return '%s@%s' % (pathname, archive)
        return pathname

    def scan(self, path, subdir=None, excludepattern=None):
        """Scans a path, adding all matching files to the container.

        If a located file is a ``.zip`` or ``.tar`` archive, its
        contents will be indexed and added to the container automatically.

        Args:
            path (str): The path of the directory to scan.
            subdir (str, optional): Deprecated, do not use.
            excludepattern (str, optional): A regular expression indicating
                which directories (if any) within the file structure of the
                given path to exclude from indexing. Defaults to ``None``. 

        Raises:
            ValueError: If the specified path does not exist.

        """
        match = None
        if excludepattern:
            match = re.compile(excludepattern).match
        join = os.path.join
        add = self.add
        abspath = os.path.abspath(path)
        if not os.path.exists(abspath):
            raise ValueError("invalid path '%s'" % abspath)
        if not os.path.isdir(abspath):
            abspath = os.path.dirname(abspath)
        if subdir is not None:
            abspath = os.path.join(abspath, subdir)
        if not os.path.exists(abspath):
            raise ValueError("invalid path '%s'" % abspath)
        for (pdir, dirnames, filenames) in os.walk(abspath):
            if match and match(pdir) is not None:
                continue
            for fname in filenames:
                add(join(pdir, fname))
