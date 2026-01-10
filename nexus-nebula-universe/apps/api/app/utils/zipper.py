from __future__ import annotations

import io
import zipfile
from typing import Dict


def make_zip_bytes(files: Dict[str, str]) -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", compression=zipfile.ZIP_DEFLATED) as z:
        for path, content in files.items():
            safe_path = path.lstrip("/").replace("..", "_")
            z.writestr(safe_path, content)
    return buf.getvalue()
