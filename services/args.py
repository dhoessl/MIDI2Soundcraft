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
        "--colored-log",
        action="store_true",
        help="Output Log with colors to stdout"
    )

    return parser.parse_args()
