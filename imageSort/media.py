import pathlib
from backend import safe_copy
from dataclasses import dataclass
from PIL import Image
from PIL.ExifTags import TAGS
from pprint import pprint
import datetime

time_field = "DateTime"  # This seems to be a common time_field


def get_metadata(path: pathlib.Path, print_=False) -> dict[str]:
    exifdata = Image.open(str(path)).getexif()
    parsed = dict()
    for tag_id in exifdata:
        # get the tag name, instead of human unreadable tag id
        tag = TAGS.get(tag_id, tag_id)
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


@dataclass
class Media:
    filename: str
    path: pathlib.Path
    metadata: dict[str]

    @staticmethod
    def from_path(path: pathlib.Path):
        """Loads the image from a path"""
        meta = get_metadata(path, False)
        return Media(filename=path.name, path=path, metadata=meta)

    def show(self):
        pprint({"Path": self.path, "Filename": self.filename, "Metadata": self.metadata})

    def datetime(self, as_timestamp=False):
        if "DateTime" in self.metadata:
            dt = datetime.datetime.strptime(self.metadata["DateTime"], "%Y:%m:%d %H:%M:%S")
            if as_timestamp:
                return dt.timestamp()
            return dt
        else:
            raise KeyError("Datetime does not exist in metadata.")


class MediaHolder(list):
    def sort_by_time(self):
        self.sort(key=lambda m: m.datetime(as_timestamp=True))

    def add_many(self, paths: list[pathlib.Path]):
        for path in paths:
            self.append(Media.from_path(path))

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
        for year in name_description.keys():
            for month in name_description[year].keys():
                for day in name_description[year][month].keys():
                    for image in name_description[year][month][day]:
                        safe_copy(image.path,
                                  destination_folder.joinpath(str(year)).joinpath(str(month)).
                                  joinpath(str(day)))
                        self.remove(image)
        for file in self:
            """Those with no datetime"""
            safe_copy(file.path, destination_folder.joinpath("Not_enough_metadata").joinpath(file.filename))