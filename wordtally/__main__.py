"""python -m wordtally FILE...: the lines, words and characters of each file."""
import sys

from wordtally.count import counts


def main(argv=None):
    paths = sys.argv[1:] if argv is None else argv
    if not paths:
        print("usage: python -m wordtally FILE...", file=sys.stderr)
        return 2
    rows = []
    failed = False
    for path in paths:
        try:
            with open(path, encoding="utf-8", newline="") as f:
                rows.append((counts(f.read()), path))
        except (OSError, UnicodeDecodeError) as e:
            print(f"wordtally: {path}: {getattr(e, 'strerror', None) or e}", file=sys.stderr)
            failed = True
    # Files named, not files read: Day 3 decides where standard input goes.
    if len(paths) > 1:
        total = tuple(sum(c[i] for c, _ in rows) for i in range(3))
        rows.append((total, "total"))
    width = max((len(str(n)) for c, _ in rows for n in c), default=1)
    for c, name in rows:
        print(" ".join(str(n).rjust(width) for n in c) + f" {name}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
