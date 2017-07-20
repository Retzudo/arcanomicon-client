import settings
from addon import AddOnDatabase


def main():
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