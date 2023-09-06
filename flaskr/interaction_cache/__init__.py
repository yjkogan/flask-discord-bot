from typing import Dict, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from ..ratings import RatingCalculator

class InteractionCache:
    fake_redis: Dict[str, "RatingCalculator"] = {}

    @classmethod
    def get_rating_calculator(cls, cache_key: str) -> Optional["RatingCalculator"]:
        return cls.fake_redis.get(cache_key)

    @classmethod
    def store_rating_calculator(cls, cache_key: str, rating_calculator: "RatingCalculator") -> None:
        if cache_key in cls.fake_redis:
            return
        cls.fake_redis[cache_key] = rating_calculator

    @classmethod
    def remove_rating_calculator(cls, cache_key: str) -> None:
        if cache_key in cls.fake_redis:
            del cls.fake_redis[cache_key]
