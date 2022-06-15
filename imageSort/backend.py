import os
import shutil
import pathlib
import yaml


def safe_copy(src: pathlib.Path, dst: pathlib.Path):
    if dst.joinpath(src.name).exists():
        raise FileExistsError(f"Another file {dst} already_exists. Skipping.")
    else:
        os.makedirs(dst, exist_ok=True)
        shutil.copy2(str(src), str(dst), follow_symlinks=True)


def read_yaml(file, safe=True):
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


all_extensions = set(read_yaml("extensions/images.yaml")["formats"]). \
    union(set(read_yaml("extensions/media.yaml")["formats"]). \
          union(set(read_yaml("extensions/videos.yaml")["formats"])))
all_extensions = {e.lower() for e in all_extensions}


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
