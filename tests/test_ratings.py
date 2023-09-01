from flaskr.ratings import RatingCalculator, Comparison, Rateable


def test_get_next_comparison_empty(app):
    with app.app_context():
        ratings_calculator = RatingCalculator(
            item_being_rated=Rateable(1, "a", None), other_items=[]
        )
        nc = ratings_calculator.get_next_comparison()
        assert nc is None

def test_get_next_comparison_middle(app):
    with app.app_context():
        ratings_calculator = RatingCalculator(
            item_being_rated=Rateable(1, "a", None), other_items=[Rateable(2, "b", 0.0), Rateable(3, "c", 100.0)]
        )
        nc = ratings_calculator.get_next_comparison()
        assert nc is not None
        assert nc.name == "b"

        ratings_calculator.add_comparison(Comparison(nc.id, nc.name, nc.index, False))
        nc = ratings_calculator.get_next_comparison()
        assert nc is not None
        assert nc.name == "c"

        ratings_calculator.add_comparison(Comparison(nc.id, nc.name, nc.index, True))
        nc = ratings_calculator.get_next_comparison()
        assert nc is None

        overall_ratings = ratings_calculator.get_overall_ratings()
        expected_ratings = [Rateable(2, "b", 0.0), Rateable(1, "a", 50.0), Rateable(3, "c", 100.0)]
        assert expected_ratings == overall_ratings

def test_get_next_comparison_hypest(app):
    with app.app_context():
        ratings_calculator = RatingCalculator(
            item_being_rated=Rateable(1, "a", None), other_items=[Rateable(2, "b", 0.0), Rateable(3, "c", 50.0), Rateable(4, "d", 100.0)]
        )
        nc = ratings_calculator.get_next_comparison()
        assert nc is not None
        assert nc.name == "c"

        ratings_calculator.add_comparison(Comparison(nc.id, nc.name, nc.index, False))
        nc = ratings_calculator.get_next_comparison()
        assert nc is not None
        assert nc.name == "d"

        ratings_calculator.add_comparison(Comparison(nc.id, nc.name, nc.index, False))
        nc = ratings_calculator.get_next_comparison()
        assert nc is None

        overall_ratings = ratings_calculator.get_overall_ratings()
        expected_ratings = [Rateable(2, "b", 0.0), Rateable(3, "c", 33.33), Rateable(4, "d", 66.67), Rateable(1, "a", 100.0)]
        assert expected_ratings == overall_ratings

def test_get_next_comparison_least_hype(app):
    with app.app_context():
        ratings_calculator = RatingCalculator(
            item_being_rated=Rateable(1, "a", None), other_items=[Rateable(2, "b", 0.0), Rateable(3, "c", 50.0), Rateable(4, "d", 100.0)]
        )
        nc = ratings_calculator.get_next_comparison()
        assert nc is not None
        assert nc.name == "c"

        ratings_calculator.add_comparison(Comparison(nc.id, nc.name, nc.index, True))
        nc = ratings_calculator.get_next_comparison()
        assert nc is not None
        assert nc.name == "b"

        ratings_calculator.add_comparison(Comparison(nc.id, nc.name, nc.index, True))
        nc = ratings_calculator.get_next_comparison()
        assert nc is None

        overall_ratings = ratings_calculator.get_overall_ratings()
        expected_ratings = [Rateable(1, "a", 0.0), Rateable(2, "b", 33.33), Rateable(3, "c", 66.67), Rateable(4, "d", 100.0)]
        assert expected_ratings == overall_ratings

def test_get_next_comparison_middle_hype(app):
    with app.app_context():
        ratings_calculator = RatingCalculator(
            item_being_rated=Rateable(1, "a", None), other_items=[Rateable(2, "b", 0.0), Rateable(3, "c", 50.0), Rateable(4, "d", 100.0)]
        )
        nc = ratings_calculator.get_next_comparison()
        assert nc is not None
        assert nc.name == "c"

        ratings_calculator.add_comparison(Comparison(nc.id, nc.name, nc.index, True))
        nc = ratings_calculator.get_next_comparison()
        assert nc is not None
        assert nc.name == "b"

        ratings_calculator.add_comparison(Comparison(nc.id, nc.name, nc.index, False))
        nc = ratings_calculator.get_next_comparison()
        assert nc is None

        overall_ratings = ratings_calculator.get_overall_ratings()
        expected_ratings = [Rateable(2, "b", 0.0), Rateable(1, "a", 33.33), Rateable(3, "c", 66.67), Rateable(4, "d", 100.0)]
        assert expected_ratings == overall_ratings
