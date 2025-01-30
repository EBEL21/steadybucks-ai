from bs4 import BeautifulSoup
import requests
import urllib.parse

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36"}


def fetch_html(url: str) -> BeautifulSoup:
    """Fetch the HTML content of a URL and return a BeautifulSoup object."""
    response = requests.get(url, headers=HEADERS)
    response.raise_for_status()
    return BeautifulSoup(response.text, 'html.parser')


def convert_real_news_link(news_link: str) -> str:
    # Parse the URL and extract query parameters
    parsed_url = urllib.parse.urlparse(news_link)
    query_params = urllib.parse.parse_qs(parsed_url.query)
    # Extract relevant parameters
    article_id = query_params.get('article_id', [None])[0]
    office_id = query_params.get('office_id', [None])[0]
    converted_link = f"https://n.news.naver.com/mnews/article/{office_id}/{article_id}"
    return converted_link


def extract_news_links(url: str) -> list:
    """Extract news links from the main news list."""
    link_prefix = "https://finance.naver.com"
    news_links = []

    soup = fetch_html(url)
    news_list = soup.select("div.mainNewsList._replaceNewsLink ul.newsList li.block1")
    for news_item in news_list:
        link_tag = news_item.select_one("dd.articleSubject a")
        if link_tag:
            news_links.append(convert_real_news_link(link_prefix + link_tag["href"]))

    return news_links

def extract_num_pagination(url: str) -> int:
    """Extract pagination links to iterate through pages."""
    # pagination_links = [a["href"] for an in soup.select("table.Nnavi td a") if "href" in a.attrs]
    soup = fetch_html(url)
    next_page = soup.select_one("table.Nnavi td.pgRR a")
    next_page_link = next_page["href"] if next_page else None
    last_page = next_page_link.split("=")[-1]

    return last_page


def extract_news_text(url: str) -> str:
    """Extract clean text from HTML with custom tag handling."""
    soup = fetch_html(url)
    content = soup.find("article", id="dic_area")  # 기사 내용의 부모 태그

    def process_element(element):
        """Recursive function to process each element and extract text."""
        summary = []
        clean_text = []
        for idx, child in enumerate(element.children):
            if child.name == "span":
                if child.attrs.get("data-type") == "ore":
                    # <span> 태그 처리: data-type이 'ore'인 경우 내부 텍스트 유지
                    clean_text.append(child.get_text(strip=True))
                else:
                    strong_tag = child.find("strong")
                    if strong_tag:
                        strong_text = strong_tag.get_text(separator="\n", strip=True)
                        summary.append(strong_text)
            elif child.name == "br":
                # <br> 태그 처리: 줄바꿈 기호로 치환
                clean_text.append("\n")
            elif child.string:
                if not child.string.strip().endswith("//"):
                    # 일반 텍스트 노드 처리
                    clean_text.append(child.string.strip())
            elif child.name:  # 다른 태그는 재귀적으로 처리
                clean_text.append(process_element(child))
        return "".join(clean_text), "".join(summary)

    return process_element(content) if content else ""


if __name__ == '__main__':
    page_num = extract_num_pagination("https://finance.naver.com/news/mainnews.naver")
    news_link_list = []
    for i in range(int(page_num)):
        page_news_link = "https://finance.naver.com/news/mainnews.naver?" + f"&page={i + 1}"
        news_link_list += extract_news_links(page_news_link)
    print(news_link_list)

    news = extract_news_text(news_link_list[0])
    print(news)

