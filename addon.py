import os
import tempfile

import requests

import settings
import json


class AddOn:
    """Class representing an installed add-on.

    id: The add-on's ID on the server
    name: The add-on's name
    version: the installed version
    paths: List of directories that are installed
    settings_paths: List of directories/files that contain add-on settings"""
    def __init__(self, id, name, version, paths=None, settings_paths=None):
        if not paths:
            paths = []
        if not settings_paths:
            settings_paths = []

        self.id = id
        self.name = name
        self.version = version
        self.paths = paths
        self.settings_paths = settings_paths

    def __eq__(self, other):
        return (self.name, self.version) == (other.name, other.version)

    def __str__(self, *args, **kwargs):
        return self.name

    def to_json(self):
        return json.dumps(self.__dict__)

    @classmethod
    def from_dict(cls, dct):
        try:
            return cls(
                id=dct['id'],
                name=dct['name'],
                version=dct['version'],
                paths=dct['paths'],
                settings_paths=dct['settings_paths'],
            )
        except KeyError as e:
            raise ValueError('Invalid dict for AddOn') from e


def fetch_add_on_data(add_on_id):
    """Fetch an add-on dataa from the server."""
    url = settings.URLS['add_on_details'].format(id=add_on_id)

    try:
        return requests.get(url).json()
    except requests.HTTPError as e:
        raise RuntimeError('Could not fetch add-on for id {}'.format(add_on_id)) from e


def get_installed_add_ons():
    """Return a list of installed add-ons."""
    add_ons = []
    with open(settings.FILES['database']) as f:
        data = json.load(f)
        for add_on in data:
            add_ons.append(AddOn.from_dict(add_on))

    return add_ons


def download_to_file(url, file_handler):
    """Download the given file at `url` to `filehandler`."""
    stream = requests.get(url, stream=True)

    for chunk in stream.iter_content(chunk_size=1024):
        if chunk:
            file_handler.write(chunk)


def update_installed_add_ons():
    """Update all installed add-ons to the latest version.

    Update the database file if successful."""


def install_add_on(add_on_id):
    """Download and extract the latest version of the add-on with the specified ID.

    Update the database file if successful."""
    data = fetch_add_on_data(add_on_id)

    temp_zip_file = tempfile.mkstemp(suffix='.zip')
    with open(temp_zip_file) as f:
        download_to_file(data['latest_version']['url'], f)

    # TODO unzip, move dirs, set paths on AddOn object


def remove_add_on(add_on, with_settings=False):
    """Remove all directories of an add-on.

     Update the database file if successful."""
    for path in add_on.paths:
        full_path = os.path.join(settings.CONFIG.get('AddOnsDir'), path)
        os.removedirs(full_path)

    if with_settings:
        for settings_path in add_on.settings_paths:
            full_path = os.path.realpath(os.path.join(settings.CONFIG.get('AddOnsDir'), '../WTF/', settings_path))
            if os.path.isfile(full_path):
                os.remove(full_path)
            elif os.path.isdir(full_path):
                os.removedirs(full_path)
