"""Command-line entry points for data profiling and supervised workflow launch."""
from __future__ import annotations

import argparse
import json
import uuid

from .connectors import business_system_summary
from .workflow import run_graph_start


def main() -> None:
    parser = argparse.ArgumentParser(prog="agentic-ml", description="Supervised agentic ML department demo")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("profile", help="Discover and profile synthetic business systems")
    run = sub.add_parser("run", help="Start a supervised ML workflow")
    run.add_argument("--objective", choices=["customer_churn", "lead_conversion"], required=True)
    run.add_argument("--instructions", default="")
    args = parser.parse_args()

    if args.command == "profile":
        print(json.dumps(business_system_summary(), indent=2, default=str))
        return

    state = {
        "run_id": str(uuid.uuid4()),
        "objective": args.objective,
        "supervisor_instructions": args.instructions,
    }
    print(json.dumps(run_graph_start(state), indent=2, default=str))


if __name__ == "__main__":
    main()
