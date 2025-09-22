from flask import Flask, render_template, url_for, send_from_directory, request
import sqlite3, time, os
from src.module.db_io import init_db, insert_book,insert_holding, delete_data
from src.module.googlebooks import get_isbn_title_description_GoogleBooksAPI
from src.module.ndlSearch import get_ndc,get_bookimage
from src.module.calil import get_library_holdings_and_status
from dotenv import load_dotenv



app = Flask(__name__)
DB_PATH = "library.db"

init_db()

#booksテーブルのデータを取得
def get_books():
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute("SELECT * FROM books").fetchall()
    return rows

#holdingsテーブルのデータを取得
def get_holdings():
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute("SELECT * FROM holdings").fetchall()
    return rows

#指定したISBNに対応するデータを取得
def get_book_detail(isbn: str):
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        
        #指定したISBNに対応するbooksテーブルのデータを取得
        book = conn.execute(
            "SELECT * FROM books WHERE isbn = ?", (isbn,)
        ).fetchone()

        #指定したbook_idに対応するholdingsテーブルのデータを取得
        holdings = conn.execute("""
            SELECT *
            FROM holdings
            WHERE holdings.book_id = ?
        """, (book["id"],)).fetchall()

        return {"book": book, "holdings": holdings}


#画像ファイルの提供
@app.route("/book_images/<path:filename>")
def serve_book_image(filename):
    return send_from_directory("book_images", filename)

#画像ファイルのURL生成
def build_image_src(image_path: str | None) -> str | None:
    if not image_path:
        return url_for("serve_book_image", filename="default_image.jpg")
    
    p = image_path.replace("\\", "/").strip()
    if p.startswith("book_images/"):
        p = p.split("book_images/", 1)[1]
    return url_for("serve_book_image", filename=p)

#indexページにデータベース情報を読み取り
@app.route("/")
def index():
    books = get_books()
    holdings=get_holdings()
    return render_template("index.html", books=books, build_image_src=build_image_src, holdings=holdings) 

#booksページにデータベース情報を読み取り
@app.route("/book/<isbn>")
def book_by_isbn(isbn):
    
    data = get_book_detail(isbn)
    book = data["book"]  
    holdings = data["holdings"]
    img_src = build_image_src(book["image_path"])
    return render_template("book.html", book=book, img_src=img_src, holdings=holdings)

#ISBNが入力されたらbooksデータベースに追加
@app.route('/add_data', methods=["POST"])
def add_data():
    if request.method == 'POST':
        input_isbn = request.form.get('input_isbn')
        
        #APIから情報取得
        isbn, title, description =get_isbn_title_description_GoogleBooksAPI(input_isbn)#ISBN13桁(上書き)・書名・説明文
        if title==None:
            message = f"書籍情報が見つかりませんでした。入力内容：{input_isbn}"
            books = get_books()
            return render_template("index.html", books=books, message=message, build_image_src=build_image_src)
                
        ndc=get_ndc(isbn)#NDCを取得
        image_path=get_bookimage(isbn)#書影を取得し、bookimagesフォルダに保存

        message = f"データベースに「ISBN:{isbn}」の書籍情報を登録しました。"
        insert_book(isbn, title, ndc, description, image_path)#データベースに保存
        books = get_books()
        
        ##カーリルAPI
    
        #図書館の条件指定  
        system_id="Tokyo_Musashino" #検索する図書館
        
        #APIキーの読み込み
        load_dotenv()
        calil_api_key = os.getenv("CALIL_API_KEY")
        
        #最初のリクエスト
        json_data=get_library_holdings_and_status(isbn,system_id,APPKEY=calil_api_key)
        #検索が失敗すれば、受け取った「session」をAPPKEYに更新して再検索。 
        retries = 0 
        while json_data.get("continue", 0) == 1 and retries < 5: 
            session=json_data["session"] 
            json_data=get_library_holdings_and_status(isbn,system_id,SESSION=session) 
            print(f"データ取得中...（リトライ {retries + 1} 回目）") 
            retries+=1 
            time.sleep(2)
        lib_info = json_data.get("books", {}).get(isbn, {}).get(system_id, {})
        libkey = lib_info.get("libkey")
        if libkey:
            # 図書館ごとに蔵書情報を追加
            for lib_name, status in libkey.items():
                insert_holding(isbn, system_id, lib_name, status)
        
        return render_template("index.html", books=books, build_image_src=build_image_src, message=message)

#削除ボタンを押したらデータベースから削除
@app.route('/delete_data', methods=['POST'])
def delete_():
    if request.method == 'POST':
        isbn = request.form.get("delete_data")
        delete_data(isbn)
        books = get_books()
        message = f"データベースから「ISBN:{isbn}」の書籍情報を削除しました。"
        return render_template("index.html", books=books, build_image_src=build_image_src, message=message)

if __name__ == "__main__":
    app.run(debug=True)
