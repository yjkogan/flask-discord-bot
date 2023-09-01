from flaskr.ratings import RatingCalculator, Comparison, Rateable


def test_get_next_comparison_empty(app):
    with app.app_context():
        ratings_calculator = RatingCalculator(
            item_being_rated=Rateable("a", None), other_items=[]
        )
        nc = ratings_calculator.get_next_comparison()
        assert nc is None

def test_get_next_comparison_middle(app):
    with app.app_context():
        ratings_calculator = RatingCalculator(
            item_being_rated=Rateable("a", None), other_items=[Rateable("b", 0.0), Rateable("c", 100.0)]
        )
        nc = ratings_calculator.get_next_comparison()
        assert nc is not None
        assert nc.name == "b"

        ratings_calculator.add_comparison(Comparison(nc.name, nc.index, False))
        nc = ratings_calculator.get_next_comparison()
        assert nc is not None
        assert nc.name == "c"

        ratings_calculator.add_comparison(Comparison(nc.name, nc.index, True))
        nc = ratings_calculator.get_next_comparison()
        assert nc is None

        overall_ratings = ratings_calculator.get_overall_ratings()
        expected_ratings = [Rateable("b", 0.0), Rateable("a", 50.0), Rateable("c", 100.0)]
        assert expected_ratings == overall_ratings

def test_get_next_comparison_hypest(app):
    with app.app_context():
        ratings_calculator = RatingCalculator(
            item_being_rated=Rateable("a", None), other_items=[Rateable("b", 0.0), Rateable("c", 50.0), Rateable("d", 100.0)]
        )
        nc = ratings_calculator.get_next_comparison()
        assert nc is not None
        assert nc.name == "c"

        ratings_calculator.add_comparison(Comparison(nc.name, nc.index, False))
        nc = ratings_calculator.get_next_comparison()
        assert nc is not None
        assert nc.name == "d"

        ratings_calculator.add_comparison(Comparison(nc.name, nc.index, False))
        nc = ratings_calculator.get_next_comparison()
        assert nc is None

        overall_ratings = ratings_calculator.get_overall_ratings()
        expected_ratings = [Rateable("b", 0.0), Rateable("c", 33.33), Rateable("d", 66.67), Rateable("a", 100.0)]
        assert expected_ratings == overall_ratings

def test_get_next_comparison_least_hype(app):
    with app.app_context():
        ratings_calculator = RatingCalculator(
            item_being_rated=Rateable("a", None), other_items=[Rateable("b", 0.0), Rateable("c", 50.0), Rateable("d", 100.0)]
        )
        nc = ratings_calculator.get_next_comparison()
        assert nc is not None
        assert nc.name == "c"

        ratings_calculator.add_comparison(Comparison(nc.name, nc.index, True))
        nc = ratings_calculator.get_next_comparison()
        assert nc is not None
        assert nc.name == "b"

        ratings_calculator.add_comparison(Comparison(nc.name, nc.index, True))
        nc = ratings_calculator.get_next_comparison()
        assert nc is None

        overall_ratings = ratings_calculator.get_overall_ratings()
        expected_ratings = [Rateable("a", 0.0), Rateable("b", 33.33), Rateable("c", 66.67), Rateable("d", 100.0)]
        assert expected_ratings == overall_ratings

def test_get_next_comparison_middle_hype(app):
    with app.app_context():
        ratings_calculator = RatingCalculator(
            item_being_rated=Rateable("a", None), other_items=[Rateable("b", 0.0), Rateable("c", 50.0), Rateable("d", 100.0)]
        )
        nc = ratings_calculator.get_next_comparison()
        assert nc is not None
        assert nc.name == "c"

        ratings_calculator.add_comparison(Comparison(nc.name, nc.index, True))
        nc = ratings_calculator.get_next_comparison()
        assert nc is not None
        assert nc.name == "b"

        ratings_calculator.add_comparison(Comparison(nc.name, nc.index, False))
        nc = ratings_calculator.get_next_comparison()
        assert nc is None

        overall_ratings = ratings_calculator.get_overall_ratings()
        expected_ratings = [Rateable("b", 0.0), Rateable("a", 33.33), Rateable("c", 66.67), Rateable("d", 100.0)]
        assert expected_ratings == overall_ratings
