from cyclopts import App

CLI: App = App()


@CLI.default
def main() -> None:
    print("Hello World")


def serve() -> None:
    CLI()
