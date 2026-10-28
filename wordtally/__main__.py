"""python -m wordtally FILE...: the number of words in each file."""
import sys

from wordtally.count import count_words


def main(argv=None):
    paths = sys.argv[1:] if argv is None else argv
    if not paths:
        print("usage: python -m wordtally FILE...", file=sys.stderr)
        return 2
    for path in paths:
        with open(path, encoding="utf-8") as f:
            print(f"{count_words(f.read())} {path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
