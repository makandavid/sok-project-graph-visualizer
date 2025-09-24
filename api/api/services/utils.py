import json
from datetime import date, datetime
from typing import Any

class DateTimeEncoder(json.JSONEncoder):
    """JSON encoder that parses datetime or date objects into a ISO string."""
    def default(self, obj: Any) -> str:
        if isinstance(obj, (datetime, date)):
            return obj.isoformat()
        return super().default(obj)
    
def sanitize_dates(obj: Any) -> Any:
    """Recursively convert date/datetime to ISO strings. Leaves other values intact."""
    if isinstance(obj, (date, datetime)):
        return obj.isoformat()
    if isinstance(obj, dict):
        return {k: sanitize_dates(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple, set)):
        return [sanitize_dates(v) for v in obj]
    return obj    