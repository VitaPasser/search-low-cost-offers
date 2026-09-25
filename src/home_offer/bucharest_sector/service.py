from functools import cache

from src.home_offer.bucharest_sector.model import BucharestSector


def string_to_bucharest_sector(sector: str) -> BucharestSector:
    sector_cleaned = sector.strip().lower()
    match sector_cleaned:
        case "ultracentral": return BucharestSector.ULTRACENTRAL
        case "sector 1": return BucharestSector.SECTOR_1
        case "sector 2": return BucharestSector.SECTOR_2
        case "sector 3": return BucharestSector.SECTOR_3
        case "sector 4": return BucharestSector.SECTOR_4
        case "sector 5": return BucharestSector.SECTOR_5
        case "sector 6": return BucharestSector.SECTOR_6
    raise ValueError(f"Invalid sector name: {sector}. Cleaned version: {sector_cleaned}")


@cache
def comment_for_property_model():
    list_enum_str: list[str] = []
    for element in BucharestSector:
        list_enum_str.append(f"{element.value} - {element.name.replace('-', ' ')}")
    return ", ".join(list_enum_str)
