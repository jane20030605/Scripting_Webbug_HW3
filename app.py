import re
import requests
import sqlite3
import tkinter as tk
from tkinter import Label, Entry, Button, StringVar, messagebox
from tkinter.scrolledtext import ScrolledText


def setup_database() -> None:
    """
    初始化 SQLite 資料庫，創建 contacts 資料表。
    """
    try:
        conn = sqlite3.connect("contacts.db")
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS contacts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                title TEXT NOT NULL,
                email TEXT NOT NULL UNIQUE
            )
        ''')
        conn.commit()
    except sqlite3.DatabaseError as e:
        print(f"資料庫操作發生錯誤: {e}")
    finally:
        conn.close()


def save_to_database(name: str, title: str, email: str) -> None:
    """
    將聯絡資訊存入 SQLite 資料庫，排除重複。
    :param name: 聯絡人姓名
    :param title: 職稱
    :param email: 電子郵件
    """
    try:
        conn = sqlite3.connect("contacts.db")
        cursor = conn.cursor()
        cursor.execute('''
            INSERT OR IGNORE INTO contacts (name, title, email)
            VALUES (?, ?, ?)
        ''', (name, title, email))
        conn.commit()
    except sqlite3.DatabaseError as e:
        print(f"資料庫操作發生錯誤: {e}")
    finally:
        conn.close()


def scrape_contacts(url: str) -> str:
    """
    從指定的 URL 抓取 HTML 內容。
    :param url: 目標 URL
    :return: HTML 內容
    """
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return response.text
    except requests.exceptions.RequestException as e:
        raise RuntimeError("無法連接網路" if "ConnectionError" in str(e) else "無法取得網頁")
    except requests.exceptions.HTTPError:
        raise RuntimeError("網頁錯誤(無法取得網頁)。")
    except requests.exceptions.RequestException as e:
        raise RuntimeError(f"未知的網路錯誤: {e}")


def parse_contacts(html_content: str) -> list[tuple[str, str, str]]:
    """
    解析 HTML 內容，提取姓名、職稱與 Email。
    :param html_content: HTML 內容
    :return: 聯絡資訊列表
    """
    name_pattern = re.compile(r'<div class="member_name"><a href="[^"]+">([^<]+)</a>')
    title_pattern = re.compile(r'<div class="member_info_content"[^>]*>([^<]*教授[^<]*)</div>')
    email_pattern = re.compile(r'mailto://([A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,})')

    names = name_pattern.findall(html_content)
    titles = title_pattern.findall(html_content)
    emails = email_pattern.findall(html_content)

    results = []
    for name, title, email in zip(names, titles, emails):
        results.append((name.strip(), title.strip(), email.strip()))
    return results


def pad_to_width(text: str, width: int) -> str:
    """
    將文字填充至指定寬度。
    :param text: 原始文字
    :param width: 目標寬度
    :return: 填充後的文字
    """
    return f"{text:<{width}}"


def display_contacts(contacts: list[tuple[str, str, str]]) -> None:
    """
    在 Tkinter 視窗中顯示聯絡資訊。
    :param contacts: 聯絡資訊列表
    """
    text_display.delete("1.0", "end")
    if not contacts:
        text_display.insert("end", "未抓取到聯絡資訊。\n")
        return

    name_width, title_width, email_width = 20, 30, 40
    header = (
        pad_to_width("姓名", name_width) +
        pad_to_width("職稱", title_width) +
        pad_to_width("Email", email_width)
    )
    text_display.insert("end", header + "\n")
    text_display.insert("end", "-" * (name_width + title_width + email_width) + "\n")

    for contact in contacts:
        row = (
            pad_to_width(contact[0], name_width) +
            pad_to_width(contact[1], title_width) +
            pad_to_width(contact[2], email_width)
        )
        text_display.insert("end", row + "\n")


def fetch_contacts() -> None:
    """
    抓取聯絡資訊，顯示在視窗中並儲存至資料庫。
    """
    url = url_var.get().strip()
    if not url:
        messagebox.showerror("錯誤", "請輸入有效的 URL。")
        return

    try:
        html_content = scrape_contacts(url)
        contacts = parse_contacts(html_content)
        display_contacts(contacts)
        for contact in contacts:
            save_to_database(contact[0], contact[1], contact[2])
        messagebox.showinfo("成功", "聯絡資訊已成功抓取並儲存至資料庫。")
    except RuntimeError as e:
        messagebox.showerror("錯誤", str(e))


def on_closing() -> None:
    """
    當關閉視窗時執行清理操作。
    """
    root.destroy()


# 主視窗設置
root = tk.Tk()
root.title("聯絡資訊爬蟲")
root.geometry("640x480")
root.minsize(400, 300)

# URL 輸入
url_var = StringVar(value="https://csie.ncut.edu.tw/content.php?key=86OP82WJQO")
Label(root, text="URL:").grid(row=0, column=0, padx=10, pady=10, sticky="w")
url_entry = Entry(root, textvariable=url_var)
url_entry.grid(row=0, column=1, padx=10, pady=10, sticky="we")
fetch_button = Button(root, text="抓取", command=fetch_contacts)
fetch_button.grid(row=0, column=2, padx=10, pady=10)

# 顯示區域
text_display = ScrolledText(root)
text_display.grid(row=1, column=0, columnspan=3, padx=10, pady=10, sticky="nsew")

# 權重設置
root.grid_rowconfigure(1, weight=1)
root.grid_columnconfigure(1, weight=1)

# 設定關閉事件
root.protocol("WM_DELETE_WINDOW", on_closing)

# 初始化資料庫
setup_database()

# 啟動主程式
root.mainloop()
