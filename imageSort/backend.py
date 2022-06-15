import os
import shutil
import pathlib


def safe_copy(src: pathlib.Path, dst: pathlib.Path):
    if dst.exists():
        raise FileExistsError(f"Another file {dst} already_exists. Skipping.")
    else:
        os.makedirs(dst, exist_ok=True)
        shutil.copy2(str(src), str(dst), follow_symlinks=True)


def all_files_in_folder(directory_path: pathlib.Path) -> list[pathlib.Path]:
    return [p for p in [pathlib.Path(path) for path in os.listdir(directory_path)] if p.is_file()]
