"""Publish a preview bundle without overwriting any existing destination."""

from contextlib import contextmanager
import ctypes
import errno
import os
from pathlib import Path
import pwd
import stat
from uuid import uuid4

from .schema import ThemeError

_DIRECTORY = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW


def _destination(path):
    if ".." in path.parts:
        raise ThemeError("salida: no se admiten segmentos '..'")
    path = Path(os.path.abspath(path))
    if path == path.parent:
        raise ThemeError("salida: se requiere un directorio de pruebas específico")

    homes = {Path.home(), Path(pwd.getpwuid(os.getuid()).pw_dir)}
    protected = [home / suffix for home in homes for suffix in
                 (".config", ".local/share", ".local/bin", ".themes")]
    for key in ("XDG_CONFIG_HOME", "XDG_DATA_HOME", "XDG_CONFIG_DIRS", "XDG_DATA_DIRS"):
        protected.extend(Path(value) for value in os.environ.get(key, "").split(":")
                         if value and Path(value).is_absolute())
    protected.extend(Path(path) for path in ("/etc", "/usr", "/opt", "/run", "/proc", "/sys", "/dev"))
    if any(path.is_relative_to(root) or path.is_relative_to(os.path.realpath(root))
           for root in protected):
        raise ThemeError("salida: la ruta pertenece a un árbol de configuración o del sistema")
    return path


@contextmanager
def _open_directory(path):
    # Open each component relative to the verified parent without following links.
    fd = os.open("/", _DIRECTORY)
    try:
        for component in path.parts[1:]:
            child = os.open(component, _DIRECTORY, dir_fd=fd)
            os.close(fd)
            fd = child
        yield fd
    finally:
        os.close(fd)


def _existing_matches(parent, name, outputs):
    try:
        destination = os.open(name, _DIRECTORY, dir_fd=parent)
    except FileNotFoundError:
        return False
    except OSError as error:
        if error.errno in (errno.ENOTDIR, errno.ELOOP):
            raise ThemeError("salida: el destino existe y no es un directorio seguro") from error
        raise
    try:
        if set(os.listdir(destination)) != set(outputs):
            raise ThemeError("salida: el directorio existe con otros contenidos; elige otro destino")
        for filename, data in outputs.items():
            info = os.stat(filename, dir_fd=destination, follow_symlinks=False)
            if not stat.S_ISREG(info.st_mode) or info.st_size != len(data):
                raise ThemeError(f"salida.{filename}: archivo ajeno o distinto; elige otro destino")
            fd = os.open(filename, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=destination)
            with os.fdopen(fd, "rb") as stream:
                opened = os.fstat(stream.fileno())
                if (not stat.S_ISREG(opened.st_mode) or opened.st_size != len(data)
                        or stream.read(len(data) + 1) != data):
                    raise ThemeError(f"salida.{filename}: contenido distinto; elige otro destino")
        return True
    finally:
        os.close(destination)


def _write_file(directory, filename, data):
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW
    fd = os.open(filename, flags, 0o600, dir_fd=directory)
    with os.fdopen(fd, "wb") as stream:
        stream.write(data)
        stream.flush()
        os.fsync(stream.fileno())


def _rename_new(parent, source, destination):
    # Linux renameat2 with RENAME_NOREPLACE commits both fragments in one operation.
    libc = ctypes.CDLL(None, use_errno=True)
    try:
        rename = libc.renameat2
    except AttributeError as error:
        raise ThemeError("salida: la plataforma no ofrece renameat2") from error
    rename.argtypes = (ctypes.c_int, ctypes.c_char_p, ctypes.c_int, ctypes.c_char_p, ctypes.c_uint)
    rename.restype = ctypes.c_int
    if rename(parent, os.fsencode(source), parent, os.fsencode(destination), 1) != 0:
        code = ctypes.get_errno()
        raise OSError(code, os.strerror(code))


def _publish(parent, name, outputs):
    if _existing_matches(parent, name, outputs):
        return False

    staging = f".carbon-preview-{uuid4().hex}"
    os.mkdir(staging, mode=0o700, dir_fd=parent)
    directory = None
    published = False
    try:
        directory = os.open(staging, _DIRECTORY, dir_fd=parent)
        for filename, data in outputs.items():
            _write_file(directory, filename, data)
        os.fsync(directory)
        try:
            _rename_new(parent, staging, name)
        except FileExistsError:
            if _existing_matches(parent, name, outputs):
                return False
            raise
        published = True
        return True
    finally:
        try:
            if not published:
                if directory is not None:
                    for filename in outputs:
                        try:
                            os.unlink(filename, dir_fd=directory)
                        except FileNotFoundError:
                            pass
                os.rmdir(staging, dir_fd=parent)
        finally:
            if directory is not None:
                os.close(directory)


def write_preview(path, outputs):
    path = _destination(path)
    # Output names are supplied by trusted renderer registrations, as basenames.
    if not outputs or any(Path(name).name != name or name in ("", ".", "..") for name in outputs):
        raise ThemeError("salida: nombres de artefactos inválidos")
    try:
        with _open_directory(path.parent) as parent:
            return _publish(parent, path.name, outputs)
    except FileNotFoundError as error:
        raise ThemeError("salida: crea primero el directorio padre de pruebas") from error
    except OSError as error:
        raise ThemeError(f"salida: no se pudo publicar la vista previa ({error.strerror})") from error
