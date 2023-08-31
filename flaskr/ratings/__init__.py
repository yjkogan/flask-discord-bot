from flask import current_app

from ..interaction_cache import InteractionCache


class RatingCalculator:
    def __init__(self, item_being_rated, other_items):
        self.item_being_rated = item_being_rated
        self.other_items = other_items
        self.comparisons = []
        InteractionCache.store_rating_calculator(
            cache_key=RatingCalculator.get_cache_key(item_being_rated),
            rating_calculator=self,
        )

    def get_cache_key(item):
        return f"{item.user_id}:{item.name}"

    def find_for_item(item):
        return InteractionCache.get_rating_calculator(RatingCalculator.get_cache_key(item))

    def complete(self):
        InteractionCache.remove_rating_calculator(
            RatingCalculator.get_cache_key(self.item_being_rated)
        )

    @classmethod
    def begin_rating(cls, item_being_rated, other_items):
        return cls(item_being_rated, other_items)

    @classmethod
    def continue_rating(cls, item_being_rated, comparison):
        rating_calculator = RatingCalculator.find_for_item(item_being_rated)
        if rating_calculator is None:
            return None
        rating_calculator.add_comparison(comparison)
        return rating_calculator

    def add_comparison(self, comparison):
        self.comparisons.append(comparison)

    def get_next_comparison(self):
        if not self.other_items:
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
                highest_possible_idx = idx_for_comparison
            else:
                lowest_possible_idx = idx_for_comparison
            if highest_possible_idx == lowest_possible_idx:
                return None
            new_idx_for_comparison = (
                int((highest_possible_idx - lowest_possible_idx) / 2)
                + lowest_possible_idx
            )
            idx_for_comparison = (
                new_idx_for_comparison
                if new_idx_for_comparison != idx_for_comparison
                else new_idx_for_comparison + 1
            )
            current_app.logger.info(
                f"is_preferred: {comparison.is_preferred}, lowest: {lowest_possible_idx}, highest: {highest_possible_idx}, comparison: {idx_for_comparison}"
            )

        current_app.logger.info(f"rateable: {self.other_items[idx_for_comparison]}")
        return Comparison(
            self.other_items[idx_for_comparison].name, idx_for_comparison, None
        )

    def get_overall_ratings(self):
        # Make a copy of the list
        rateables = [Rateable(name=r.name, rating=r.rating) for r in self.other_items]

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
            Rateable(name=r.name, rating=round((idx / denominator) * 100, 2))
            for (idx, r) in enumerate(rateables)
        ]


class Rateable:
    def __init__(self, name, rating):
        self.name = name
        self.rating = rating


class Comparison:
    def __init__(self, name, index, is_preferred):
        self.name = name
        self.index = index
        self.is_preferred = is_preferred
