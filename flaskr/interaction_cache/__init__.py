class InteractionCache:
    fake_redis = {}

    @classmethod
    def get_rating_calculator(cls, cache_key):
        return cls.fake_redis.get(cache_key)

    @classmethod
    def store_rating_calculator(cls, cache_key, rating_calculator):
        if cache_key in cls.fake_redis:
            return
        cls.fake_redis[cache_key] = rating_calculator

    @classmethod
    def remove_rating_calculator(cls, cache_key):
        if cache_key in cls.fake_redis:
            del cls.fake_redis[cache_key]
