from media import Media, MediaHolder
import pathlib
import tkinter as tk
from tkinter import filedialog
from backend import all_files_in_folder
window = tk.Tk()
window.withdraw()


def select_file() -> pathlib.Path:
    return pathlib.Path(filedialog.askopenfilename())


def select_folder() -> pathlib.Path:
    return pathlib.Path(filedialog.askdirectory())


if __name__ == "__main__":
    holder: MediaHolder[Media] = MediaHolder()
    holder.add_many(all_files_in_folder(select_folder()))
    holder.copy_with_new_names(pathlib.Path(filedialog.askdirectory()), holder.year_month_day())

