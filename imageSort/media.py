import pathlib

import PIL

from backend import safe_copy, video_exts, media_exts, image_exts
from dataclasses import dataclass
from PIL import Image
from PIL.ExifTags import TAGS
from pprint import pprint
import datetime
import os
from tqdm import tqdm

time_field = "DateTime"  # This seems to be a common time_field


def extension_from_pathlib_path(path):
    return path.name.split(".")[-1].lower()


def get_metadata_image(path: pathlib.Path, only_keep_time_field=True, print_=False) -> dict[str]:
    exifdata = Image.open(str(path)).getexif()
    parsed = dict()
    # TODO change so it gets access to same amount of info as windows, which it does not do. At least not on old pics.
    for tag_id in exifdata:
        # get the tag name, instead of human unreadable tag id
        tag = TAGS.get(tag_id, tag_id)
        if only_keep_time_field and tag != time_field:
            continue
        data = exifdata.get(tag_id)
        # decode bytes
        if isinstance(data, bytes):
            try:
                data = data.decode()
                parsed[tag] = data
            except UnicodeDecodeError:
                parsed[tag] = "Error: Could not decode."
        else:
            parsed[tag] = data

        if print_:
            print(f"{tag:25}: {parsed[tag]}")
    return parsed


def get_metadata_video(path: pathlib.Path, only_keep_time_field=True, print_=False) -> dict[str]:
    data = {time_field: min([os.path.getctime(str(path)), os.path.getmtime(str(path))])}
    if print_:
        print(data)
    return data


@dataclass
class Media:
    filename: str
    path: pathlib.Path
    metadata: dict[str]
    uncertain_metadata = False

    @staticmethod
    def from_path(path: pathlib.Path, only_keep_time=True):
        """Loads the metadata from a file at the path."""
        ext = extension_from_pathlib_path(path)
        if ext in image_exts:
            try:
                meta = get_metadata_image(path, only_keep_time_field=only_keep_time, print_=False)
            except PIL.UnidentifiedImageError as e:
                print(e)
                meta = None
        elif ext in video_exts:
            meta = get_metadata_video(path, only_keep_time_field=only_keep_time, print_=False)
        return Media(filename=path.name, path=path, metadata=meta)

    def show(self):
        pprint({"Path": self.path, "Filename": self.filename, "Metadata": self.metadata})

    def datetime(self, as_timestamp=False):
        if "DateTime" in self.metadata:
            try:
                dt = datetime.datetime.strptime(self.metadata["DateTime"], "%Y:%m:%d %H:%M:%S")
            except TypeError:
                assert isinstance(self.metadata["DateTime"], float)
                dt = datetime.datetime.fromtimestamp(self.metadata["DateTime"], datetime.datetime.now().tzinfo)

            if as_timestamp:
                return dt.timestamp()
            return dt
        else:
            try:
                self.uncertain_metadata = True
                dt_unprecise = min([os.path.getctime(str(self.path)), os.path.getmtime(str(self.path))])
                dt = datetime.datetime.fromtimestamp(dt_unprecise, datetime.datetime.now().tzinfo)
                if as_timestamp:
                    return dt.timestamp()
                return dt
            except Exception as e:
                raise e

    def y_m_d_folder(self):
        """Creates a part of a path for example Year 2022/September/Day 23"""
        dt = self.datetime()
        month_name = "{0:%B}".format(dt)

        part = "Year " + str(dt.year) + "/" + month_name + "/" + "Day " + str(dt.day)

        return part


class MediaHolder(list):
    def sort_by_time(self):
        self.sort(key=lambda m: m.datetime(as_timestamp=True))

    def add_many(self, paths: list[pathlib.Path]):
        print("Checking metadata")
        for path in tqdm(paths):
            self.append(Media.from_path(path))
        print(f"Adding {len(paths)} files matching the allowed extensions.")

    def year_month_day(self) -> dict[int,
                                     dict[int,
                                          dict[int, list[Media]]]]:
        """Groups the files into a sorted order from the dates they were taken.
         The format of the files is year/month/day."""
        dict_representation = dict()
        for file in self:
            try:
                dt = file.datetime()
            except KeyError as e:
                print(e)
                dt = None
            if dt is not None:
                try:
                    dict_representation[dt.year][dt.month][dt.day].append(file)
                except KeyError:
                    if dt.year not in dict_representation:
                        dict_representation[dt.year] = dict()
                    if dt.month not in dict_representation[dt.year]:
                        dict_representation[dt.year][dt.month] = dict()
                    if dt.day not in dict_representation[dt.year][dt.month]:
                        dict_representation[dt.year][dt.month][dt.day] = list()
                    dict_representation[dt.year][dt.month][dt.day].append(file)
        return dict_representation

    def copy_with_new_names(self, destination_folder: pathlib.Path,
                            name_description: dict[int, dict[int, dict[int, list[Media]]]]):
        """Copies the files into their new correct folders, will not change filenames."""
        print("Starting copying of files.")
        moved = 0
        tq = tqdm(total=len(self))
        for year in name_description.keys():
            for month in name_description[year].keys():
                for day in name_description[year][month].keys():
                    for image in name_description[year][month][day]:
                        month_name = "{0:%B}".format(image.datetime())
                        safe_copy(image.path,
                                  destination_folder.joinpath("Year " + str(year)).joinpath(month_name).
                                  joinpath("Day " + str(day)))
                        moved += 1
                        tq.update(1)
                        self.remove(image)
        for file in self:
            """Those with no datetime"""
            safe_copy(file.path, destination_folder.joinpath("Not_enough_metadata"))
            moved += 1
            tq.update(1)
        print(f"Moved {moved} images or videos.")

