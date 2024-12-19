import httpx


def fetch_meal_data():
    # POST 요청을 보낼 URL
    url = "https://puls2.pulmuone.com/src/sql/menu/week_sql.php"

    # HTTP 헤더 설정
    headers = {
        "Accept": "application/json, text/javascript, */*; q=0.01",
        "Accept-Encoding": "gzip, deflate, br, zstd",
        "Accept-Language": "ko-KR,ko;q=0.9",
        "Connection": "keep-alive",
        "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
        "DNT": "1",
        "Origin": "https://puls2.pulmuone.com",
        "Referer": "https://puls2.pulmuone.com/src/php/menu/week.php",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
        "X-Requested-With": "XMLHttpRequest",
    }

    # POST 데이터 설정
    data = {
        "requestId": "search_week",
        "requestUrl": "/src/sql/menu/week_sql.php",
        "requestMode": 1,
        "requestParam": (
            '{"topOperCd":"O000002",'
            '"topAssignCd":"S000646",'
            '"menuDay":0,'
            '"srchCurShopclsCd":"",'
            '"custCd":""}'
        )
    }

    try:
        # HTTP 요청 보내기
        with httpx.Client() as client:
            response = client.post(url, headers=headers, data=data)
            response.raise_for_status()  # HTTP 오류 발생 시 예외 발생

        # JSON 데이터 로드
        try:
            json_data = response.json()
        except ValueError as e:
            raise ValueError("Response is not in valid JSON format.") from e

        # 데이터 파싱
        return parse_meal_data(json_data)

    except httpx.RequestError as e:
        raise Exception(f"HTTP request failed: {e}")
    except Exception as e:
        raise Exception(f"Unexpected error: {e}")


def parse_meal_data(data):
    """
    meal 데이터 파싱 함수
    """
    result = {}
    try:
        for row in data.get('data', []):
            if isinstance(row, list) and len(row) > 3:
                k, v = row[1], row[3]
                if k and v:
                    result[k] = v
    except (KeyError, IndexError, TypeError) as e:
        raise ValueError(f"Failed to parse menu data: {e}")
    return result
