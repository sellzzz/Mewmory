import argparse
import json
from .memory import Memory
from .instinct import simulate


def main():
    parser = argparse.ArgumentParser(description="Mewmory / Kitten-01 local memory baseline")
    parser.add_argument("--db", default="mewmory.db")
    commands = parser.add_subparsers(dest="command", required=True)
    add = commands.add_parser("add")
    for field in ("actor", "place", "cue", "outcome", "text"):
        add.add_argument("--" + field, required=True)
    add.add_argument("--occurred-at")
    commands.add_parser("events")
    rules = commands.add_parser("rules")
    rules.add_argument("--min-support", type=int, default=2)
    recall = commands.add_parser("recall")
    recall.add_argument("query")
    recall.add_argument("--limit", type=int, default=3)
    recall.add_argument("--max-chars", type=int, default=2000)
    trace = commands.add_parser("trace")
    trace.add_argument("ids", type=int, nargs="+")
    demo = commands.add_parser("demo")
    demo.add_argument("--file", default="examples/kitten.json")
    simulation = commands.add_parser("simulate", help="Run a fictional needs-driven experiment")
    simulation.add_argument("--name", default="Kitten-01")
    args = parser.parse_args()
    try:
        with Memory(args.db) as memory:
            if args.command == "add":
                result = {"id": memory.add(**{key: getattr(args, key) for key in
                          ("actor", "place", "cue", "outcome", "text", "occurred_at")})}
            elif args.command == "demo":
                with open(args.file, encoding="utf-8") as source:
                    events = json.load(source)
                # Validate all input before writing; avoid partial demo imports.
                with Memory(":memory:") as validation:
                    for event in events:
                        validation.add(**event)
                result = {"ids": [memory.add(**event) for event in events]}
            elif args.command == "simulate":
                result = simulate(memory, args.name)
            elif args.command == "events":
                result = memory.events()
            elif args.command == "rules":
                result = memory.rules(args.min_support)
            elif args.command == "recall":
                result = memory.recall(args.query, args.limit, args.max_chars)
            else:
                result = memory.trace(args.ids)
        print(json.dumps(result, ensure_ascii=False, indent=None if args.command == "recall" else 2))
    except (ValueError, KeyError, TypeError, OSError) as error:
        parser.exit(2, f"Error: {error}\n")


if __name__ == "__main__":
    main()
