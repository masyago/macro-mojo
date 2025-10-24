from datetime import date, datetime
from typing import Optional, List


def error_for_nutrition_entry(
    calories: str, protein: str, fat: str, carbs: str
) -> Optional[str]:
    inputs = [calories, protein, fat, carbs]

    try:
        # Check that inputs are numbers
        for input in inputs:
            int(input)
    except ValueError:
        return """
            Inputs for calories, protein, fats, and carbohydrates must 
            be non-negative integers.
            """

    for input in inputs:
        # Check that inputs fall between 0 and 10,000, inclusive
        if int(input) not in range(10001):
            return """
                    Inputs for calories, protein, fats, and carbohydrates
                    must be integers between 0 and 10,000. Try again!
                    """

    return None


def error_for_meal_len(name: str) -> Optional[str]:
    if len(name) > 100:
        return (
            "Meal or snack name must be less than 100 characters. Try again!"
        )

    return None


def error_for_targets(
    calories: str, protein: str, fat: str, carbs: str
) -> Optional[str]:
    inputs = [calories, protein, fat, carbs]

    try:
        for input in inputs:
            int(input)
    except ValueError:
        return """Inputs for calories, protein, fats, and carbohydrates must 
                  be non-negative integers."""

    for input in inputs:
        if int(input) not in range(10001):
            return """Targets for calories, protein, fats, and carbohydrates 
                      must be integers between 0 and 10,000. Try again!"""

    return None


# Check date format in URL
def is_date_in_url_valid(d: str) -> bool:
    try:
        """Confirm that the input string can be converted to a datetime
        object"""
        datetime.strptime(d, "%Y-%m-%d")
        return True
    except ValueError:
        return False


# Check date format in user input
"""
Note: Even though browser display date is in 'MM/DD/YYYY', 
normalized format is 'YYYY-MM-DD'
"""


def error_for_date_format(date_str: str) -> Optional[str]:
    try:
        datetime.strptime(date_str, "%Y-%m-%d")
    except ValueError:
        return "Date must be in 'MM/DD/YYYY' format. Try again!"


def is_nutrition_id_valid(id: int, available_nutrition_id: List[int]) -> bool:
    if id in available_nutrition_id:
        return True
    return False


def get_todays_date() -> date:
    return date.today()
