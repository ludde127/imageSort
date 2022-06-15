import pathlib
from dataclasses import dataclass
from PIL import Image
from PIL.ExifTags import TAGS
from pprint import pprint

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