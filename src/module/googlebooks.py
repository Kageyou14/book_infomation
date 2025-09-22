#googlebooksAPIの操作

#文字化け対策に文字コードを指定
import sys
sys.stdout.reconfigure(encoding='utf-8')

import requests

#指定したISBNに対応するISBN13桁・書名・説明文を、GoogleBooksAPIで取得
def get_isbn_title_description_GoogleBooksAPI(ISBN):
    url=f"https://www.googleapis.com/books/v1/volumes?q=isbn:{ISBN}"
    response= requests.get(url).json()

   # 検索結果がない場合
    if "items" not in response:
        return ISBN, None, None
    volume_info = response["items"][0]["volumeInfo"]
    # ISBN-13 の取得（industryIdentifiersのリストを安全に処理）
    isbn13 = ISBN  # デフォルトは入力値のまま
    for identifier in volume_info.get("industryIdentifiers", []):
        if identifier["type"] == "ISBN_13":
            isbn13 = identifier["identifier"]
        else:
            isbn13 = None
    # タイトルの取得（なければデフォルト値）
    title = volume_info.get("title", "タイトルなし")
    # 説明文の取得（なければデフォルト値）
    description = volume_info.get("description", "説明文なし")
    return  isbn13,title,description