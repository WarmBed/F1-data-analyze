"""Optional dependency guards for the F1T toolkit.

This module makes sure that optional third-party packages the project relies on
are either available or replaced with lightweight stand-ins so the application
can continue to operate in a degraded—but functional—state.  The primary goal
is to keep the GUI and CLI entrypoints resilient on developer machines where a
package such as ``prettytable`` might be missing.
"""

from __future__ import annotations

import sys
import types
from typing import Any, Dict, Iterable, List


def _normalize_alignment(value: str | None) -> str:
    """Normalize alignment strings to ``l``/``c``/``r`` tokens."""
    if not value:
        return "l"
    value = value.lower()
    if value in {"l", "left"}:
        return "l"
    if value in {"r", "right"}:
        return "r"
    if value in {"c", "centre", "center"}:
        return "c"
    return "l"


def _create_prettytable_stub() -> types.ModuleType:
    """Create a minimal stub replacement for :mod:`prettytable`."""

    class PrettyTableStub:  # type: ignore[override]
        """Small subset of the PrettyTable API used across the project."""

        def __init__(self) -> None:
            self.field_names: List[str] = []
            self.align: str | Dict[str, str] = "l"
            self._rows: List[List[str]] = []

        # -- data manipulation -------------------------------------------------
        def add_row(self, row: Iterable[Any]) -> None:
            values = [self._stringify(value) for value in row]
            if not self.field_names:
                # Gracefully derive placeholder headers if none were provided.
                self.field_names = [f"Column {index + 1}" for index in range(len(values))]

            if len(values) != len(self.field_names):
                raise ValueError(
                    "Row has a different number of values than the configured field_names"
                )

            self._rows.append(values)

        # -- rendering --------------------------------------------------------
        def _stringify(self, value: Any) -> str:
            if value is None:
                return ""
            return str(value)

        def _column_widths(self) -> List[int]:
            widths: List[int] = []
            for index, name in enumerate(self.field_names):
                width = len(self._stringify(name))
                for row in self._rows:
                    width = max(width, len(row[index]))
                widths.append(width)
            return widths

        def _alignment_map(self) -> List[str]:
            default_align = _normalize_alignment(self.align if isinstance(self.align, str) else "l")
            if isinstance(self.align, dict):
                return [
                    _normalize_alignment(self.align.get(name, default_align))
                    for name in self.field_names
                ]
            return [default_align for _ in self.field_names]

        def _format_cell(self, text: str, width: int, alignment: str) -> str:
            if alignment == "r":
                return text.rjust(width)
            if alignment == "c":
                return text.center(width)
            return text.ljust(width)

        def get_string(self) -> str:
            if not self.field_names:
                return ""

            widths = self._column_widths()
            aligns = self._alignment_map()
            border_segments = ["-" * (width + 2) for width in widths]
            border = "+" + "+".join(border_segments) + "+"

            header_cells = [
                self._format_cell(self._stringify(name), width, "c")
                for name, width in zip(self.field_names, widths)
            ]
            header = "| " + " | ".join(header_cells) + " |"

            body_lines: List[str] = []
            for row in self._rows:
                formatted = [
                    self._format_cell(value, width, align)
                    for value, width, align in zip(row, widths, aligns)
                ]
                body_lines.append("| " + " | ".join(formatted) + " |")

            lines = [border, header, border]
            lines.extend(body_lines)
            lines.append(border)
            return "\n".join(lines)

        # -- python dunder helpers --------------------------------------------
        def __str__(self) -> str:  # pragma: no cover - formatting exercised via print
            return self.get_string()

        def __repr__(self) -> str:  # pragma: no cover - developer convenience only
            return f"PrettyTableStub(rows={len(self._rows)}, columns={len(self.field_names)})"

    stub = types.ModuleType("prettytable")
    stub.PrettyTable = PrettyTableStub
    stub.__all__ = ["PrettyTable"]
    return stub


def ensure_optional_dependencies() -> None:
    """Install lightweight fallbacks for optional third-party packages."""
    try:
        import prettytable  # type: ignore  # noqa: F401
    except ModuleNotFoundError:
        stub = _create_prettytable_stub()
        sys.modules.setdefault("prettytable", stub)
        sys.stderr.write(
            "[WARN] prettytable package not found. Using simplified text-table fallback.\n"
        )
    else:
        # The real library is available; nothing to do.
        return


# Automatically guard optional dependencies when this module is imported.
ensure_optional_dependencies()
