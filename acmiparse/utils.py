def to_float(s: str, default: float = None) -> float:
    try:
        return float(s.strip()) if s.strip() else default
    except (ValueError, TypeError):
        return default