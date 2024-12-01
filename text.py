import requests
import re

def scrape_contacts(url: str) -> list[dict]:
    """
    從指定的 URL 抓取聯絡資訊。
    參數: url (str): 網頁的 URL。
    回傳: list[dict]: 包含聯絡資訊的字典列表，每個字典包含 'name', 'ext', 和 'email'。
    """
    try:
        # 設定超時為 10 秒
        response = requests.get(url, timeout=10)
        response.raise_for_status()  # 檢查是否為 200 OK
    except requests.Timeout:
        raise RuntimeError("抓取網頁超時，請檢查網絡連接。")
    except requests.RequestException as e:
        raise RuntimeError(f"無法抓取資料: {e}")

    html_content = response.text

    # 正則表達式提取聯絡資訊
    pattern = re.compile(
        r'<div class="mtitle">.*?<a.*?>(.*?)</a>.*?</div>.*?<p>(.*?)</p>.*?<p>(.*?)</p>',
        re.DOTALL
    )
    matches = pattern.findall(html_content)

    contacts = []
    for match in matches:
        contacts.append({
            "name": match[0].strip(),
            "email": match[1].strip(),
            "ext": match[2].strip() if match[2] else "無分機"
        })

    if not contacts:
        raise RuntimeError("未能從頁面中提取聯絡資訊，請檢查網頁格式。")

    return contacts


def display_contacts(contacts: list[dict]) -> None:
    """
    顯示抓取到的聯絡資訊。
    contacts (list[dict]): 包含聯絡資訊的字典列表。
    """
    if not contacts:
        print("沒有抓取到聯絡資訊。")
        return

    print(f"{'姓名':<20}{'分機':<10}{'Email':<30}")
    print("-" * 60)
    for contact in contacts:
        print(f"{contact['name']:<20}{contact['ext']:<10}{contact['email']:<30}")


def main():
    url = input("請輸入網址：")
    if not url:
        print("請提供有效的 URL。")
        return

    try:
        contacts = scrape_contacts(url)
        display_contacts(contacts)
    except RuntimeError as e:
        print(f"錯誤: {e}")


if __name__ == "__main__":
    main()
