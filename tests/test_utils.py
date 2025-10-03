import pytest
from macro_mojo import utils

from datetime import date, datetime

"""
Parametrized tests for nutrition entry and targets. Functions tested:
- `error_for_nutrition_entry`
- `error_for_targets`

Tests:
1. Valid inputs:
   - Test that the function returns `None` when inputs are integers within set 
     range
2. Invalid inputs:
   - Test that the function returns an error if any of the inputs are not 
   integers: float and str
   - Test that the function returns an error if any of the inputs are integers 
     but outside set range
"""
@pytest.mark.parametrize("func, args, expected_output",
    [
        (utils.error_for_nutrition_entry, (1, 5, 10, 2000), None),
        (utils.error_for_nutrition_entry, (0, 0, 0, 0), None),
        (utils.error_for_nutrition_entry, (10000, 10000, 10000, 10000), None),
        (utils.error_for_targets, (1, 5, 10, 2000), None),
        (utils.error_for_targets, (0, 0, 0, 0), None),
        (utils.error_for_targets, (10000, 10000, 10000, 10000), None),
    ]
    )
def test_nutrition_and_targets_inputs_valid(func, args, expected_output):
    assert func(*args) == expected_output

@pytest.mark.parametrize("func, args, expected_output_substr",
    [
        (utils.error_for_nutrition_entry, ("10.1", 0, 0, 0), 
                                           "non-negative integers"),
        (utils.error_for_nutrition_entry, (10.1, 0, 0, 0),
                                           "between 0 and 10,000"),
        (utils.error_for_nutrition_entry, (-10, 0, 0, 0), 
                                           "between 0 and 10,000"),
        (utils.error_for_nutrition_entry, (10, 0, 10001, 0), 
                                           "between 0 and 10,000"),
        (utils.error_for_targets, ("10.1", 0, 0, 0), 
                                    "non-negative integers"),
        (utils.error_for_targets, (10.1, 0, 0, 0),
                                   "between 0 and 10,000"),
        (utils.error_for_targets, (-10, 0, 0, 0), 
                                   "between 0 and 10,000"),
        (utils.error_for_targets, (10, 0, 10001, 0), 
                                   "between 0 and 10,000"),
    ]
    )
def test_nutrition_and_targets_inputs_invalid(func, args, expected_output_substr):
    assert expected_output_substr in func(*args)

"""
Tests for `error_for_meal_len` function:
1. Test that the function returns `None` when input is under 100 characters
2. Test that the function returns error when input is greater that 100
   charaters 
"""
def test_error_for_meal_len_ok():
    assert utils.error_for_meal_len("") is None
    assert utils.error_for_meal_len("tomato") is None

def test_error_for_meal_len_too_long():
    meal_input = """A very spicy ramen with chicken, corn, and delisious noodles
                    in a trendy downtown Japanese restaurant. I loved it so
                    much, I want to come back!"""
    meal_len_error_message = utils.error_for_meal_len(meal_input)
    assert meal_len_error_message is not None
    assert "must be less than 100 characters" in meal_len_error_message

"""
Tests for `is_date_in_url_valid` function:
1. Test that the function returns `True` when input string that represents date
   in URL can be converted to a datetime object
2. Test that the function returns `False` when input string that represents date
   in URL cannot be converted to a datetime object
"""
def test_is_date_in_url_valid_ok():
    date_url = '2025-06-01'
    assert utils.is_date_in_url_valid(date_url) == True
    
def test_is_date_in_url_valid_invalid_year():
    date_url = '25-06-01'
    assert utils.is_date_in_url_valid(date_url) == False

def test_is_date_in_url_valid_invalid_delimeter():
    date_url = '2025/06/01'
    assert utils.is_date_in_url_valid(date_url) == False

"""
Tests for `error_for_date_format` function:
1. Test that the function returns `None` when user date input can be converted 
   to a datetime object
2. Test that the function returns an error message when user date input cannot 
   be converted to a datetime object
"""
def test_error_for_date_format_ok():
    date_input = '2025-09-13'
    assert utils.error_for_date_format(date_input) is None

def test_error_for_date_format_invalid():
    date_input = '13-09-2025'
    error_message = "Date must be in 'MM/DD/YYYY' format"
    assert error_message in utils.error_for_date_format(date_input)

"""
Tests for `is_nutrition_id_valid` function:
1. Test that the function returns `True` if nutrition id can be found in 
   available_nutrition_id
2. Test that the function returns `False` if nutrition id cannot be found in 
   available_nutrition_id
"""
def test_is_nutrition_id_valid_ok():
    available_nutrition_id = [1, 2, 4, 7]
    assert utils.is_nutrition_id_valid(1, available_nutrition_id) == True

def test_is_nutrition_id_valid_invalid_avail_id_empty():
    available_nutrition_id = []
    assert utils.is_nutrition_id_valid(1, available_nutrition_id) == False

def test_is_nutrition_id_valid_invalid_not_in_avail_id():
    available_nutrition_id = [1, 2, 3, 7, 90]
    assert utils.is_nutrition_id_valid(8, available_nutrition_id) == False

"""
Tests for `get_todays_date` function:
1. Test that the function returns instance of class `datetime.date`
2. Test that the function returns today's date
"""
def test_get_todays_date_class_date():
    assert isinstance(utils.get_todays_date(), date)

def test_get_todays_date_correct():
    test_date = date.today()
    assert utils.get_todays_date() == test_date


