import settings
import logging
from addon import AddOnDatabase


def main():
    logging.basicConfig(level=logging.DEBUG)
    db = AddOnDatabase(
        db_path=settings.FILES['database'],
        add_ons_path=settings.CONFIG['InterfaceDir']
    )

    db.load()
    db.update_all()
    db.save()

    # db.uninstall(db.add_ons[0])


if __name__ == '__main__':
    main()