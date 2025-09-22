#国立国会図書館APIに関する処理

#文字化け対策に文字コードを指定
import sys
sys.stdout.reconfigure(encoding='utf-8')

import requests
from PIL import Image
from io import BytesIO
import webbrowser
import os
import xml.etree.ElementTree as ET
import re
import html


#書影を取得し、bookimagesフォルダに保存
def get_bookimage(isbn):
    url = f"https://ndlsearch.ndl.go.jp/thumbnail/{isbn}.jpg"
    response = requests.get(url)
    
    # 書影出力先のフォルダを指定（もし存在しなければ作成）
    output_folder = "book_images"
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    img_file = "書影なし" #書影を取得できない場合
    if response.status_code == 200:
        img = Image.open(BytesIO(response.content))
        img_path = os.path.join(output_folder, f"書影_{isbn}.jpg")
        img.save(img_path) 
        #print(f"{isbn}の書影を保存しました: {img_path}")
        return img_path
              
    else:
        #print(f"{isbn}の書影が見つかりませんでした。")
        return None

#NDCを取得
def get_ndc(isbn):
    url = (
        f"https://ndlsearch.ndl.go.jp/api/sru?"
        f"operation=searchRetrieve&"
        f"query=isbn={isbn}"
    )
    response = requests.get(url)

    # 取得失敗の場合 None を返す
    if response.status_code != 200:
        return None

    # HTMLエスケープをデコード
    decoded_text = html.unescape(response.text)

    # NDCの数値を正規表現で抽出
    ndc_match = re.search(r'<lst name="NDC">\s*<int name="(\d+)"', decoded_text)
    if ndc_match:
        return ndc_match.group(1)

    return None

#書影をHTML上に表示
def show_image_in_browser(image_path):
    html_content = f"""
    <html>
    <head><meta charset="utf-8"><title>書影表示</title></head>
    <body>
        <h2>書影画像</h2>
        <img src="{image_path}" style="max-width:400px;">
    </body>
    </html>
    """
    html_file = "book_image.html"
    with open(html_file, "w", encoding="utf-8") as f:
        f.write(html_content)

    # ブラウザでHTMLを開く
    webbrowser.open("file://" + os.path.abspath(html_file))
 
if __name__ == "__main__": 
    isbn="9784787200884"
    ndc=get_ndc(isbn)
    print(ndc)
    img_path=get_bookimage(isbn)
    #print(img_path)
    #if img_path:
        #show_image_in_browser(img_path)
    
        