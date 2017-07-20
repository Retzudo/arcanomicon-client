import json
import os
import shutil
import tempfile
from zipfile import ZipFile

import logging
import requests

import settings


class BaseAddOn:
    def __init__(self, add_on_id, name, version):
        self.id = add_on_id
        self.name = name
        self.version = version

    def __str__(self, *args, **kwargs):
        return self.name

    def __eq__(self, other):
        return (self.name, self.version) == (other.name, other.version)


class InstalledAddOn(BaseAddOn):
    def __init__(self, add_on_id, name, version, paths=None):
        super().__init__(add_on_id, name, version)
        self.paths = paths

    @classmethod
    def from_dict(cls, dct):
        try:
            return cls(
                add_on_id=dct.get('id'),
                name=dct.get('name'),
                version=dct.get('version', None),
                paths=dct.get('paths', []),
            )
        except KeyError as e:
            raise ValueError('Invalid dict for AddOn') from e

    @classmethod
    def from_remote_add_on(cls, remote_add_on):
        return cls(
            add_on_id=remote_add_on.id,
            name=remote_add_on.name,
            version=remote_add_on.latest_version.get('version'),
            paths=[]
        )


class RemoteAddOn(BaseAddOn):
    def __init__(self, add_on_id, name, version, latest_version, logo, short_description, created, updated):
        super().__init__(add_on_id, name, version)
        self.updated = updated
        self.created = created
        self.short_description = short_description
        self.logo = logo
        self.latest_version = latest_version

    @classmethod
    def from_dict(cls, dct):
        return cls(
            add_on_id=dct.get('id'),
            name=dct.get('name'),
            version=dct.get('latest_version').get('version'),
            latest_version=dct.get('latest_version'),
            logo=dct.get('logo'),
            short_description=dct.get('short_description'),
            created=dct.get('created'),
            updated=dct.get('updated'),
        )


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
                self.add_ons.append(InstalledAddOn.from_dict(add_on))

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
            data = requests.get(url).json()
        except requests.HTTPError as e:
            raise RuntimeError('Could not fetch add-on for id {}.'.format(add_on_id)) from e

        return RemoteAddOn.from_dict(data)

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
        logging.debug('Checking if {} needs an update.'.format(add_on))
        add_on_id = add_on.id
        remote_add_on = self._fetch_info(add_on_id)

        if add_on != remote_add_on:
            logging.debug(
                '{} needs an update. Installed version: {}; latest version: {}'.format(
                    add_on,
                    add_on.version,
                    remote_add_on.version,
                )
            )
            self.uninstall(add_on)
            self.install(remote_add_on)
        else:
            logging.debug('{} does not need an update'.format(add_on))

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

    def install(self, remote_add_on):
        """Installs an add-on from add-on info retrieved with _fetch_info."""
        logging.debug('Installing add-on.')
        with tempfile.TemporaryFile(suffix='.zip') as f:
            self._download_to_file(remote_add_on.latest_version.get('file'), f)
            logging.debug('Downloaded ZIP file.')

            add_on = InstalledAddOn.from_remote_add_on(remote_add_on)

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


class FavouritesAddOnDatabase(AddOnDatabase):
    def __init__(self, db_path, add_ons_path, add_ons=None, favourites=None):
        super().__init__(db_path, add_ons_path, add_ons)
        if not favourites:
            favourites = []

        self.favourites = favourites

    def _fetch_favourites(self):
        pass

    def install_favourites(self):
        pass
