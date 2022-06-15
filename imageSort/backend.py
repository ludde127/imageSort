import os
import shutil
from media import Media, MediaHolder
import pathlib
import tkinter as tk
from tkinter import filedialog

window = tk.Tk()
window.withdraw()


def select_file() -> pathlib.Path:
    return pathlib.Path(filedialog.askopenfilename())


if __name__ == "__main__":
    holder: MediaHolder[Media] = MediaHolder()
    holder.append(Media.from_path(select_file()))
    holder.append(Media.from_path(select_file()))
    """print(pic.datetime())
    print(pic.datetime(as_timestamp=True))
    print(pic.show())"""
    holder.sort_by_time()
    for image in holder:
        image.show()
