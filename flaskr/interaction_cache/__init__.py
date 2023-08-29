from flask import current_app

class InteractionCache:
    fake_redis = {}

    def _get_key(user_id, artist_name):
        return f'{user_id}:{artist_name}'

    def get_interaction(user_id, artist_name):
        return InteractionCache.fake_redis.get(InteractionCache._get_key(user_id, artist_name))

    def store_interaction(user_id, artist_name, artists_for_user):
        key = InteractionCache._get_key(user_id=user_id, artist_name=artist_name)
        if key in InteractionCache.fake_redis:
            return InteractionCache.fake_redis[key]
        interaction = {
            'artist_name': artist_name,
            'artists_for_user': artists_for_user,
            'comparisons': []
        }
        InteractionCache.fake_redis[key] = interaction
        return interaction

    def add_comparison(interaction, compared_to_artist, index_of_compared_artist, is_preferred_to_new_artist):
        if interaction is None:
            return None # TODO: throw
        interaction['comparisons'].append({
            'compared_to_artist': compared_to_artist,
            'is_preferred_to_new_artist': is_preferred_to_new_artist,
            'index_of_compared_artist': index_of_compared_artist
        })
        return interaction

    def get_artist_to_compare(interaction):
        if interaction is None:
            return (None, None) # TODO: throw
        artists_for_user = interaction['artists_for_user']
        if not artists_for_user:
            return (None, None)
        comparisons = interaction['comparisons']
        lowest_possible_artist_idx = 0
        highest_possible_artist_idx = len(artists_for_user) - 1
        idx_for_comparison = int((highest_possible_artist_idx - lowest_possible_artist_idx) / 2) + lowest_possible_artist_idx
        current_app.logger.info(f'lowest: {lowest_possible_artist_idx}, highest: {highest_possible_artist_idx}, comparison: {idx_for_comparison}')
        for comparison in comparisons:
            is_preferred = comparison['is_preferred_to_new_artist']
            if is_preferred:
                highest_possible_artist_idx = idx_for_comparison
            else:
                lowest_possible_artist_idx = idx_for_comparison
            if highest_possible_artist_idx == lowest_possible_artist_idx:
                return (None, None)
            new_idx_for_comparison = int((highest_possible_artist_idx - lowest_possible_artist_idx) / 2) + lowest_possible_artist_idx
            idx_for_comparison = new_idx_for_comparison if new_idx_for_comparison != idx_for_comparison else new_idx_for_comparison + 1
            current_app.logger.info(f'is_preferred: {is_preferred}, lowest: {lowest_possible_artist_idx}, highest: {highest_possible_artist_idx}, comparison: {idx_for_comparison}')

        return (idx_for_comparison, artists_for_user[idx_for_comparison])


# class Interaction:
#     def __init__(self, user_id, artist_name, artists_for_user):
#         self.user_id = user_id
#         self.artist_name = artist_name
#         self.artists_for_user
