"""python -m wordtally [--top N] [FILE...]: the lines, words and characters of each file.
No file, or "-", reads standard input."""
import argparse
import sys
from collections import Counter

from wordtally.count import counts, words


def whole_number(text):
    # argparse turns this error into a usage message and exit 2.
    try:
        n = int(text)
    except ValueError:
        n = 0
    if n < 1:
        raise argparse.ArgumentTypeError(f"--top takes a whole number of at least 1, not {text!r}")
    return n


def read(path):
    # Standard input is read as bytes, as files are, so that no newline is translated.
    if path == "-":
        return sys.stdin.buffer.read().decode("utf-8")
    with open(path, encoding="utf-8", newline="") as f:
        return f.read()


def main(argv=None):
    parser = argparse.ArgumentParser(prog="python -m wordtally")
    parser.add_argument("--top", metavar="N", type=whole_number,
                        help="also print the N most frequent words")
    parser.add_argument("files", nargs="*", default=["-"])
    args = parser.parse_args(argv)
    rows = []
    tally = Counter()
    failed = False
    for path in args.files:
        try:
            text = read(path)
        except (OSError, UnicodeDecodeError) as e:
            print(f"wordtally: {path}: {getattr(e, 'strerror', None) or e}", file=sys.stderr)
            failed = True
        else:
            rows.append((counts(text), path))
            if args.top:
                tally.update(word.lower() for word in words(text))
    # Files named, not files read: standard input counts as a file named -, as Day 3's stop decided.
    if len(args.files) > 1:
        total = tuple(sum(c[i] for c, _ in rows) for i in range(3))
        rows.append((total, "total"))
    width = max((len(str(n)) for c, _ in rows for n in c), default=1)
    for c, name in rows:
        print(" ".join(str(n).rjust(width) for n in c) + f" {name}")
    if args.top:
        for word, count in sorted(tally.items(), key=lambda kv: (-kv[1], kv[0]))[:args.top]:
            print(f"{count} {word}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
