import datetime
import os
import logging
import sys

import dotenv
import pytz
from fastapi import FastAPI, Request, HTTPException
from slack_sdk import WebClient
from starlette.responses import JSONResponse, HTMLResponse
from tenacity import retry, stop_after_attempt, wait_fixed

from utils import fetch_meal_data

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

SLACK_TOKEN = os.getenv("SLACK_TOKEN")
client = WebClient(token=SLACK_TOKEN)


def format_error_message(error: str) -> str:
    return f"점심 메뉴 정보를 가져오는 데 실패했습니다. 에러: {error}"

@retry(stop=stop_after_attempt(3), wait=wait_fixed(1))
async def get_today_meal_text():
    try:
        utc_now = datetime.datetime.now(pytz.utc)
        korea_now = utc_now.astimezone(pytz.timezone("Asia/Seoul"))
        formatted_korea_now = korea_now.strftime("%Y-%m-%d")

        meal_data = fetch_meal_data()
        if not meal_data:
            if korea_now.weekday() in [5, 6]:
                meal_text = "오늘은 주말입니다. 점심 메뉴 정보가 없습니다."
            elif korea_now.weekday() == 0:
                meal_text = "점심 메뉴 정보가 아직 업데이트되지 않았습니다. 월요일의 경우 정보가 늦게 업데이트될 수 있습니다."
            else:
                meal_text = "오늘 판교 캠퍼스 점심 메뉴가 이작 업데이트 되지 않았습니다."
        else:
            formatted_meal_data = "\n".join([f"- {k}: {v}" for k, v in meal_data.items()])
            meal_text = f"판교 캠퍼스 점심 메뉴({formatted_korea_now}) 입니다:\n" + formatted_meal_data

        return meal_text
    except Exception as e:
        logger.exception(f"Error while fetching meal data: {e}")
        raise HTTPException(status_code=500, detail=format_error_message(str(e)))


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
        logger.info("Received lunch command request")
        today_meal_text = await get_today_meal_text()
        response_message = {
            "response_type": "in_channel",
            "text": today_meal_text
        }
    except HTTPException as http_exc:
        logger.warning(f"Known error: {http_exc.detail}")
        return JSONResponse(content={"text": http_exc.detail}, status_code=http_exc.status_code)
    except Exception as e:
        logger.exception(f"Unexpected error: {e}")
        return JSONResponse(content={"text": format_error_message("알 수 없는 오류가 발생했습니다.")}, status_code=500)

    return JSONResponse(content=response_message)

