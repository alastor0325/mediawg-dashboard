import sys


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if not args:
        print("usage: python -m mediawg_dashboard.cli {refresh|brief}", file=sys.stderr)
        return 1
    command = args[0]
    if command == "refresh":
        print("refresh: not yet implemented (Phase 0 scaffolding)")
        return 0
    if command == "brief":
        print("brief: not yet implemented (Phase 0 scaffolding)")
        return 0
    print(f"unknown command: {command}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
