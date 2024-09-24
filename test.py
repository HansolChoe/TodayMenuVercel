import httpx

TODAY_DATE = "20240610"

with httpx.Client() as client:
    url = "https://front.cjfreshmeal.co.kr/meal/v1/week-meal?storeIdx=6498&weekType=1"
    response = client.get(url)

    if response.status_code != 200:
        raise Exception("Failed to get meal data")
    data = response.json()
    if data['status'] != 'success':
        raise Exception("Failed to get meal data")
    meal_data = data.get('data', {})

    # Initialize result dictionary
    result = {}

    # Traverse the meal data to find the desired date
    for day, meals in meal_data.items():
        for meal in meals.get("2", []):  # Assuming mealCd "2" represents the relevant meals
            if meal['mealDt'] == TODAY_DATE:
                corner = meal.get('corner')
                if corner:
                    result[corner] = {
                        "name": meal['name'],
                        "side": meal['side']
                    }

    if not result:
        raise Exception(f"Menu data for the given date not found. {TODAY_DATE}")

    print (result)