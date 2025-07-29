from datetime import date, datetime

def error_for_nutrition_entry(calories, protein, fat, carbs):
    inputs = [calories, protein, fat, carbs]
    
    try:
        for input in inputs:
            int(input)
    except:
        return "Inputs for calories, protein, fats, and carbohydrates must be non-negative integers."
    
    for input in inputs:
        if int(input) not in range(10001):
            return """Inputs for calories, protein, fats, and carbohydrates
                      must be integers between 0 and 10,000. Try again!"""
        
    return None

def error_for_targets(calories, protein, fat, carbs):
    inputs = [calories, protein, fat, carbs]
    
    try:
        for input in inputs:
            int(input)
    except:
        return "Inputs for calories, protein, fats, and carbohydrates must be non-negative integers."
    
    for input in inputs:
        if int(input) not in range(10001):
            return """Targets for calories, protein, fats, and carbohydrates
                      must be integers between 0 and 10,000. Try again!"""
        
    return None

def error_for_meal_len(name):
    if not 2 <= len(name) <= 100:
        return "Meal or snack name must be between 2 and 100 characters. Try again!"
    
    return None

def check_meal_duplicates(new_meal, existing_meals):
    for meal in existing_meals:
        if new_meal == meal:
            return "Entered meal name already exists. Try another one!"
    return None

def is_date_valid(d):
    try: 
        datetime.strptime(d, '%Y-%m-%d')
        return True
    except ValueError:
        return False
    
def is_meal_id_valid(id, available_meal_id):
    if id in available_meal_id:
        return True
    return False

def is_nutrition_id_valid(id, available_nutrition_id):
    if id in available_nutrition_id:
        return True
    return False