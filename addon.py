import json
import os
import shutil
import tempfile
from zipfile import ZipFile

import logging
import requests

import settings


class AddOn:
    """Class representing an installed add-on.

    id: The add-on's ID on the server
    name: The add-on's name
    version: the installed version
    paths: List of directories that are installed"""
    def __init__(self, add_on_id, name, version, paths=None):
        if not paths:
            paths = []

        self.id = add_on_id
        self.name = name
        self.version = version
        self.paths = paths

    def __eq__(self, other):
        return (self.name, self.version) == (other.name, other.version)

    def __str__(self, *args, **kwargs):
        return self.name

    @classmethod
    def from_dict(cls, dct):
        try:
            return cls(
                add_on_id=dct['id'],
                name=dct['name'],
                version=dct.get('version', None),
                paths=dct.get('paths', []),
            )
        except KeyError as e:
            raise ValueError('Invalid dict for AddOn') from e


class AddOnDatabase:
    def __init__(self, db_path, add_ons_path, add_ons=None):
        if not add_ons:
            add_ons = []

        if not os.path.exists(db_path):
            raise ValueError('{} is not a file'.format(db_path))

        if not os.path.isdir(add_ons_path):
            raise ValueError('{} does not exist'.format(add_ons_path))

        self.db_path = db_path
        self.add_ons_path = add_ons_path
        self.add_ons = add_ons

    def __len__(self):
        return len(self.add_ons)

    def load(self):
        """Load all installed add-ons from the database file."""
        logging.debug('Loaded database from file "{}".'.format(self.db_path))
        with open(self.db_path) as f:
            try:
                data = json.load(f)
            except json.decoder.JSONDecodeError as e:
                raise RuntimeError('Could not parse database file') from e
            for add_on in data:
                self.add_ons.append(AddOn.from_dict(add_on))

    def save(self):
        """Save the list of installed add-ons back to the database file."""
        logging.debug('Saving database to file "{}".'.format(self.db_path))
        json_data = json.dumps([add_on.__dict__ for add_on in self.add_ons])
        with open(self.db_path, 'w') as f:
            f.write(json_data)

    @staticmethod
    def _fetch_info(add_on_id):
        """Fetch info about an add-on from the server."""
        logging.debug('Fetching info for add-on with ID {}.'.format(add_on_id))
        url = settings.URLS['add_on_details'].format(id=add_on_id)

        try:
            return requests.get(url).json()
        except requests.HTTPError as e:
            raise RuntimeError('Could not fetch add-on for id {}.'.format(add_on_id)) from e

    @staticmethod
    def _download_to_file(url, file_handler):
        """Download the file from the URL to the file handler."""
        logging.debug('Downloading file from URL "{}".'.format(url))
        stream = requests.get(url, stream=True)

        # TODO check for 404

        for chunk in stream.iter_content(chunk_size=1024):
            if chunk:
                file_handler.write(chunk)

    def update(self, add_on):
        """Update an installed add-on."""
        add_on_id = add_on.id
        latest_version_info = self._fetch_info(add_on_id)
        logging.debug('Checking if {} needs an update.'.format(add_on))

        if add_on.version != latest_version_info['latest_version']['version']:
            logging.debug(
                '{} needs an update. Installed version: {}; latest version: {}'.format(
                    add_on,
                    add_on.version,
                    latest_version_info['latest_version']['version']
                )
            )
            self.uninstall(add_on)
            self.install(latest_version_info)

    def update_all(self):
        """Updated all installed add-ons."""
        logging.debug('Checking all add-ons for available updates.')
        for add_on in self.add_ons:
            self.update(add_on)

    def install_by_id(self, add_on_id):
        """Install an add-on with the given ID.

        Fetches the latest version from the server."""
        logging.debug('Fetching data for add-in with ID {} for installation.'.format(add_on_id))
        info = self._fetch_info(add_on_id)
        self.install(info)

    def install(self, latest_version_info):
        """Installs an add-on from add-on info retrieved with _fetch_info."""
        logging.debug('Installing add-on.')
        with tempfile.TemporaryFile(suffix='.zip') as f:
            self._download_to_file(latest_version_info['latest_version']['file'], f)
            logging.debug('Downloaded ZIP file.')

            add_on = AddOn.from_dict(latest_version_info)
            add_on.version = latest_version_info['latest_version']['version']

            logging.debug('Extracting ZIP...')
            with ZipFile(f) as zip_file:
                add_on.paths = zip_file.namelist()
                zip_file.extractall(path=self.add_ons_path)
            logging.debug('ZIP extracted and object updated.')

            logging.debug('Adding {} to database'.format(add_on))
            self.add_ons.append(add_on)

    def uninstall(self, add_on):
        """Uninstalls an add-on by remove related files.

        Does *not* remove add-on settings in the WTF directory."""
        logging.debug('Removing all files of {}'.format(add_on))
        for path in add_on.paths:
            full_path = os.path.join(self.add_ons_path, path)
            try:
                shutil.rmtree(full_path)
            except FileNotFoundError:
                pass

        logging.debug('Removing {} from database'.format(add_on))
        self.add_ons.remove(add_on)
