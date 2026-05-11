from __future__ import annotations

import inspect
from datetime import datetime
from pathlib import Path

_APP_ROOT = Path(__file__).resolve().parent


def workflow_log(layer: str, action: str, details: str = "") -> None:
    frame = inspect.currentframe()
    caller = frame.f_back if frame is not None else None

    if caller is None:
        file_name = "<unknown>"
        function_name = "<unknown>"
    else:
        caller_path = Path(caller.f_code.co_filename).resolve()
        try:
            file_name = caller_path.relative_to(_APP_ROOT).as_posix()
        except ValueError:
            file_name = caller_path.name
        function_name = caller.f_code.co_name

    timestamp = datetime.now().strftime("%H:%M:%S")
    suffix = f" | {details}" if details else ""
    print(
        f"[{timestamp}] {layer:<10} | {file_name:<45} | {function_name:<28} | {action}{suffix}",
        flush=True,
    )
