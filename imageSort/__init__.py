import os.path
import shutil
import time

from tqdm import tqdm
from media import Media
import pathlib
import tkinter as tk
from tkinter import Button
from tkinter import filedialog
from backend import walker, all_extensions, safe_copy_v2, write_txt_row, CopyFailed
from tkinter import ttk

WIDTH = 500
HEIGHT = 200


class UI:
    source = None
    dest = None
    display_text = "Select a source and a destination\n folder to sort images."
    error_filename = "Error file " + str(int(time.time())) + ".txt"

    def __init__(self, master):
        self.text_display = tk.Label(master, text=self.display_text, bg="white")

        self.label_src = tk.Label(master, text="Select a source folder.")
        self.label_dest = tk.Label(master, text="Select the destination folder.")
        self.src_b = Button(master, text="...", command=lambda: self.set_src())
        self.dest_b = Button(master, text="...", command=lambda: self.set_dst())
        self.begin_sort = Button(master, text="Begin to copy and sort images.", command=lambda: self.begin())
        self.progress_bar = ttk.Progressbar(master, orient=tk.HORIZONTAL, length=WIDTH-20, mode="determinate")

    def set_src(self):
        folder = select_folder()
        if str(folder) != ".":
            print(folder)
            self.source = folder
            self.src_b["text"] = self.source

    def enough_storage_space(self) -> bool:
        """True if available space > needed. Defaults to false if paths are not specified."""
        if self.source is not None and self.dest is not None:
            root_directory = self.source
            src_size = sum(f.stat().st_size for f in root_directory.rglob('**/*') if f.is_file())
            (_, _, free_dst) = shutil.disk_usage(str(self.dest))
            return free_dst > src_size * 1.05  # Adds a small part to be safe
        return False

    def begin(self):
        if self.source is not None and self.dest is not None:
            self.text_display["text"] = "Checking if you have the needed amount\n of disk space to copy the files."
            if self.enough_storage_space():
                first = True
                to_move = 0
                moved = 0
                for output in fast_copy_for_ui(self.source, self.dest):
                    if first:
                        to_move = len(output)
                        self.display(f"Began to copy and sort {to_move} media files.")
                        self.progress_bar["maximum"] = to_move

                        first = False
                    elif isinstance(output, int):
                        moved += output
                        self.progress_bar["value"] += output
                        self.progress_bar.update()
                        percent = moved/to_move
                        self.display(f"Have sorted and copied {(percent*100):.1f} % ({moved}/{to_move})", success=True)

                    elif isinstance(output, CopyFailed):
                        write_txt_row(self.error_filename, f"Error info {output.msg}, {output.media_path}")
                        #self.display(f"Failed to copy and sort \n{output.media_path}", error=True, cont=True)
                if moved == to_move:
                    self.display(f"Correctly moved and sorted {moved}/{to_move} files!")
                else:
                    self.display(f"Correctly moved and sorted {moved}/{to_move} files, some were not moved\n"
                                 f"check '{self.error_filename}' for those files.")
            else:
                self.display(f"You do not have enough storage space to copy those files.", error=True)
        else:
            self.display("You must select both a source folder and an\n destination folder before beginning.")

    def display(self, text: str, error=False, cont=False, success=False):
        if not cont:
            self.text_display["text"] = text
        else:
            self.text_display["text"] = text + ", continuing copy."
        if error:
            self.text_display["bg"] = "yellow"
            write_txt_row(self.error_filename, text)
        elif success:
            self.text_display["bg"] = "#62eb23"

    def set_dst(self):
        folder = select_folder()
        if str(folder) != ".":
            self.dest = folder
            self.dest_b["text"] = self.dest

    def place(self):
        self.text_display.grid(row=0, column=0, columnspan=2, rowspan=2, padx=10, pady=5, sticky='NSEW')
        self.label_src.grid(column=0, row=2, padx=10, pady=5, sticky='NSEW')
        self.label_dest.grid(column=0, row=3, padx=10, pady=5, sticky='NSEW')
        self.src_b.grid(column=1, row=2, padx=10, pady=5, sticky='NSEW')
        self.dest_b.grid(column=1, row=3, padx=10, pady=5, sticky='NSEW')
        self.begin_sort.grid(row=4, column=0, columnspan=2, padx=10, pady=5, sticky='NSEW')
        self.progress_bar.grid(row=5, column=0, columnspan=2, padx=10, pady=5, sticky='NSEW')


def select_file() -> pathlib.Path:
    return pathlib.Path(filedialog.askopenfilename())


def select_folder() -> pathlib.Path:
    return pathlib.Path(filedialog.askdirectory())


def fast_copy_for_ui(src: pathlib.Path, dst: pathlib.Path):
    files = walker(src, all_extensions)
    yield files
    for file in tqdm(files, total=len(files)):
        try:
            media = Media.from_path(file)
            try:
                sub_folder = media.y_m_d_folder()
            except KeyError:
                # Had no time metadata!
                sub_folder = "no_metadata"
            try:
                full_dst = dst.joinpath(sub_folder).joinpath(file.name)
                final_path = safe_copy_v2(file, full_dst, add_uncertain_metadata_tag=media.uncertain_metadata)
                assert final_path.exists() and final_path.is_file()
                yield 1
            except Exception as e:
                yield CopyFailed(str(e), str(media.path))
        except Exception as e:
            yield CopyFailed(str(e), str(file))


def inspect_image():
    file = select_file()
    media = Media.from_path(file, only_keep_time=False)
    media.show()


if __name__ == "__main__":
    root = tk.Tk()

    root.title("Image sorter")
    root.columnconfigure(0, weight=1)
    root.columnconfigure(1, weight=3)
    ui = UI(root)
    ui.place()
    root.mainloop()
