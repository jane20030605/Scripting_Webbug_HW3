import re
import requests
import sqlite3
import tkinter as tk
from tkinter import Label, Entry, Button, StringVar, messagebox
from tkinter.scrolledtext import ScrolledText


def setup_database() -> None:
    """
    設定 SQLite 資料庫，創建 contacts 資料表。
    """
    try:
        conn = sqlite3.connect('contacts.db')
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS contacts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                ext TEXT NOT NULL,
                email TEXT NOT NULL UNIQUE
            )
        ''')
        conn.commit()
    except sqlite3.DatabaseError as e:
        print(f"資料庫操作發生錯誤: {e}")
    except Exception as e:
        print(f"發生其它錯誤: {e}")
    finally:
        conn.close()


def save_to_database(name: str, ext: str, email: str):
    """
    儲存抓取到的聯絡資訊到資料庫，排除重複資料。
    :param name: 姓名
    :param ext: 分機
    :param email: Email
    """
    try:
        conn = sqlite3.connect('contacts.db')
        cursor = conn.cursor()
        cursor.execute('''
            INSERT OR IGNORE INTO contacts (name, ext, email)
            VALUES (?, ?, ?)
        ''', (name, ext, email))
        conn.commit()
    except sqlite3.DatabaseError as e:
        print(f"資料庫操作發生錯誤: {e}")
    finally:
        conn.close()


def scrape_contacts(url: str) -> list[tuple[str, str, str]]:
    """
    透過 requests 模組發送 GET 請求，從指定 URL 抓取 HTML 內容。
    """
    response = requests.get(url, timeout=10)
    response.raise_for_status()  # 如果回應不是 200，會引發錯誤
    return response.text


def parse_contacts(html_content: str) -> list[tuple[str, str, str]]:
    """
    從 HTML 內容中解析聯絡資訊（姓名、分機、Email）。
    
    :param html_content: 網頁 HTML 內容
    :return: 解析出的聯絡資訊，包含姓名、分機和 Email
    """
    # 姓名正則表達式，從 class="mtitle" 標籤中的 <a> 標籤提取姓名
    name_pattern = re.compile(r'<div class="mtitle">.*?<a href="[^"]+">([^<]+)</a>')

    # 分機和 Email 正則表達式，從 class="meditor" 標籤中的 <p> 標籤提取
    ext_pattern = re.compile(r'<div class="meditor">.*?<p>分機:\s*(\d+)</p>', re.DOTALL)
    email_pattern = re.compile(r'<div class="meditor">.*?<p>.*?mailto:([\w.%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,})', re.DOTALL)

    # 使用正則表達式抓取資料
    names = name_pattern.findall(html_content)
    exts = ext_pattern.findall(html_content)
    emails = email_pattern.findall(html_content)

    # 確保資料一致性，將抓取的資料配對成一個結果
    results = []
    for name, ext, email in zip(names, exts, emails):
        results.append((name.strip(), ext.strip(), email.strip()))
    
    return results


def display_contacts(contacts: list) -> None:
    """
    將聯絡資訊顯示在 Tkinter 視窗中。
    :param contacts: 包含聯絡資訊的字典列表
    """
    text_display.delete("1.0", "end")  # 清空目前內容
    if not contacts:
        text_display.insert("end", "沒有抓取到聯絡資訊。\n")
        return

    text_display.insert("end", f"{'姓名':<20}{'分機':<10}{'Email':<30}\n")
    text_display.insert("end", "-" * 60 + "\n")
    for contact in contacts:
        text_display.insert(
            "end", f"{contact[0]:<20}{contact[1]:<10}{contact[2]:<30}\n"
        )


def fetch_contacts() -> None:
    """
    抓取並顯示聯絡資訊，並將其儲存到資料庫。
    """
    url = url_var.get().strip()
    if not url:
        messagebox.showerror("錯誤", "請輸入有效的 URL。")
        return

    try:
        contacts = parse_contacts(scrape_contacts(url))
        display_contacts(contacts)
        for contact in contacts:
            save_to_database(contact[0], contact[1], contact[2])
        messagebox.showinfo("成功", "聯絡資訊已成功抓取並儲存到資料庫。")
    except RuntimeError as e:
        messagebox.showerror("錯誤", str(e))


def on_closing() -> None:
    """
    當關閉視窗時，關閉資料庫連接。
    """
    root.destroy()


# 建立 Tkinter 主視窗
root = tk.Tk()
root.title("聯絡資訊爬蟲")
root.geometry("640x480")
root.minsize(400, 300)

# 設定欄位的權重
root.grid_rowconfigure(1, weight=1)
root.grid_columnconfigure(0, weight=1)
root.grid_columnconfigure(1, weight=5)
root.grid_columnconfigure(2, weight=1)

# 網址輸入框
url_var = StringVar(value="https://ai.ncut.edu.tw/p/412-1063-2382.php")
Label(root, text="URL:").grid(row=0, column=0, padx=10, pady=10, sticky="w")
url_entry = Entry(root, textvariable=url_var)
url_entry.grid(row=0, column=1, padx=10, pady=10, sticky="we")

# 抓取按鈕
fetch_button = Button(root, text="抓取", command=fetch_contacts)
fetch_button.grid(row=0, column=2, padx=10, pady=10, sticky="E")

# 顯示區域
text_display = ScrolledText(root)
text_display.grid(row=1, column=0, columnspan=3, padx=10, pady=10, sticky="NSEW")

# 設定 grid 權重
root.grid_rowconfigure(1, weight=1)
root.grid_columnconfigure(1, weight=1)

# 當視窗關閉時執行 on_closing 函數
root.protocol("WM_DELETE_WINDOW", on_closing)

# 初始化資料庫
setup_database()

# 啟動主事件循環
root.mainloop()
