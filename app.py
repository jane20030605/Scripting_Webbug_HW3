import re
import requests
import sqlite3
from tkinter import Tk, Label, Entry, Button, StringVar, messagebox
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


def parse_contacts(html: str) -> list[dict]:
    """
    從 HTML 內容解析聯絡資訊。
    :param html: HTML 內容字串
    :return: 包含聯絡資訊的字典列表
    """
    # 姓名抓取：抓取 <a> 標籤內的文字
    name_pattern = re.compile(r'<div class="mtitle"><a [^>]*title="([^"]+)">', re.S)
    # 信箱抓取：信箱對應的 p 標籤
    email_pattern = re.compile(r'<p>信箱\s*[:：]\s*([\w.%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,})</p>', re.S)
    # 分機抓取：分機數字
    ext_pattern = re.compile(r'<p>電話\s*[:：]\s*[\d\-]+.*?分機\s*[:：]\s*(\d+)</p>', re.S)

    # 抓取所有匹配的項目
    names = name_pattern.findall(html)
    emails = email_pattern.findall(html)
    exts = ext_pattern.findall(html)

    print(f"抓取的姓名: {names}")
    print(f"抓取的信箱: {emails}")
    print(f"抓取的分機: {exts}")

    # 將結果打包成字典列表
    contacts = []
    max_len = max(len(names), len(exts), len(emails))  # 取最大長度，防止資料丟失

    for i in range(max_len):
        contact = {
            "name": names[i].strip() if i < len(names) else "N/A",
            "ext": exts[i].strip() if i < len(exts) else "N/A",
            "email": emails[i].strip() if i < len(emails) else "N/A",
        }
        contacts.append(contact)

    return contacts


def scrape_contacts(url: str) -> list[dict]:
    """
    從指定的 URL 抓取聯絡資訊。
    :param url: 網頁的 URL
    :return: 包含聯絡資訊的字典列表
    """
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
    except requests.Timeout:
        raise RuntimeError("抓取網頁超時，請檢查網路連接。")
    except requests.RequestException as e:
        raise RuntimeError(f"無法抓取資料: {e}")

    return parse_contacts(response.text)


def display_contacts(contacts: list[dict]) -> None:
    """
    將聯絡資訊顯示在 Tkinter 視窗中。
    :param contacts: 包含聯絡資訊的字典列表
    """
    text_display.delete(1.0, "end")
    if not contacts:
        text_display.insert("end", "沒有抓取到聯絡資訊。\n")
        return

    text_display.insert("end", f"{'姓名':<20}{'分機':<10}{'Email':<30}\n")
    text_display.insert("end", "-" * 60 + "\n")
    for contact in contacts:
        text_display.insert(
            "end", f"{contact['name']:<20}{contact['ext']:<10}{contact['email']:<30}\n"
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
        contacts = scrape_contacts(url)
        display_contacts(contacts)
        for contact in contacts:
            save_to_database(contact['name'], contact['ext'], contact['email'])
        messagebox.showinfo("成功", "聯絡資訊已成功抓取並儲存到資料庫。")
    except RuntimeError as e:
        messagebox.showerror("錯誤", str(e))


# 建立 Tkinter 主視窗
root = Tk()
root.title("聯絡資訊爬蟲")
root.geometry("640x480")

# 網址輸入框
url_var = StringVar(value="https://ai.ncut.edu.tw/p/412-1063-2382.php")
Label(root, text="URL:").grid(row=0, column=0, padx=10, pady=10, sticky="w")
url_entry = Entry(root, textvariable=url_var, width=50)
url_entry.grid(row=0, column=1, padx=10, pady=10, sticky="we")

# 抓取按鈕
fetch_button = Button(root, text="抓取", command=fetch_contacts)
fetch_button.grid(row=0, column=2, padx=10, pady=10)

# 顯示區域
text_display = ScrolledText(root, wrap="word", width=80, height=20)
text_display.grid(row=1, column=0, columnspan=3, padx=10, pady=10, sticky="nsew")

# 設定 grid 權重
root.grid_rowconfigure(1, weight=1)
root.grid_columnconfigure(1, weight=1)

# 初始化資料庫
setup_database()

# 啟動主事件循環
root.mainloop()
