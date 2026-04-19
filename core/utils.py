def clamp_int(value, min_val, max_val, default):
    """Parse value as int and clamp to [min_val, max_val]. Returns default on error."""
    try:
        return max(min_val, min(max_val, int(value)))
    except (ValueError, TypeError):
        return default
