"""Azure DevOps Bug Tracker - CLI Entry Point."""

import argparse
import json
import logging
import sys
from datetime import datetime

from src.config import AzureDevOpsConfig
from src.azure_devops_client import AzureDevOpsClient
from src.bug_report_generator import BugReportGenerator

logger = logging.getLogger(__name__)


def print_bug_summary(bugs: list[dict], title: str):
    """Print a formatted bug summary to console."""
    print(f"\n{'=' * 70}")
    print(f"  {title}")
    print(f"  Total: {len(bugs)} bugs")
    print(f"{'=' * 70}")

    if not bugs:
        print("  No bugs found.")
        return

    # Table header
    print(f"  {'ID':<8} {'Priority':<10} {'State':<12} {'Assigned To':<20} {'Title'}")
    print(f"  {'-' * 8} {'-' * 10} {'-' * 12} {'-' * 20} {'-' * 30}")

    for bug in bugs:
        fields = bug.get("fields", {})
        bug_id = bug.get("id", "")
        title_text = fields.get("System.Title", "")[:40]
        state = fields.get("System.State", "")
        priority = fields.get("Microsoft.VSTS.Common.Priority", "-")
        assignee = fields.get("System.AssignedTo", {})
        assignee_name = assignee.get("displayName", "Unassigned") if isinstance(assignee, dict) else "Unassigned"

        print(f"  {bug_id:<8} P{priority:<9} {state:<12} {assignee_name:<20} {title_text}")


def main():
    parser = argparse.ArgumentParser(
        description="Azure DevOps Bug Tracker - Fetch and report bugs",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py --active                   Fetch active bugs
  python main.py --my-bugs                  Fetch bugs assigned to me
  python main.py --p1p2                     Fetch P1 and P2 bugs
  python main.py --sprint                   Fetch current sprint bugs
  python main.py --all --export all         Fetch all bugs with full report
  python main.py --stats                    Show bug statistics
  python main.py --saved-queries            List saved queries
        """,
    )

    # Query options
    query_group = parser.add_mutually_exclusive_group(required=True)
    query_group.add_argument("--all", action="store_true", help="Fetch all bugs")
    query_group.add_argument("--active", action="store_true", help="Fetch active bugs")
    query_group.add_argument("--my-bugs", action="store_true", help="Fetch bugs assigned to me")
    query_group.add_argument("--p1p2", action="store_true", help="Fetch P1 and P2 bugs")
    query_group.add_argument("--sprint", nargs="?", const="current", help="Fetch sprint bugs (optionally specify iteration path)")
    query_group.add_argument("--stats", action="store_true", help="Show bug statistics")
    query_group.add_argument("--saved-queries", action="store_true", help="List saved queries")
    query_group.add_argument("--query-id", type=str, help="Execute a saved query by ID")

    # Export options
    parser.add_argument(
        "--export",
        choices=["csv", "excel", "html", "json", "all"],
        help="Export format",
    )
    parser.add_argument("--output-dir", type=str, help="Output directory override")

    args = parser.parse_args()

    # Initialize configuration
    config = AzureDevOpsConfig()
    if args.output_dir:
        from pathlib import Path
        config.output_dir = Path(args.output_dir)

    if not config.validate():
        print("\nError: Configuration validation failed.")
        print("Please set the required environment variables or create a .env file.")
        print("See .env.example for reference.")
        sys.exit(1)

    # Initialize client and report generator
    client = AzureDevOpsClient(config)
    reporter = BugReportGenerator(config.output_dir)

    try:
        if args.saved_queries:
            queries = client.get_saved_queries()
            print(f"\n{'=' * 70}")
            print("  Saved Queries")
            print(f"{'=' * 70}")
            for q in queries:
                print(f"  [{q['id']}] {q['path']}")
            return

        if args.stats:
            stats = client.get_bug_statistics()
            print(f"\n{'=' * 70}")
            print("  Bug Statistics")
            print(f"{'=' * 70}")
            print(f"\n  Total Bugs: {stats['total']}")
            print(f"\n  By State:")
            for state, count in sorted(stats["by_state"].items()):
                print(f"    {state:<15} {count}")
            print(f"\n  By Priority:")
            for priority, count in sorted(stats["by_priority"].items()):
                print(f"    {priority:<15} {count}")
            print(f"\n  By Sprint (Top 10):")
            sorted_sprints = sorted(stats["by_sprint"].items(), key=lambda x: x[1], reverse=True)[:10]
            for sprint, count in sorted_sprints:
                print(f"    {sprint:<40} {count}")
            print(f"\n  By Assignee (Top 10):")
            sorted_assignees = sorted(stats["by_assignee"].items(), key=lambda x: x[1], reverse=True)[:10]
            for assignee, count in sorted_assignees:
                print(f"    {assignee:<30} {count}")
            return

        # Fetch bugs based on selected option
        if args.all:
            bugs = client.get_all_bugs()
            title = "All Bugs"
        elif args.active:
            bugs = client.get_active_bugs()
            title = "Active Bugs"
        elif args.my_bugs:
            bugs = client.get_bugs_assigned_to_me()
            title = "My Bugs"
        elif args.p1p2:
            bugs = client.get_p1_p2_bugs()
            title = "P1 & P2 Bugs"
        elif args.sprint:
            iteration = args.sprint if args.sprint != "current" else None
            bugs = client.get_sprint_bugs(iteration)
            title = f"Sprint Bugs ({args.sprint})"
        elif args.query_id:
            bugs = client.execute_saved_query(args.query_id)
            title = f"Query Results ({args.query_id})"
        else:
            bugs = []
            title = "Bugs"

        # Display summary
        print_bug_summary(bugs, title)

        # Export if requested
        if args.export and bugs:
            print(f"\n  Generating reports...")
            if args.export == "all":
                reports = reporter.generate_all_reports(bugs, title.lower().replace(" ", "_"))
                for fmt, path in reports.items():
                    print(f"  ✓ {fmt.upper()}: {path}")
            elif args.export == "csv":
                path = reporter.to_csv(bugs)
                print(f"  ✓ CSV: {path}")
            elif args.export == "excel":
                path = reporter.to_excel(bugs)
                print(f"  ✓ Excel: {path}")
            elif args.export == "html":
                path = reporter.to_html(bugs)
                print(f"  ✓ HTML: {path}")
            elif args.export == "json":
                path = reporter.to_json(bugs)
                print(f"  ✓ JSON: {path}")

    except Exception as e:
        logger.error(f"Error: {e}")
        print(f"\nError: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
