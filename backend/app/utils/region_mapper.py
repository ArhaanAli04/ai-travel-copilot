"""
Region mapper utility

Maps ISO country codes (returned by disruption_agent's airport lookup)
to regulation regions used as MongoDB lookup keys.
"""

# All 27 EU member states (ISO alpha-2)
EU_COUNTRIES = {
    "AT", "BE", "BG", "HR", "CY", "CZ", "DK", "EE", "FI", "FR",
    "DE", "GR", "HU", "IE", "IT", "LV", "LT", "LU", "MT", "NL",
    "PL", "PT", "RO", "SK", "SI", "ES", "SE"
}


def get_region_from_country(country_code: str) -> str:
    """
    Map ISO alpha-2 country code to a regulation region key.

    Args:
        country_code: ISO alpha-2 country code (e.g., "US", "FR", "GB", "IN")

    Returns:
        Region key: "EU", "US", "UK", "IN", "CA", "AU", "AE", or "GENERAL"

    Examples:
        >>> get_region_from_country("FR")  # France → EU
        'EU'
        >>> get_region_from_country("GB")  # Great Britain → UK
        'UK'
        >>> get_region_from_country("US")
        'US'
        >>> get_region_from_country("JP")  # Japan → GENERAL
        'GENERAL'
    """
    if not country_code:
        return "GENERAL"

    code = country_code.strip().upper()

    if code in EU_COUNTRIES:
        return "EU"

    region_map = {
        "GB": "UK",
        "US": "US",
        "IN": "IN",
        "CA": "CA",
        "AU": "AU",
        "AE": "AE",
    }

    return region_map.get(code, "GENERAL")
