import os
import shutil
from media import Media
import pathlib
import tkinter as tk
from tkinter import filedialog

window = tk.Tk()
window.withdraw()


def select_file() -> pathlib.Path:
    return pathlib.Path(filedialog.askopenfilename())


if __name__ == "__main__":
    Media.from_path(select_file()).show()