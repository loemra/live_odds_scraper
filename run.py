import sys

from packages.util.setup_logging import setup_root_logging

logger = setup_root_logging()


def run():
    if len(sys.argv) > 1:
        eval(sys.argv[1])()
    else:
        print("Must provide argument to run.")


if __name__ == "__main__":
    run()
