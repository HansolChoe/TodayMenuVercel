import datetime
import os
import logging
import sys

import dotenv
import httpx
import pytz
from fastapi import FastAPI, Request, HTTPException
from slack_sdk import WebClient
from starlette.responses import JSONResponse, HTMLResponse
from tenacity import retry, stop_after_attempt, wait_fixed

dotenv.load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

app = FastAPI()

TODAY_MEAL_URL = os.getenv("TODAY_MEAL_URL")
SLACK_TOKEN = os.getenv("SLACK_TOKEN")
client = WebClient(token=SLACK_TOKEN)

if not TODAY_MEAL_URL:
    raise Exception("TODAY_MEAL_URL is not set")


@retry(stop=stop_after_attempt(3), wait=wait_fixed(1))
async def get_today_meal_menu():
    async with httpx.AsyncClient() as client:
        utc_now = datetime.datetime.now(pytz.utc)
        korea_now = utc_now.astimezone(pytz.timezone("Asia/Seoul"))
        formatted_korea_now = korea_now.strftime("%Y%m%d")

        url = TODAY_MEAL_URL
        response = await client.get(url)

        if response.status_code != 200:
            raise HTTPException(status_code=500, detail="Failed to retrieve data")

        data = response.json()
        if data['status'] != 'success':
            raise HTTPException(status_code=500, detail="Failed to retrieve data")

        meal_data = data.get('data', {})

        # Initialize result dictionary
        result = {}

        # Traverse the meal data to find the desired date
        for day, meals in meal_data.items():
            for meal in meals.get("2", []):  # Assuming mealCd "2" represents the relevant meals
                if meal['mealDt'] == formatted_korea_now:
                    corner = meal.get('corner')
                    if corner:
                        result[corner] = {
                            "name": meal['name'],
                            "side": meal['side']
                        }
        return result


@app.get("/", response_class=HTMLResponse)
async def read_root():
    return """
    <html>
        <head>
            <title>Welcome to TodayMenu</title>
        </head>
        <body>
            <h1>Welcome to TodayMenu API!</h1>
            <p>This is a default page to check if the server is running.</p>
        </body>
    </html>
    """


@app.post("/commands/lunch")
async def slack_lunch(request: Request):
    try:
        logger.info("Recieved lunch command request")
        meal_menu = await get_today_meal_menu()
        logger.info(f"Retrieved meal menu: {meal_menu}")
        utc_now = datetime.datetime.now(pytz.utc)
        korea_now = utc_now.astimezone(pytz.timezone("Asia/Seoul"))
        today_str = f"{korea_now.month}월 {korea_now.day}일"

        if meal_menu:
            # Build response message
            response_message = {
                "response_type": "in_channel",
                "text": f"오늘({today_str})의 점심 메뉴입니다:",
                "attachments": []
            }

            # Add meal information to the response
            for corner, menu in meal_menu.items():
                response_message["attachments"].append({
                    "text": f"{corner}: {menu['name']} - 반찬: {menu['side']}"
                })
        else:
            text = f"오늘({today_str})의 메뉴 정보가 없습니다. 아직 메뉴 정보가 업데이트 되지 않았을 수 있습니다."
            if korea_now.weekday() == 0:
                text += " 월요일의 경우 메뉴 정보가 늦게 업데이트 될 수 있습니다."
            response_message = {
                "response_type": "in_channel",
                "text": text
            }
    except Exception as e:
        logger.exception(f"Error in slack_lunch: {str(e)}")
        return JSONResponse(content={"text": f"Failed to retrieve meal data: {str(e)}"}, status_code=500)

    return JSONResponse(content=response_message)
