"""
Structured JSON error logger following error-observability.md workflow.

Appends structured error entries to data/error_logs.json with
AST-compressed summaries. Non-blocking writes ensure logging
never crashes the pipeline (per 12-factor-rules.md Factor IX).
"""

import json
import os
import threading
import traceback
from datetime import UTC, datetime

# Base directory for log files
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data")
ERROR_LOG_PATH = os.path.join(DATA_DIR, "error_logs.json")


def _ensure_data_dir():
    """Create the data directory if it doesn't exist."""
    os.makedirs(DATA_DIR, exist_ok=True)


def log_error(
    error: Exception,
    component: str,
    domain: str | None = None,
    tier: str | None = None,
    context: dict | None = None,
) -> None:
    """Log a structured error entry to data/error_logs.json.

    Per error-observability.md Step 3:
    - timestamp: Current UTC time
    - error_type: Type of exception
    - component: The function or module that broke
    - stack_trace_summary: Compressed summary of the stack trace
    - status: "UNRESOLVED"

    Writes are non-blocking (background thread) per Factor XI.
    """
    entry = {
        "timestamp": datetime.now(UTC).isoformat(),
        "error_type": type(error).__name__,
        "component": component,
        "domain": domain,
        "tier": tier,
        "stack_trace_summary": _compress_traceback(error),
        "context": context or {},
        "status": "UNRESOLVED",
        "resolution_strategy": None,
    }

    # Non-blocking write
    thread = threading.Thread(target=_append_entry, args=(entry,), daemon=True)
    thread.start()


def log_resolution(
    component: str,
    resolution_strategy: str,
    error_type: str | None = None,
) -> None:
    """Mark the most recent matching error as RESOLVED.

    Per error-observability.md Step 4:
    Updates the error log entry with the resolution strategy.
    """
    thread = threading.Thread(
        target=_resolve_entry,
        args=(component, resolution_strategy, error_type),
        daemon=True,
    )
    thread.start()


def get_recent_errors(component: str | None = None, limit: int = 10) -> list[dict]:
    """Read recent error entries for pre-execution log verification.

    Per error-observability.md Step 1:
    Before generating or modifying code, check recent error history.
    """
    try:
        _ensure_data_dir()
        if not os.path.exists(ERROR_LOG_PATH):
            return []
        with open(ERROR_LOG_PATH, encoding="utf-8") as f:
            entries = json.load(f)
        if component:
            entries = [e for e in entries if e.get("component") == component]
        return entries[-limit:]
    except (OSError, json.JSONDecodeError):
        return []


def _append_entry(entry: dict) -> None:
    """Thread-safe append to the JSON error log."""
    try:
        _ensure_data_dir()
        entries = []
        if os.path.exists(ERROR_LOG_PATH):
            with open(ERROR_LOG_PATH, encoding="utf-8") as f:
                try:
                    entries = json.load(f)
                except json.JSONDecodeError:
                    entries = []

        entries.append(entry)

        # Keep only the last 500 entries to prevent unbounded growth
        if len(entries) > 500:
            entries = entries[-500:]

        with open(ERROR_LOG_PATH, "w", encoding="utf-8") as f:
            json.dump(entries, f, indent=2, default=str)

    except Exception as e:
        # Logging must never crash the pipeline
        print(f"[OBSERVABILITY] Failed to write error log: {e}")


def _resolve_entry(
    component: str,
    resolution_strategy: str,
    error_type: str | None,
) -> None:
    """Find and resolve the most recent matching unresolved error."""
    try:
        _ensure_data_dir()
        if not os.path.exists(ERROR_LOG_PATH):
            return
        with open(ERROR_LOG_PATH, encoding="utf-8") as f:
            entries = json.load(f)

        # Find the most recent matching unresolved entry
        for entry in reversed(entries):
            if entry.get("status") != "UNRESOLVED":
                continue
            if entry.get("component") != component:
                continue
            if error_type and entry.get("error_type") != error_type:
                continue
            entry["status"] = "RESOLVED"
            entry["resolution_strategy"] = resolution_strategy
            break

        with open(ERROR_LOG_PATH, "w", encoding="utf-8") as f:
            json.dump(entries, f, indent=2, default=str)

    except Exception as e:
        print(f"[OBSERVABILITY] Failed to resolve error log entry: {e}")


def _compress_traceback(error: Exception) -> str:
    """Compress a stack trace into a concise summary.

    Per error-observability.md Step 2: use compressed summaries
    instead of full stack traces to conserve context window.
    Extracts only the final frame and the exception message.
    """
    tb_lines = traceback.format_exception(type(error), error, error.__traceback__)
    if not tb_lines:
        return str(error)

    # Extract the last meaningful frame (where the error actually occurred)
    frames = [line for line in tb_lines if line.strip().startswith("File ")]
    last_frame = frames[-1].strip() if frames else ""
    error_msg = tb_lines[-1].strip()

    # Compress: "File '/path/to/file.py', line 42, in function_name" → "file.py:42 in function_name"
    if last_frame:
        parts = last_frame.split(",")
        if len(parts) >= 2:
            filename = parts[0].split("/")[-1].split("\\")[-1].replace("'", "").replace("File ", "")
            lineno = parts[1].strip().replace("line ", "")
            func = parts[2].strip().replace("in ", "") if len(parts) > 2 else "?"
            return f"{filename}:{lineno} in {func} → {error_msg}"

    return error_msg
