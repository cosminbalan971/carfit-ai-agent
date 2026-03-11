

from app.infrastructure.data import CARS
from app.domain.engine import recommend_cars


def test_diesel_sedan_auto_comfort_priority():
    prefs = {
        "fuel": "diesel",
        "body": "sedan",
        "gearbox": "auto",
        "reliability_priority": 1,
        "comfort_priority": 5
    }

    result = recommend_cars(CARS, prefs)

    print("\nTest: Comfort priority high")
    print(result)

    assert result["total_matches"] >= 1
    assert result["top_3"][0]["name"] == "Volkswagen Passat 2.0 TDI DSG"


def test_diesel_sedan_auto_reliability_priority():
    prefs = {
        "fuel": "diesel",
        "body": "sedan",
        "gearbox": "auto",
        "reliability_priority": 5,
        "comfort_priority": 1
    }

    result = recommend_cars(CARS, prefs)

    print("\nTest: Reliability priority high")
    print(result)

    assert result["total_matches"] >= 1
    assert result["top_3"][0]["name"] == "Toyota Avensis 2.0 D-4D Auto"


if __name__ == "__main__":
    test_diesel_sedan_auto_comfort_priority()
    test_diesel_sedan_auto_reliability_priority()
    print("\nAll tests passed.")