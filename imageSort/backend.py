import os
import shutil
import pathlib
import sys
import time

import yaml


def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)


def safe_copy_v2(src: pathlib.Path, dst: pathlib.Path, add_uncertain_metadata_tag=False, max_depth=10) -> pathlib.Path:
    """This copies the files and never overwrites any files, it returns the final path which may not be the same
       as the given dst path if that spot was occupied."""
    if add_uncertain_metadata_tag:
        name = dst.name
        (name_no_ext, ext) = name.split(".")
        dst = dst.with_name(name_no_ext + "_uncertain_metadata." + ext)

    if dst.exists():
        name = dst.name
        (name_no_ext, ext) = name.split(".")
        depth = 1
        while dst.exists() and depth < max_depth:
            dst = dst.with_name(name_no_ext+f"[{depth}]."+ext)
            depth += 1

        if not dst.exists():
            os.makedirs(dst.parent, exist_ok=True)
            return pathlib.Path(shutil.copy2(src, dst))
        else:
            raise CopyFailed(f"Copy failed on {src} -> {dst} as max depth while avoiding overwrite was succeded",
                             media_path=str(src))

    else:
        os.makedirs(dst.parent, exist_ok=True)
        return pathlib.Path(shutil.copy2(src, dst))


def read_yaml(file, safe=True):
    file = resource_path(file)  # Needed for PyInstaller
    try:
        with open(file, "r+") as f:
            if safe:
                data = yaml.safe_load(f)
            else:
                data = yaml.load_all(f)
    except FileNotFoundError as e:
        print(e)
        data = {}
    return data


def write_txt_row(file, data, newline=True, error_handled=False):
    """Appends the data to file"""
    data = str(data)
    try:
        if isinstance(data, list) or isinstance(data, set) or isinstance(data, tuple):
            with open(file, "a+") as f:
                for d in data:
                    f.write(f"{d}\n")
        elif len(str(data).replace(" ", "")) > 0:
            with open(file, "a+") as f:
                if newline:
                    f.write(f"{data}\n")
                else:
                    f.write(data)
    except FileNotFoundError as e:
        print(e)
        os.makedirs(pathlib.Path(file).parent)
        if not error_handled:
            write_txt_row(file, data, error_handled=True)
        else:
            raise FileNotFoundError


class CopyFailed(Exception):
    def __init__(self, msg:str, media_path: str):
        self.msg = msg
        self.media_path = media_path


image_exts = {e.lower() for e in set(read_yaml("extensions/images.yaml")["formats"])}
media_exts = {e.lower() for e in set(read_yaml("extensions/media.yaml")["formats"])}
video_exts = {e.lower() for e in set(read_yaml("extensions/videos.yaml")["formats"])}

all_extensions = image_exts.union(media_exts.union(video_exts))


def walker(dir, extensions: list[str]) -> set[pathlib.Path]:
    """This function will return all possible file paths from a dir, its an recursive use of os.walk(dir)"""
    paths = set()
    assert isinstance(paths, set)
    for root, dirs, files in os.walk(dir):
        for file in files:
            if (file.split(".")[-1]).lower() in extensions:
                paths.add(pathlib.Path(root).joinpath(file))
        for dir in dirs:
            paths.union(walker(dir, extensions))
    return paths  # Returns a set of all paths as pathlib.Path objs under dir
