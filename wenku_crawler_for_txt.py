# 爬輕小說文庫 繁體中文
from bs4 import BeautifulSoup
import requests
import time
import os
from opencc import OpenCC

# 假的 headers 資訊
headers = {'user-agent': 'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/52.0.2743.116 Safari/537.36'}
cc = OpenCC('s2twp') # 簡中轉繁中

def get_websites(url):
	html_text = requests.get(url, headers = headers)
	html_text.encoding = 'utf8'
	return html_text

# 注意！不含 index.htm 喔！請自行設定！
novel_url = 'https://www.wenku8.net/novel/3/3057/' # 預設是 敗北女角太多了

def find_names_and_titles():
	url = novel_url + 'index.htm'
	# 進入網站
	html_text = get_websites(url)

	soup = BeautifulSoup(html_text.content, 'lxml')
	novel = soup.find('table', class_ = 'css')
	 
	table_data = novel.find_all('td')
	title_cnt = 0
	 
	# 每本書的篇章數
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
	titles = novel.find_all('td', class_ = 'ccss')
	with open(f'wenku/title.txt', 'w', encoding = 'utf-8') as f:
		for title in titles:
			ref = title.a
			if ref:
				title_name = title.text
				f.write(f"{title_name.replace(' ', '')}\n")
	 
	# 網址
	with open(f'wenku/website.txt', 'w', encoding = 'utf-8') as f:
		for title in titles:
			ref = title.a
			if ref:
				title_web = ref['href']
				f.write(f'{title_web}\n')
	 
	# 書名
	book_names = novel.find_all('td', class_ = 'vcss')
	with open(f'wenku/book_name.txt', 'w', encoding = 'utf-8') as f:
		for current_name in book_names:
			f.write(f'{current_name.text}\n')

choose = [0] # 選擇的書籍

def choose_the_books():
	book_names = []
	with open(f'wenku/book_name.txt', 'r', encoding = 'utf-8') as f:
		book_names = f.readlines()
	book_id = 0
	for book_name in book_names:
		print(f"[{book_id}] {book_name.strip('\n')}")
		book_id += 1
	print(f'[{book_id}] 全部')
	print(f'請輸入你想要的書籍編號 (可選多個): ', end = '')
	tmp = list(map(int, input().split()))
	choose.clear()
	if book_id in tmp:
		for i in range(book_id):
			choose.append(i)
	else:
		for i in tmp:
			choose.append(i)
	print(f'你想要的書籍是 ', end = '')
	for i in choose:
		print(f'[{i}]', end = ' ')
	print()
	return

def catch_text():
	titles = [] # 篇章名稱
	with open(f'wenku/title.txt', 'r', encoding = 'utf-8') as f:
		titles = f.readlines()
	book_names = [] # 書名
	with open(f'wenku/book_name.txt', 'r', encoding = 'utf-8') as f:
		book_names = f.readlines()
	title_gap = [] # 標題分界
	with open(f'wenku/title_gap.txt', 'r', encoding = 'utf-8') as f:
		title_gap = [int(line.strip()) for line in f] # 分界有 n + 1 個
	wait_second = 0
	for title_id in choose:
		wait_second += 2 * (title_gap[title_id + 1] - title_gap[title_id])
	print(f'請稍後...預計至少需要 {wait_second} 秒鐘...')
	 
	with open(f'wenku/website.txt', 'r') as f:
		websites = f.readlines() # 網址編碼
		try:
			os.mkdir('wenku/novel_text')
		except:
			pass
		for book_id in choose:
			with open(f'wenku/novel_text/{cc.convert(book_names[book_id].strip('\n'))}.txt', 'w', encoding = 'utf-8') as wr:
				for title_id in range(title_gap[book_id], title_gap[book_id + 1]):
					url = novel_url + websites[title_id].strip('\n')
					html_text = get_websites(url)
					 
					soup = BeautifulSoup(html_text.content, 'lxml')
					novel = soup.find('div', {'id': 'content'})
					if novel:
						wr.write(f'\n')
						wr.write(f"<< {cc.convert(titles[title_id].strip('\n'))} >>\n")
						wr.write(f'\n')
						for i in novel:
							if 'http://www.wenku8.com' not in i.text:
								line = i.text.strip().replace(' ', '').replace(u'\xa0','')
								if line:
									wr.write(f'{cc.convert(line)} \n')
					time.sleep(2)

### main code ###
find_names_and_titles()
choose_the_books()
catch_text()
