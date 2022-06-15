from media import Media, MediaHolder
import pathlib
import tkinter as tk
from tkinter import filedialog
from backend import walker, all_extensions
window = tk.Tk()
window.withdraw()


def select_file() -> pathlib.Path:
    return pathlib.Path(filedialog.askopenfilename())


def select_folder() -> pathlib.Path:
    return pathlib.Path(filedialog.askdirectory())


if __name__ == "__main__":
    holder: MediaHolder[Media] = MediaHolder()
    holder.add_many(walker(select_folder(), all_extensions))
    holder.copy_with_new_names(pathlib.Path(filedialog.askdirectory()), holder.year_month_day())

