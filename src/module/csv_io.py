#csvファイルの処理

import tkinter 
from tkinter import filedialog, messagebox
import pandas as pd
import csv

#ファイルパス取得
def select_file_path():
    root = tkinter.Tk()
    root.withdraw()
    tkinter.messagebox.showinfo('ファイル選択', '処理ファイルを選択してください')
    file_path = tkinter.filedialog.askopenfilename(filetypes=[("CSV files", "*.csv")])
    return file_path

# 指定されたCSVファイルの一列目をリストとして返す
def read_first_column_from_csv(file_path):
    df = pd.read_csv(file_path, header=None,dtype=str) 
    first_column_list = df.iloc[:, 0].astype(str).str.strip().tolist()# 最初の列をリスト化
    if not first_column_list[0].isdigit():
        del first_column_list[0]
    if not first_column_list:
        print("エラー")
    return first_column_list 

#csvファイルに書き込み(1列)
#もう使ってない
def csv_export_one(file_name,row_name,data):
    with open(f"{file_name}.csv", mode="w", newline="",encoding="utf-8-sig") as file:
            writer = csv.writer(file)
            writer.writerow([row_name]) #1列目：列名
            for item in data:
                writer.writerow([item])#2列目以降：データ
  
#csvファイルに書き込み(列数は動的)
def csv_export(file_name,list_of_dicts):
    fieldnames = sorted({key for row in list_of_dicts for key in row.keys()})

    with open(f"{file_name}.csv", mode="w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(list_of_dicts)
  
  
if __name__ == "__main__":
    file_path=select_file_path()
    print(file_path)
    first_column_list=read_first_column_from_csv(file_path)
    print(first_column_list)
    
    

