ACTIVITY_TYPE_ALIASES = {
    "running": {
        "run",
        "running",
        "trailrun",
        "treadmill",
        "virtualrun",
    },
    "cycling": {
        "cycling",
        "ride",
        "virtualride",
        "gravelride",
        "mountainbikeride",
        "emountainbikeride",
        "ebikeride",
        "handcycle",
        "velomobile",
    },
}


def normalize_activity_type(value):
    return "".join(
        character for character in str(value or "").lower() if character.isalnum()
    )


def normalize_activity_types(activity_types):
    normalized = set()
    for activity_type in activity_types or []:
        key = normalize_activity_type(activity_type)
        normalized.add(key)
        normalized.update(ACTIVITY_TYPE_ALIASES.get(key, set()))
    return normalized


def activity_type(activity):
    for field in ("sport_type", "subtype", "type"):
        value = normalize_activity_type(getattr(activity, field, ""))
        if value:
            return value
    return ""


def activity_category(value):
    normalized = normalize_activity_type(value)
    for category, aliases in ACTIVITY_TYPE_ALIASES.items():
        if normalized == category or normalized in aliases:
            return category
    return None


def activity_matches_types(activity, activity_types):
    accepted_types = normalize_activity_types(activity_types)
    if not accepted_types:
        return True

    categories = {
        category
        for field in ("type", "sport_type", "subtype")
        if (category := activity_category(getattr(activity, field, "")))
    }
    if len(categories) > 1:
        return False
    return activity_type(activity) in accepted_types
