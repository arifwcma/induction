import json
from pathlib import Path

from app.config import get_settings


OBJECTIVES_FILENAME = "objectives.json"


def load_category_objectives() -> dict[str, str]:
    """Map each induction category folder to its objective.

    The objectives file is the single source of truth for which top-level
    folders under ``documents/`` are real induction categories. Anything not
    listed here (for example a holding folder) is not ingested.
    """
    documents_dir = Path(get_settings().documents_dir)
    objectives_path = documents_dir / OBJECTIVES_FILENAME
    if not objectives_path.exists():
        return {}
    return json.loads(objectives_path.read_text(encoding="utf-8"))
