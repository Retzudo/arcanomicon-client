from addon import get_installed_add_ons


def main():
    add_ons = get_installed_add_ons()
    print('Add-ons:', add_ons)

    for add_on in add_ons:
        print('DB line:', add_on.to_database_line())


if __name__ == '__main__':
    main()