from flask import Flask, render_template, url_for, send_from_directory, request
from src.module.db_io import insert_book
from app import get_books, build_image_src

app = Flask(__name__)
DB_PATH = "library.db"

#ISBNが入力されたらデータベースに追加
@app.route('/', methods=['POST'])
def add_book():
    if request.method == 'POST':
        isbn = request.form.get('input_isbn')
        insert_book(isbn, "テストtitle", "テストndc", "テストdescription", "テストimage_path")
        books = get_books()
        return render_template("index.html", books=books, build_image_src=build_image_src)
