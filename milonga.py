from milonga_app import MilongaApp
from runtime_setup import setup_application_environment


def main():
    setup_application_environment()
    app = MilongaApp()
    app.run()


if __name__ == "__main__":
    main()
