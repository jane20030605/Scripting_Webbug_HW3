import re
import requests
import sqlite3
import tkinter as tk
from tkinter import Label, Entry, Button, StringVar, messagebox
from tkinter import ttk


def setup_database() -> None:
    """
    初始化 SQLite 資料庫，創建一個名為 contacts 的資料表。
    若資料表不存在，則自動建立。
    """
    try:
        # 連接 SQLite 資料庫 (若不存在會自動建立)
        conn = sqlite3.connect("contacts.db")
        cursor = conn.cursor()
        # 創建 contacts 資料表，包含 id (主鍵)、姓名、職稱、電子郵件
        cursor.execute(''' 
            CREATE TABLE IF NOT EXISTS contacts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                title TEXT NOT NULL,
                email TEXT NOT NULL UNIQUE
            )
        ''')
        conn.commit()  # 提交更改
    except sqlite3.DatabaseError as e:
        print(f"資料庫操作發生錯誤: {e}")
    finally:
        conn.close()  # 關閉資料庫連接


def save_to_database(name: str, title: str, email: str) -> None:
    """
    將聯絡資訊存入 SQLite 資料庫，避免重複插入。
    :param name: 聯絡人姓名
    :param title: 職稱
    :param email: 電子郵件
    """
    try:
        # 連接 SQLite 資料庫
        conn = sqlite3.connect("contacts.db")
        cursor = conn.cursor()
        # 插入聯絡資訊，如果電子郵件已存在則忽略
        cursor.execute(''' 
            INSERT OR IGNORE INTO contacts (name, title, email)
            VALUES (?, ?, ?)
        ''', (name, title, email))
        conn.commit()  # 提交更改
    except sqlite3.DatabaseError as e:
        print(f"資料庫操作發生錯誤: {e}")
    finally:
        conn.close()  # 關閉資料庫連接


def scrape_contacts(url: str) -> str:
    """
    從指定的 URL 抓取 HTML 內容，並處理網路錯誤。
    :param url: 目標 URL
    :return: HTML 內容
    """
    try:
        # 使用 requests 抓取 URL 的內容
        response = requests.get(url, timeout=10)
        response.raise_for_status()  # 如果 HTTP 狀態碼不是 200，拋出異常
        return response.text  # 返回 HTML 內容
    except requests.exceptions.ConnectionError:
        # 無法連接網站時顯示錯誤訊息
        messagebox.showerror("網路錯誤", "無法連接網站。")
        raise RuntimeError("Domain 錯誤")
    except requests.exceptions.HTTPError as e:
        # 若 HTTP 狀態碼為 404，顯示特定錯誤訊息
        if e.response.status_code == 404:
            messagebox.showerror("網頁錯誤", "無法取得網頁：404\n")
            raise RuntimeError("404 錯誤")
        else:
            raise RuntimeError(f"HTTP 錯誤：{e.response.status_code}")
    except requests.exceptions.RequestException as e:
        # 其他未知的網路錯誤
        messagebox.showerror("未知的網路錯誤", f"未知的網路錯誤：\n{str(e)}")
        raise RuntimeError("未知的網路錯誤")


def parse_contacts(html_content: str) -> list[tuple[str, str, str]]:
    """
    解析 HTML 內容，提取姓名、職稱與 Email。
    :param html_content: HTML 內容
    :return: 聯絡資訊列表，每項為 (姓名, 職稱, 電子郵件)
    """
    # 定義正則表達式來匹配姓名、職稱和 Email
    name_pattern = re.compile(r'<div class="member_name"><a href="[^"]+">([^<]+)</a>')
    title_pattern = re.compile(r'<div class="member_info_content"[^>]*>([^<]*教授[^<]*)</div>')
    email_pattern = re.compile(r'mailto://([A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,})')

    # 匹配 HTML 中的姓名、職稱和 Email
    names = name_pattern.findall(html_content)
    titles = title_pattern.findall(html_content)
    emails = email_pattern.findall(html_content)

    # 將結果組合成 (姓名, 職稱, Email) 的列表
    results = []
    for name, title, email in zip(names, titles, emails):
        results.append((name.strip(), title.strip(), email.strip()))
    return results


def display_contacts(contacts: list[tuple[str, str, str]]) -> None:
    """
    使用 Treeview 控件顯示聯絡資訊。
    :param contacts: 聯絡資訊列表
    """
    # 清空舊的內容
    for widget in table_frame.winfo_children():
        widget.destroy()

    # 定義 Treeview 的欄位
    columns = ("姓名", "職稱", "Email")
    tree = ttk.Treeview(table_frame, columns=columns, show="headings", height=20)

    # 設定欄位標題和寬度
    tree.heading("姓名", text="姓名")
    tree.heading("職稱", text="職稱")
    tree.heading("Email", text="Email")
    tree.column("姓名", width=120, anchor="w")
    tree.column("職稱", width=200, anchor="w")
    tree.column("Email", width=250, anchor="w")

    separator = ("-" * 120, "-" * 200, "-" * 250) 
    tree.insert("", "end", values=separator)

    # 將資料插入 Treeview
    for contact in contacts:
        tree.insert("", "end", values=contact)

    # 添加垂直滾動條
    scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=tree.yview)
    tree.configure(yscrollcommand=scrollbar.set)
    scrollbar.pack(side="right", fill="y")

    tree.pack(fill="both", expand=True)

    # 如果沒有抓取到資料，顯示提示訊息
    if not contacts:
        messagebox.showinfo("提示", "未抓取到聯絡資訊。")


def fetch_contacts() -> None:
    """
    嘗試抓取聯絡資訊，若遇到錯誤則顯示彈跳視窗。
    """
    # 從輸入框獲取 URL
    url = url_var.get().strip()
    if not url:
        messagebox.showerror("錯誤", "請輸入有效的 URL。")
        return

    try:
        # 抓取 HTML 內容並解析聯絡資訊
        html_content = scrape_contacts(url)
        contacts = parse_contacts(html_content)
        # 顯示聯絡資訊並儲存到資料庫
        display_contacts(contacts)
        messagebox.showinfo("成功", "聯絡資訊已成功抓取並儲存至資料庫。")
        for name, title, email in contacts:
            save_to_database(name, title, email)
    except RuntimeError as e:
        print(f"抓取過程中出現錯誤：{e}")


def on_closing() -> None:
    """
    當使用者關閉視窗時執行的清理操作。
    """
    root.destroy()


# 主視窗設置
root = tk.Tk()
root.title("聯絡資訊爬蟲")  # 視窗標題
root.geometry("640x480")  # 預設視窗大小
root.minsize(400, 300)  # 最小視窗大小

# URL 輸入框
url_var = StringVar(value="https://csie.ncut.edu.tw/content.php?key=86OP82WJQO")
Label(root, text="URL:").grid(row=0, column=0, padx=10, pady=10, sticky="w")
url_entry = Entry(root, textvariable=url_var)
url_entry.grid(row=0, column=1, padx=10, pady=10, sticky="we")
fetch_button = Button(root, text="抓取", command=fetch_contacts)
fetch_button.grid(row=0, column=2, padx=10, pady=10)

# 顯示聯絡資訊的表格框架
table_frame = ttk.Frame(root)
table_frame.grid(row=1, column=0, columnspan=3, padx=10, pady=10, sticky="nsew")

# 設置表格框架的權重，確保視窗大小調整時表格自適應
root.grid_rowconfigure(1, weight=1)
root.grid_columnconfigure(1, weight=1)

# 設定關閉事件
root.protocol("WM_DELETE_WINDOW", on_closing)

# 初始化資料庫
setup_database()

# 啟動主程式
root.mainloop()