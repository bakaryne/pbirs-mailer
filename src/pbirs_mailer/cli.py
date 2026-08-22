"""Command-line interface."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .app import run
from .config import ConfigurationError, load_config


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="pbirs-mailer",
        description="Capture des pages PBIRS et les envoie par email.",
    )
    parser.add_argument("--config", type=Path, default=Path("config.json"))
    parser.add_argument("--dry-run", action="store_true", help="Valide sans ouvrir le navigateur.")
    parser.add_argument(
        "--no-send",
        action="store_true",
        help="Crée les captures sans envoyer de mail.",
    )
    parser.add_argument("--headed", action="store_true", help="Affiche Edge pour le diagnostic.")
    parser.add_argument(
        "--subscription",
        action="append",
        default=[],
        metavar="NOM",
        help="Traite uniquement cet abonnement (option répétable).",
    )
    parser.add_argument("--verbose", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        config = load_config(args.config)
        return run(
            config,
            dry_run=args.dry_run,
            no_send=args.no_send,
            headed=args.headed,
            requested_names=tuple(args.subscription),
            verbose=args.verbose,
        )
    except (ConfigurationError, ValueError) as exc:
        print(f"Erreur de configuration : {exc}", file=sys.stderr)
        return 2
