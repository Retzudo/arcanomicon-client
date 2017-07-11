import settings


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

    def to_database_line(self):
        return '{id}${name}={version}${paths}'.format(
            id=self.id,
            name=self.name,
            version=self.version,
            paths=':'.join(self.paths)
        )


def get_installed_add_ons():
    """Return a list of installed add-ons."""
    add_ons = []
    with open(settings.FILES['database']) as f:
        for line in f.readlines():
            app_info, version_info = line.strip().split('=')
            add_on_id, name = app_info.split('$')
            version, paths = version_info.split('$')

            add_ons.append(AddOn(
                id=add_on_id,
                name=name,
                version=version,
                paths=paths.split(':')
            ))

    return add_ons


def update_installed_add_ons():
    """Update all installed add-ons to the latest version.

    Update the database file if successful."""


def install_add_on(id):
    """Download and extract the latest version of the add-on with the specified ID.

    Update the database file if successful."""


def remove_add_on(id):
    """Remove all directories of an add-on.

     Update the database file if successful."""
