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

# 注意！不含 index.htm 喔！請自行設定！
url_prefix = 'https://www.wenku8.net/novel/3/3057/' # 預設是 敗北女角太多了

# 假的 headers 資訊
headers = {'user-agent': 'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/52.0.2743.116 Safari/537.36'}
cc = OpenCC('s2twp') # 簡中轉繁中

# A4 紙張設定 & 字型設定
a4_width, a4_height = A4
page_width = a4_width
page_height = a4_height
pdfmetrics.registerFont(TTFont('notoR', "font/NotoSansTC-Regular.ttf"))
pdfmetrics.registerFont(TTFont('notoB', "font/NotoSansTC-Bold.ttf"))
styles = getSampleStyleSheet()
styleNormalCustom = ParagraphStyle(
	'styleNormalCustom', fontName = 'notoR', fontSize = 10, leading = 20)
styleTitleCustom = ParagraphStyle(
	'styleTitleCustom', fontName = 'notoB', fontSize = 20, alignment = 'center')

# 獲取 url 的 html
def GetWebsite(url):
	html_text = requests.get(url, headers = headers)
	html_text.encoding = 'utf8'
	return html_text

# 將一張圖片存成 jpg
def InstallPicture(pic_cnt, pic_url):
	pic_info = requests.get(pic_url, headers = headers)
	picture_path = f'wenku/pic/pic_{pic_cnt}.jpg'
	with open(f'wenku/pic/pic_{pic_cnt}.jpg', 'wb') as f:
		f.write(pic_info.content)
	pic_cnt += 1
	time.sleep(0.5)
	return picture_path

story = []
# 將一張圖片放到 pdf 陣列上
def AppendPicture(picture_path):
	try:
		img = Image(picture_path)
		img_width, img_height = img.wrap(0, 0)	# 獲取原始圖片大小
		if img_width > page_width or img_height > page_height:
			scale_factor = max(img_width / page_width, img_height / page_height) + 1
			img.drawWidth = img_width / scale_factor
			img.drawHeight = img_height / scale_factor
		story.append(img)
		story.append(PageBreak())
	except Exception as e:
		print(e)
		print(f'找不到此圖片，路徑：{picture_path}')

# 前置作業
def FindNamesAndUrls():
	url = url_prefix + 'index.htm'
	# 進入目錄網站
	category_page = GetWebsite(url)

	soup = BeautifulSoup(category_page.content, 'lxml')
	catalog = soup.find('table', class_ = 'css')
	 
	table_data = catalog.find_all('td')
	
	# 每本書的篇章數（做前綴）
	title_cnt = 0
	title_gap = []
	for info in table_data:
		if info.has_attr('class'):
			if info['class'][0] == 'vcss':
				title_gap.append(title_cnt)
			elif info['class'][0] == 'ccss' and info.text.strip().replace(u'\xa0',''):
				title_cnt += 1
	title_gap.append(title_cnt)
	with open(f'wenku/title_gap.txt', 'w', encoding = 'utf-8') as f:
		for i in title_gap:
			f.write(f'{i}\n')

	# 篇章名稱
	titles = catalog.find_all('td', class_ = 'ccss')
	with open(f'wenku/title.txt', 'w', encoding = 'utf-8') as f:
		for title in titles:
			if title.a:
				title_name = title.text
				f.write(f"{title_name.replace(' ', '')}\n")
	 
	# 網址
	with open(f'wenku/website.txt', 'w', encoding = 'utf-8') as f:
		for title in titles:
			if title.a:
				title_web = title.a['href']
				f.write(f'{title_web}\n')
	 
	# 書名
	book_names = catalog.find_all('td', class_ = 'vcss')
	with open(f'wenku/book_name.txt', 'w', encoding = 'utf-8') as f:
		for book_name in book_names:
			f.write(f'{book_name.text}\n')

choose = [0] # 選擇的書籍

def AskToChoose():
	book_names = []
	with open(f'wenku/book_name.txt', 'r', encoding = 'utf-8') as f:
		book_names = f.readlines()
	book_id = 0
	for book_name in book_names:
		print(f"[{book_id}] {book_name.strip('\n')}")
		book_id += 1
	book_all = book_id
	print(f'[{book_all}] 我全都要')
	print(f'請輸入你想要的書籍編號 (可選多個): ', end = '')
	tmp = list(map(int, input().split()))
	choose.clear()
	if book_all in tmp:
		for i in range(book_all):
			choose.append(i)
	else:
		for i in tmp:
			choose.append(i)
	print(f'你想要的書籍是 ', end = '')
	for i in choose:
		print(f'[{i}]', end = ' ')
	print()
	return

def CatchAllInfo():
	titles = [] # 篇章名稱
	with open(f'wenku/title.txt', 'r', encoding = 'utf-8') as f:
		titles = f.readlines()
	book_names = [] # 書名
	with open(f'wenku/book_name.txt', 'r', encoding = 'utf-8') as f:
		book_names = f.readlines()
	title_gap = [] # 標題分界
	with open(f'wenku/title_gap.txt', 'r', encoding = 'utf-8') as f:
		title_gap = [int(line.strip()) for line in f] # 分界有 n + 1 個
	wait_second = 0 # 計算等待秒數
	for title_id in choose:
		wait_second += 2 * (title_gap[title_id + 1] - title_gap[title_id])
	print(f'請稍後...預計至少需要 {wait_second} 秒鐘...')
	
	pic_cnt = 0
	with open(f'wenku/website.txt', 'r') as f:
		websites = f.readlines() # 網址編碼
		for book_id in choose:
			for title_id in range(title_gap[book_id], title_gap[book_id + 1]):
				url = url_prefix + websites[title_id].strip('\n')
				page_text = GetWebsite(url)
				
				soup = BeautifulSoup(page_text.content, 'lxml')
				cur_page = soup.find('div', {'id': 'content'})
				if cur_page:
					cur_title = f'<< {cc.convert(titles[title_id].strip('\n'))} >>'
					story.append(Paragraph(cc.convert(cur_title), styleNormalCustom))
					story.append(Paragraph(f'\n', styleNormalCustom))
					pics = cur_page.find_all('div', class_ = 'divimage')
					if pics: # 是圖片
						for pic in pics:
							pic_url = pic.a["href"]
							picture_path = InstallPicture(pic_cnt, pic_url)
							pic_cnt += 1
							AppendPicture(picture_path)
					else: # 是文字
						for words in cur_page:
							if 'http://www.wenku8.com' not in words.text:
								line = words.text.strip().replace(' ', '').replace(u'\xa0','')
								if line:
									story.append(Paragraph(cc.convert(line), styleNormalCustom))
				time.sleep(2)
			# 創建 pdf
			fileName = f"wenku/pdf_file/{book_id}_{cc.convert(book_names[book_id].strip('\n'))}.pdf"
			pdfTemplate = SimpleDocTemplate(fileName, pagesize = A4)
			pdfTemplate.build(story)
			time.sleep(2)

### main code ###
# 建資料夾
try:
	os.mkdir('wenku')
except:
	pass
try:
	os.mkdir('wenku/novel_text')
except:
	pass
try:
	os.mkdir('wenku/pic')
except:
	pass
try:
	os.mkdir('wenku/pdf_file')
except:
	pass
FindNamesAndUrls()
AskToChoose()
CatchAllInfo()
