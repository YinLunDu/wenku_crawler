########## 爬輕小說文庫 繁體中文 ##########
######## update python to 3.12.6 ########
##### 注意！需要下載字體資料夾 font！ #####
from bs4 import BeautifulSoup
import requests
import time
import os
from opencc import OpenCC
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import SimpleDocTemplate, Paragraph, Image as ReportImage, PageBreak, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import Spacer

# 常量設定
URL_PREFIX = 'https://www.wenku8.net/novel/3/3057/'  # 輕小說文庫預設網址
HEADERS = {'user-agent': 'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/52.0.2743.116 Safari/537.36'}
FONT_PATH = "font/NotoSansTC-"
DATA_DIR = 'wenku'
OUTPUT_DIRS = ['novel_text', 'pic', 'pdf_file']
PAGE_WIDTH, PAGE_HEIGHT = A4
cc = OpenCC('s2twp')  # 簡中轉繁中

# 字型與樣式設定
pdfmetrics.registerFont(TTFont('notoR', f"{FONT_PATH}Regular.ttf"))
pdfmetrics.registerFont(TTFont('notoB', f"{FONT_PATH}Bold.ttf"))
styles = getSampleStyleSheet()
style_normal = ParagraphStyle('styleNormal', fontName='notoR', fontSize=10, leading=20)
style_title = ParagraphStyle('styleTitle', fontName='notoB', fontSize=13, alignment=1)

def fetch_website_content(url):
    response = requests.get(url, headers=HEADERS)
    response.encoding = 'utf8'
    return response

def save_image_to_file(pic_cnt, pic_url):
    response = requests.get(pic_url, headers=HEADERS)
    image_path = f'wenku/pic/pic_{pic_cnt}.jpg'
    with open(image_path, 'wb') as f:
        f.write(response.content)
    time.sleep(0.5)
    return image_path

def append_image_to_story(image_path, story):
    try:
        img = Image(image_path)
        img_width, img_height = img.wrap(0, 0)
        if img_width > PAGE_WIDTH or img_height > PAGE_HEIGHT:
            scale_factor = max(img_width / PAGE_WIDTH, img_height / PAGE_HEIGHT) + 1
            img.drawWidth = img_width / scale_factor
            img.drawHeight = img_height / scale_factor
        story.append(img)
        story.append(PageBreak())
    except Exception as e:
        print(f"Error: {e} - Path: {image_path}")

def find_names_and_urls():
    category_page = fetch_website_content(f"{URL_PREFIX}index.htm")
    soup = BeautifulSoup(category_page.content, 'lxml')
    catalog = soup.find('table', class_='css')
    table_data = catalog.find_all('td')

    title_cnt = 0
    title_gap = []
    for info in table_data:
        if info.get('class'):
            if 'vcss' in info['class']:
                title_gap.append(title_cnt)
            elif 'ccss' in info['class'] and info.text.strip().replace(u'\xa0', ''):
                title_cnt += 1
    title_gap.append(title_cnt)

    save_to_file('title_gap.txt', '\n'.join(map(str, title_gap)))
    titles = [title.text.replace(' ', '') for title in catalog.find_all('td', class_='ccss') if title.a]
    save_to_file('title.txt', '\n'.join(titles))

    websites = [title.a['href'] for title in catalog.find_all('td', class_='ccss') if title.a]
    save_to_file('website.txt', '\n'.join(websites))

    book_names = [book.text for book in catalog.find_all('td', class_='vcss')]
    save_to_file('book_name.txt', '\n'.join(book_names))

def save_to_file(filename, content):
    with open(os.path.join(DATA_DIR, filename), 'w', encoding='utf-8') as f:
        f.write(content)

chosen = []

def prompt_user_to_choose():
    book_names = load_from_file('book_name.txt')
    for i, name in enumerate(book_names):
        print(f"[{i}] {name.strip()}")
    print(f"[{len(book_names)}] 我全都要")
    tmp = list(map(int, input("Enter book numbers to choose (multiple choices allowed): ").split()))
    
    if len(book_names) in tmp:
        for i in range(len(book_names)):
            chosen.append(i)
    else:
        for i in tmp:
            chosen.append(i)
    return

def load_from_file(filename):
    with open(os.path.join(DATA_DIR, filename), 'r', encoding='utf-8') as f:
        return f.readlines()

def download_content():
    titles = load_from_file('title.txt')
    book_names = load_from_file('book_name.txt')
    title_gaps = list(map(int, load_from_file('title_gap.txt')))
    websites = load_from_file('website.txt')
    story = []
    for book_id in chosen:
        for title_id in range(title_gaps[book_id], title_gaps[book_id + 1]):
            url = URL_PREFIX + websites[title_id].strip()
            page_content = fetch_website_content(url)
            soup = BeautifulSoup(page_content.content, 'lxml')
            content = soup.find('div', {'id': 'content'})
            if content:
                cur_title = f'<< {cc.convert(titles[title_id].strip('\n'))} >>\n'
                story.append(Spacer(1, 0.2 * inch))
                story.append(Paragraph(f'{cc.convert(cur_title)}\n', style_title))
                story.append(Spacer(1, 0.3 * inch))
                process_content(content, story)
            time.sleep(2)
        generate_pdf(story, book_names[book_id].strip(), book_id)
        story.clear()

def process_content(content, story):
    pics = content.find_all('div', class_='divimage')
    pic_cnt = 0
    if pics:
        for pic in pics:
            img_path = save_image_to_file(pic_cnt, pic.a["href"])
            pic_cnt += 1
            append_image_to_story(img_path, story)
    else:
        for _text in content:
            if 'http://www.wenku8.com' not in _text.text:
                line = _text.text.strip().replace(' ', '').replace(u'\xa0', '')
                if line:
                    story.append(Paragraph(cc.convert(line), style_normal))

def generate_pdf(story, book_name, book_id):
    filename = f'wenku/pdf_file/{book_id}_{cc.convert(book_name)}.pdf'
    pdf_template = SimpleDocTemplate(filename, pagesize=A4)
    pdf_template.build(story)

def main():
    os.makedirs(DATA_DIR, exist_ok=True)
    for directory in OUTPUT_DIRS:
        os.makedirs(os.path.join(DATA_DIR, directory), exist_ok=True)

    find_names_and_urls()
    prompt_user_to_choose()
    download_content()

if __name__ == "__main__":
    main()
