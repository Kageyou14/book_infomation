#文字化け対策に文字コードを指定
import sys
sys.stdout.reconfigure(encoding='utf-8')

import sqlite3
import pandas as pd

DB_PATH = "library.db"

#データベースを作成
def init_db(db_path: str = DB_PATH) -> None:
    schema = """
    -- 「books」テーブル（ISBNごとの書誌情報）
    CREATE TABLE IF NOT EXISTS books (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      isbn TEXT NOT NULL UNIQUE,
      title TEXT,
      ndc TEXT,
      description TEXT,
      image_path TEXT
    );
    

    -- 「holdings」テーブル（図書館ごとの蔵書情報）
    CREATE TABLE IF NOT EXISTS holdings (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      book_id INTEGER NOT NULL,
      system_id TEXT NOT NULL,
      library_name TEXT NOT NULL,
      status TEXT NOT NULL,
      UNIQUE(book_id, library_name),
      FOREIGN KEY(book_id) REFERENCES books(id)
    );

    CREATE INDEX IF NOT EXISTS idx_books_isbn ON books(isbn);
    CREATE INDEX IF NOT EXISTS idx_holdings_book ON holdings(book_id);
    """
    with sqlite3.connect(db_path) as conn:
        conn.executescript(schema)
    print(f"DB初期化完了: {db_path}")

#外部キーの有効化
def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn

#booksテーブルにデータ追加
def insert_book(isbn, title, ndc, description, image_path):
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO books (isbn, title, ndc, description, image_path)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(isbn) DO UPDATE SET
                title=excluded.title,
                ndc=excluded.ndc,
                description=excluded.description,
                image_path=excluded.image_path
            """,
            (isbn, title, ndc, description, image_path)
        )

        conn.commit()#保存
    print(f"{title}の情報をデータベースに追加しました。")

#holdingsテーブルにデータ追加
def insert_holding(isbn, system_id, library_name, status):
    """
    蔵書情報を holdings テーブルに追加または更新する
    :param isbn: 書籍のISBN（13桁）
    :param system_id: 図書館システムID（例: "Tokyo_Musashino"）
    :param library_name: 図書館名
    :param status: 蔵書の状態（例: "貸出可", "貸出中"）
    """
    with get_conn() as conn:
        cur = conn.cursor()
        
        # book_id を ISBN から取得
        cur.execute("SELECT id FROM books WHERE isbn=?", (isbn,))
        row = cur.fetchone()
        if row is None:
            conn.close()
            raise ValueError(f"booksにISBNが見つかりません: {isbn}")
        book_id = row[0]

        # holdings に挿入（既存なら更新：book_id + library_name を一意）
        cur.execute("""
            INSERT INTO holdings (book_id, system_id, library_name, status)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(book_id, library_name) DO UPDATE SET
                status = excluded.status,
                system_id = excluded.system_id
        """, (book_id, system_id, library_name, status))

        conn.commit()
    print(f"[holdings] {library_name} に {isbn} を {status} で保存（system_id={system_id}）")

#テーブルからデータ消去
def delete_data(isbn):
    with get_conn() as conn:
        cur = conn.cursor()

        # book_id を取得
        cur.execute("SELECT id FROM books WHERE isbn = ?", (isbn,))
        book_id = cur.fetchone()
        if book_id:
            book_id = book_id[0]
            # holdings から削除
            cur.execute("DELETE FROM holdings WHERE book_id = ?", (book_id,))
            # books から削除
            cur.execute("DELETE FROM books WHERE id = ?", (book_id,))
        conn.commit()
    

#booksテーブルからデータ消去
def delete_book(isbn):
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute(""" DELETE FROM books WHERE isbn = ? """, (isbn,))
        conn.commit()#保存
        print(f"{isbn}の情報をbooksテーブルから消去しました。")

#holdingsテーブルからデータ消去
def delete_holdings(isbn):
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute(""" DELETE FROM holdings WHERE isbn = ? """, (isbn,))
        conn.commit()#保存
        print(f"{isbn}の情報をholdingsテーブルから消去しました。")

#データベースの確認
def check_db(table_name: str):
    """指定したテーブルの内容を表示して、DataFrame を返す"""
    with sqlite3.connect(DB_PATH) as conn:
        try:
            df = pd.read_sql_query(f"SELECT * FROM {table_name}", conn)
            print(f"\nテーブル名: {table_name}")
            print(df.to_string(index=False))  # インデックス非表示で見やすく
            return df
        except Exception as e:
            print(f"テーブル '{table_name}' の読み込みに失敗しました: {e}")
            return None

    

if __name__ == "__main__":
    # 1) 初期化
    init_db()

    # 2) ダミーの本を1件登録（UPSERT）
    isbn = "9780000000001"
    title = "動作確認の本"
    ndc = "000"
    description = "これは動作確認用の説明です"
    image_path = "dummy.jpg"
    insert_book(isbn, title, ndc, description, image_path)

    # 3) holdings を2件登録（同じ本×異なる館）
    system_id = "Tokyo_Musashino"
    insert_holding(isbn, system_id, "中央図書館", "貸出可")
    insert_holding(isbn, system_id, "境図書館",   "貸出中")

    # 4) 同じ本×同じ館に再度入れて UPSERT が効くか確認（ステータスを変更）
    insert_holding(isbn, system_id, "中央図書館", "館内のみ")

    # 5) SELECTで確認
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("PRAGMA foreign_keys = ON;")
        print("\n[books]")
        df_b = pd.read_sql_query("SELECT * FROM books", conn)
        print(df_b)

        print("\n[holdings] (JOIN)")
        df_h = pd.read_sql_query("""
            SELECT h.id, b.isbn, h.system_id, h.library_name, h.status
            FROM holdings h
            JOIN books b ON b.id = h.book_id
            ORDER BY h.id
        """, conn)
        print(df_h)
