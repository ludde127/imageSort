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


def safe_copy(src: pathlib.Path, dst: pathlib.Path, depth=0):
    if dst.joinpath(src.name).exists():
        name, ext = src.name.split(".")
        name + "[" + str(str(time.time()).split(".")) + "]"
        src = src.with_name(name+"."+ext)
        if dst.joinpath(src.name).exists():
            if depth > 10:
                raise FileExistsError(f"Could not copy file {src} to {dst} as destination\n"
                                      f" already exists and overwrites are forbidden.")
            safe_copy(src, dst, depth=depth+1)
        os.makedirs(dst, exist_ok=True)
        shutil.copy2(str(src), str(dst), follow_symlinks=True)
    else:
        os.makedirs(dst, exist_ok=True)
        shutil.copy2(str(src), str(dst), follow_symlinks=True)


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


def walker(dir, extensions: list[str]):
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
