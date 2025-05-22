from enum import Enum

class SortOption(str, Enum):
    RELEVANCE = "RELEVANCE"
    DISTANCE = "DISTANCE"
    PRICE = "PRICE"
    RATING = "RATING"

class ItemCategory(str, Enum):
    MEAL = "MEAL"
    BAKED_GOODS = "BAKED_GOODS"
    GROCERIES = "GROCERIES"
    PET_FOOD = "PET_FOOD"
    FLOWERS_PLANTS = "FLOWERS_PLANTS"
    OTHER = "OTHER"

class DietCategory(str, Enum):
    VEGETARIAN = "VEGETARIAN"
    VEGAN = "VEGAN"