#!/usr/bin/env python3
"""Entry point: python scripts/session/cli.py <command> [args]"""

import argparse
import sys


def main():
    parser = argparse.ArgumentParser(
        prog="session",
        description="Session-driven development CLI",
    )
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # work-new
    p = subparsers.add_parser("work-new", help="Create a new work item")
    p.add_argument("--type", required=True, help="Work item type")
    p.add_argument("--title", required=True, help="Work item title")
    p.add_argument("--priority", required=True, help="Priority level")
    p.add_argument("--dependencies", nargs="*", default=[], help="Dependency IDs")
    p.add_argument("--urgent", action="store_true", help="Mark as urgent")

    # work-list
    p = subparsers.add_parser("work-list", help="List work items")
    p.add_argument("--status", help="Filter by status")
    p.add_argument("--type", help="Filter by type")
    p.add_argument("--milestone", help="Filter by milestone")

    # work-show
    p = subparsers.add_parser("work-show", help="Show work item details")
    p.add_argument("id", help="Work item ID")

    # work-update
    p = subparsers.add_parser("work-update", help="Update a work item")
    p.add_argument("id", help="Work item ID")
    p.add_argument("--status", help="New status")
    p.add_argument("--priority", help="New priority")
    p.add_argument("--milestone", help="Set milestone")
    p.add_argument("--add-dependency", help="Add a dependency")
    p.add_argument("--remove-dependency", help="Remove a dependency")
    p.add_argument("--set-urgent", action="store_true", help="Mark as urgent")
    p.add_argument("--clear-urgent", action="store_true", help="Clear urgent flag")

    # work-delete
    p = subparsers.add_parser("work-delete", help="Delete a work item")
    p.add_argument("id", help="Work item ID")
    p.add_argument("--with-spec", action="store_true", help="Also delete spec file")

    # work-next
    p = subparsers.add_parser("work-next", help="Get next recommended work items")
    p.add_argument("--limit", type=int, default=5, help="Number of items to show")

    # work-graph
    p = subparsers.add_parser("work-graph", help="Visualize dependency graph")
    p.add_argument("--critical-path", action="store_true", help="Show critical path")
    p.add_argument("--bottlenecks", action="store_true", help="Show bottlenecks")
    p.add_argument("--stats", action="store_true", help="Show statistics")

    # start
    p = subparsers.add_parser("start", help="Start a session")
    p.add_argument("id", help="Work item ID")

    # end
    p = subparsers.add_parser("end", help="End current session")
    p.add_argument(
        "--complete",
        action="store_const",
        const="completed",
        dest="status",
        help="Mark as completed",
    )
    p.add_argument(
        "--incomplete",
        action="store_const",
        const="incomplete",
        dest="status",
        help="Mark as incomplete",
    )
    p.add_argument("--summary", default="", help="Session summary")

    # status
    subparsers.add_parser("status", help="Show session status")

    # validate
    p = subparsers.add_parser("validate", help="Run quality gates")
    p.add_argument("--fix", action="store_true", help="Auto-fix issues")
    p.add_argument(
        "--scope", choices=["backend", "frontend"], help="Limit to one stack"
    )

    # learn-add
    p = subparsers.add_parser("learn-add", help="Add a learning")
    p.add_argument("--content", required=True, help="Learning content")
    p.add_argument("--category", required=True, help="Learning category")
    p.add_argument("--tags", nargs="*", default=[], help="Tags")
    p.add_argument("--session", type=int, help="Session number")

    # learn-show
    p = subparsers.add_parser("learn-show", help="Show learnings")
    p.add_argument("--category", help="Filter by category")
    p.add_argument("--tag", help="Filter by tag")
    p.add_argument("--session", type=int, help="Filter by session number")

    # learn-search
    p = subparsers.add_parser("learn-search", help="Search learnings")
    p.add_argument("query", help="Search query")

    # learn-curate
    p = subparsers.add_parser("learn-curate", help="Curate (deduplicate) learnings")
    p.add_argument("--dry-run", action="store_true", help="Preview without changes")
    p.add_argument("--threshold", type=float, default=0.6, help="Similarity threshold")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    # Route to the appropriate module
    if args.command == "work-new":
        from .work_items import create

        create(args.type, args.title, args.priority, args.dependencies, args.urgent)

    elif args.command == "work-list":
        from .work_items import list_items

        list_items(args.status, args.type, args.milestone)

    elif args.command == "work-show":
        from .work_items import show

        show(args.id)

    elif args.command == "work-update":
        from .work_items import update

        update(
            args.id,
            status=args.status,
            priority=args.priority,
            milestone=args.milestone,
            add_dependency=args.add_dependency,
            remove_dependency=args.remove_dependency,
            set_urgent=args.set_urgent,
            clear_urgent=args.clear_urgent,
        )

    elif args.command == "work-delete":
        from .work_items import delete

        delete(args.id, args.with_spec)

    elif args.command == "work-next":
        from .work_items import next_items

        next_items(args.limit)

    elif args.command == "work-graph":
        from .work_items import render_graph

        render_graph(args.critical_path, args.bottlenecks, args.stats)

    elif args.command == "start":
        from .session import start

        start(args.id)

    elif args.command == "end":
        from .session import end

        end(args.status or "completed", args.summary)

    elif args.command == "status":
        from .session import show_status

        show_status()

    elif args.command == "validate":
        from .session import validate

        validate(args.fix, args.scope)

    elif args.command == "learn-add":
        from .learnings import add

        add(args.content, args.category, args.tags, args.session)

    elif args.command == "learn-show":
        from .learnings import show

        show(args.category, args.tag, args.session)

    elif args.command == "learn-search":
        from .learnings import search

        search(args.query)

    elif args.command == "learn-curate":
        from .learnings import curate

        curate(args.dry_run, args.threshold)


if __name__ == "__main__":
    main()
