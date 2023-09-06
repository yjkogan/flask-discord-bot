from typing import Optional, Self
from collections import namedtuple

from flask import current_app

from ..interaction_cache import InteractionCache

MAX_COMPARISONS = 100000

Rateable = namedtuple("Rateable", ["id", "user_id", "name", "rating"])
Comparison = namedtuple("Comparison", ["id", "name", "index", "is_preferred"])


class RatingCalculator:
    def __init__(self, item_being_rated: Rateable, other_items: list[Rateable]):
        self.item_being_rated = item_being_rated
        self.other_items = other_items
        self.comparisons: list[Comparison] = []

    @staticmethod
    def get_cache_key(item: Rateable) -> str:
        return f"{item.user_id}:{item.name}"

    @staticmethod
    def find_for_item(item: Rateable):
        return InteractionCache.get_rating_calculator(
            RatingCalculator.get_cache_key(item)
        )

    def complete(self):
        InteractionCache.remove_rating_calculator(
            RatingCalculator.get_cache_key(self.item_being_rated)
        )

    @classmethod
    def begin_rating(cls, item_being_rated: Rateable, other_items: list[Rateable]) -> Self:
        rating_calulator = cls(item_being_rated, other_items)
        InteractionCache.store_rating_calculator(
            cache_key=RatingCalculator.get_cache_key(item_being_rated),
            rating_calculator=rating_calulator,
        )
        return rating_calulator

    @classmethod
    def continue_rating(cls, item_being_rated: Rateable, comparison: Comparison) -> Optional[Self]:
        rating_calculator = RatingCalculator.find_for_item(item_being_rated)
        if rating_calculator is None:
            return None
        rating_calculator.add_comparison(comparison)
        return rating_calculator

    def add_comparison(self: Self, comparison: Comparison) -> None:
        self.comparisons.append(comparison)

    def get_next_comparison(self: Self) -> Optional[Comparison]:
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

        current_app.logger.info(f"rateable: {self.other_items[idx_for_comparison]}")
        next_item = self.other_items[idx_for_comparison]
        return Comparison(
            id=next_item.id,
            name=next_item.name,
            index=idx_for_comparison,
            is_preferred=None,
        )

    def get_overall_ratings(self: Self) -> list[Rateable]:
        # Make a copy of the list
        rateables = [Rateable(id=r.id, user_id=r.user_id, name=r.name, rating=r.rating) for r in self.other_items]

        # Insert the new item in the appropriate spot in the list
        last_comparison = self.comparisons[-1]
        index_for_artist = (
            last_comparison.index
            if last_comparison.is_preferred
            else last_comparison.index + 1
        )
        rateables.insert(index_for_artist, self.item_being_rated)

        # Recalculate the ratings
        denominator = len(rateables) - 1
        return [
            Rateable(id=r.id, user_id=r.user_id, name=r.name, rating=round((idx / denominator) * 100, 2))
            for (idx, r) in enumerate(rateables)
        ]
