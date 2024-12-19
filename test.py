from utils import fetch_meal_data

if __name__ == "__main__":
    try:
        result = fetch_meal_data()
        print("Result:", result)
    except Exception as e:
        print(e)
