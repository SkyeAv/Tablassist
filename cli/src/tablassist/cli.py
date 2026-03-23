from cyclopts import App

CLI: App = App()


@CLI.command
def main() -> None:
    print("Hello World")


def serve() -> None:
    CLI()
