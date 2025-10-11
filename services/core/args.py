from argparse import ArgumentParser, Namespace


def get_args() -> Namespace:
    parser = ArgumentParser(description="")
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="enable verbose output"
    )
    parser.add_argument(
        "--skip-network-check",
        action="store_true",
        help="set to debug without proper connection"
    )
    parser.add_argument(
        "--logfile",
        default=None,
        type=str,
        help="log to this file"
    )
    parser.add_argument(
        "-d", "--debug",
        action="store_true",
        help="enable logger debug output"
    )
    parser.add_argument(
        "--test",
        action="store_true",
        help="Debugging run"
    )
    mutually_app_group = parser.add_mutually_exclusive_group(required=True)
    mutually_app_group.add_argument(
        "--web",
        action="store_true",
        help="Runs the GUI as flask web server"
    )
    mutually_app_group.add_argument(
        "--qt",
        action="store_true",
        help="Runs the GUI as QT App"
    )
    mutually_app_group.add_argument(
        "--test-web",
        action="store_true",
        help="Run the webservice without further services"
    )
    return parser.parse_args()
