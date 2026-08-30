"""Allow ``python -m pbirs_mailer`` to run the existing CLI."""

from __future__ import annotations

from .cli import main

if __name__ == "__main__":
    raise SystemExit(main())
