from typing import Optional, Self

from flask import current_app

from ..interaction_cache import InteractionCache
from ..models.rating import Rating

MAX_COMPARISONS = 100000

# TODO: Make this an abstract base class
class _Comparison:
    def __init__(self, id: int, index: int):
        self.id = id
        self.index = index

class ComparisonToSend(_Comparison):
    # Same constructor as the parent, but can also take a name that we can then send to the user
    def __init__(self, id: int, index: int, name: str):
        super().__init__(id, index)
        self.name = name

class CompletedComparison(_Comparison):
    # Same constructor as Comparison, but can also take is_preferred
    def __init__(self, id: int, index: int, is_preferred: bool):
        super().__init__(id, index)
        self.is_preferred = is_preferred

class RatingCalculator:
    def __init__(self, item_being_rated: Rating, other_items: list[Rating]):
        self.item_being_rated = item_being_rated
        self.other_items = other_items
        self.comparisons: list[CompletedComparison] = []

    @staticmethod
    def get_cache_key(item: Rating) -> str:
        return f"{item.user_id}:{item.id}"

    @staticmethod
    def find_for_item(item: Rating):
        return InteractionCache.get_rating_calculator(
            RatingCalculator.get_cache_key(item)
        )

    def complete(self):
        InteractionCache.remove_rating_calculator(
            RatingCalculator.get_cache_key(self.item_being_rated)
        )

    @classmethod
    def begin_rating(cls, item_being_rated: Rating, other_items: list[Rating]) -> Self:
        rating_calulator = cls(item_being_rated, other_items)
        InteractionCache.store_rating_calculator(
            cache_key=RatingCalculator.get_cache_key(item_being_rated),
            rating_calculator=rating_calulator,
        )
        return rating_calulator

    @classmethod
    def continue_rating(cls, item_being_rated: Rating, comparison: CompletedComparison) -> Optional[Self]:
        rating_calculator = RatingCalculator.find_for_item(item_being_rated)
        if rating_calculator is None:
            return None
        rating_calculator.add_comparison(comparison)
        return rating_calculator

    def add_comparison(self: Self, comparison: CompletedComparison) -> None:
        self.comparisons.append(comparison)

    def get_next_comparison(self: Self) -> Optional[ComparisonToSend]:
        if not self.other_items:
            return None

        if len(self.comparisons) >= MAX_COMPARISONS:
            return None
        lowest_possible_idx = 0
        highest_possible_idx = len(self.other_items) - 1
        idx_for_comparison = (
            int((highest_possible_idx - lowest_possible_idx) / 2) + lowest_possible_idx
        )
        current_app.logger.info(
            f"lowest: {lowest_possible_idx}, highest: {highest_possible_idx}, comparison: {idx_for_comparison}"
        )
        for comparison in self.comparisons:
            if comparison.is_preferred:
                highest_possible_idx = idx_for_comparison - 1
            else:
                lowest_possible_idx = idx_for_comparison + 1

            if highest_possible_idx < lowest_possible_idx:
                return None
            idx_for_comparison = (
                int((highest_possible_idx - lowest_possible_idx) / 2)
                + lowest_possible_idx
            )

            current_app.logger.info(
                f"is_preferred: {comparison.is_preferred}, lowest: {lowest_possible_idx}, highest: {highest_possible_idx}, comparison: {idx_for_comparison}"
            )

        next_item = self.other_items[idx_for_comparison]
        current_app.logger.info(f"next item: {self.other_items[idx_for_comparison]}")
        return ComparisonToSend(
            id=next_item.id,
            name=next_item.name,
            index=idx_for_comparison,
        )

    def get_overall_ratings(self: Self) -> list[Rating]:
        # Make a copy of the list
        ratings = self.other_items[:]

        # Insert the new item in the appropriate spot in the list
        last_comparison = self.comparisons[-1]
        index_for_rating = (
            last_comparison.index
            if last_comparison.is_preferred
            else last_comparison.index + 1
        )
        ratings.insert(index_for_rating, self.item_being_rated)

        # Recalculate the ratings
        denominator = len(ratings) - 1
        return [
            r.update_value_property(round((idx / denominator) * 100, 2))
            for (idx, r) in enumerate(ratings)
        ]
