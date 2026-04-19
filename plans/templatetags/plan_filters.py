from django import template

register = template.Library()

TIME_BASED = {"Plank"}


@register.filter
def format_reps(exercise):
    """Format reps display: time-based exercises show M:SS or X, others show min-max."""
    if exercise.name in TIME_BASED:
        secs = exercise.reps_min
        if secs == 0:
            return "X"
        mins = secs // 60
        remainder = secs % 60
        return f"{mins}:{remainder:02d}"
    return f"{exercise.reps_min}-{exercise.reps_max}"


@register.filter
def get_intensity(muscle_data, muscle_name):
    """Get intensity value for a muscle from the session muscle data dict."""
    if not muscle_data:
        return 0
    return muscle_data.get(muscle_name, 0)


def _lerp_color(c1, c2, t):
    """Linearly interpolate between two hex colors."""
    r1, g1, b1 = int(c1[1:3], 16), int(c1[3:5], 16), int(c1[5:7], 16)
    r2, g2, b2 = int(c2[1:3], 16), int(c2[3:5], 16), int(c2[5:7], 16)
    r = int(r1 + (r2 - r1) * t)
    g = int(g1 + (g2 - g1) * t)
    b = int(b1 + (b2 - b1) * t)
    return f"#{r:02x}{g:02x}{b:02x}"


def _muscle_color(val):
    """
    Monochrome cyan — 3 tiers, matches sci-fi theme.
    Darker = less active, brighter = more active.
    Body outline always visible underneath.
    """
    if val <= 5:
        return "#0a1628", 0.0       # invisible

    if val <= 30:
        # Low: dark muted cyan — stabilizers
        return "#122a38", 0.45

    if val <= 65:
        # Medium: teal — secondary movers
        return "#1a8a8c", 0.60

    # High: bright cyan glow — primary movers
    return "#4df0e0", 0.90


@register.filter
def muscle_opacity(muscle_data, muscle_name):
    """Return SVG fill-opacity string."""
    if not muscle_data:
        return "0"
    val = muscle_data.get(muscle_name, 0)
    _, opacity = _muscle_color(val)
    return f"{opacity:.2f}"


@register.filter
def muscle_fill(muscle_data, muscle_name):
    """Return SVG fill color hex string."""
    if not muscle_data:
        return "#1a3a5c"
    val = muscle_data.get(muscle_name, 0)
    color, _ = _muscle_color(val)
    return color


@register.filter
def muscle_style(muscle_data, muscle_name):
    """Return inline style string for SVG: fill + opacity."""
    if not muscle_data:
        return "fill:#1a3a5c;fill-opacity:0"
    val = muscle_data.get(muscle_name, 0)
    color, opacity = _muscle_color(val)
    return f"fill:{color};fill-opacity:{opacity:.2f}"


@register.filter
def get_item(dictionary, key):
    """Generic dict lookup for templates."""
    if not dictionary:
        return None
    return dictionary.get(key)
