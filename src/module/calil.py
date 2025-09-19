#カーリルAPIに関する処理

#文字化け対策に文字コードを指定
import sys
sys.stdout.reconfigure(encoding='utf-8')

from dotenv import load_dotenv
import os
import requests
import re
import json
import time

#APPKEY,ISBN,市区町村(systemID)を指定して蔵書情報を取得
def get_library_holdings_and_status(ISBN,SYSTEMID,APPKEY=None, SESSION=None):
    url = "https://api.calil.jp/check"
    params = {
        "isbn":ISBN,
        "systemid": SYSTEMID,
        "callback": "no"  # JSON応答
    }

    if SESSION:
        params["session"] = SESSION
    else:
        params["appkey"] = APPKEY

    response = requests.get(url, params=params)
    json_data=response.json()
    return json_data


if __name__ == "__main__":
    #APIキーの読み込み
    load_dotenv()
    calil_api_key = os.getenv("CALIL_API_KEY")
    #条件指定
    isbn="9784787200884"
    system_id="Tokyo_Musashino"

    #最初のリクエスト
    json_data=get_library_holdings_and_status(isbn,system_id,APPKEY=calil_api_key)
    print(json_data)
    
    #検索が失敗すれば、受け取った「session」をAPPKEYに更新して再検索。 
    retries = 0 
    while json_data.get("continue", 0) == 1 and retries < 5: 
        session=json_data["session"] 
        json_data=get_library_holdings_and_status(isbn,system_id,session=session) 
        print(f"データ取得中...（リトライ {retries + 1} 回目）") 
        retries+=1 
        time.sleep(2)