import re
from bs4 import BeautifulSoup
import time
import os
import requests
from Crypto.Cipher import AES
import base64
import json
from pydub import AudioSegment

from download import PiecesProgressBar, url_save
class Tingbook:
  base_url = 'https://www.tingbook.cc/'
  user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0'
  headers = {
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',  # noqa
    'Accept-Charset': 'UTF-8,*;q=0.5',
    'Accept-Encoding': 'gzip,deflate,sdch',
    'Accept-Language': 'en-US,en;q=0.8',
    'User-Agent': user_agent
  }

  def pkcs7padding(self, text):
    """
    明文使用PKCS7填充
    """
    bs = 16
    length = len(text)
    bytes_length = len(text.encode('utf-8'))
    padding_size = length if (bytes_length == length) else bytes_length
    padding = bs - padding_size % bs
    padding_text = chr(padding) * padding
    coding = chr(padding)
    return {
        "coding": coding,
        "padding": text + padding_text
    }

  def input_info(self):
    book_id = input("悦听吧bookId:")
    if not book_id.strip():
      print("bookId不能为空")
      exit()
    if book_id.startswith('/'):
      book_id = book_id[1:]
    start_num = input("起始章节数【从1开始，默认第1章】：") or 1
    end_num = input("终止章节数【默认不限】") or -1
    start_chapter = int(start_num) - 1
    end_chapter = int(end_num)
    print(f"start:{start_chapter}, end{end_chapter}")
    if start_chapter < 0 or (start_chapter > end_chapter and end_chapter > 0):
      print("下载章节数字有误")
      exit()
    
    # cov_to_mp3 = input("是否将文件转换为mp3(1是/0否)：") or 1

    return book_id,start_chapter,end_chapter #,int(cov_to_mp3)



  def get_data_code(self, url):
    html = self.open_url(url)
    time.sleep(1)
    soup = BeautifulSoup(html, "html.parser")
    chapter_content = soup.find(name='div' ,class_='ting-list-content')
    srcs = chapter_content.find_all('a',attrs={"href": True, "title": True,'onclick':True})
    temp_list = list()
    for src in srcs:
      data_title = src.get('title')
      data_click = src.get('onclick')
      # print(f'data_click:{data_click.find('(\'')}:{data_click.find('\')')}')
      data_code = data_click[data_click.find('(\'')+2:data_click.find('\')')]
      temp_list.append([data_code,data_title])
    return temp_list

  def req_ting_serz(self, code):
    response = requests.get(f'{self.base_url}/api/app/docs-listen/{code}/ting-serz',
                             self.headers)
    # print(response.text)
    return response.text

  def open_url(self, url):
    print("访问悦听吧页面中.....")
    ytb.headers['Referer'] = url
    # print(ytb.headers)
    response = requests.get(url=url,headers=ytb.headers)
    response.raise_for_status()
    response.encoding = response.apparent_encoding
    content = response.text
    # print(concent)
    return content

  def get_book_title(self, content):
    soup = BeautifulSoup(content, "html.parser")
    title = soup.find('h2', class_='tx-title2 f-16 f-bold').text
    print(f'检测到书名：{title}')
    return soup, title

  # ['3a0a961a-7d86-ad0b-a6b6-2eab7d76a244', '000_作者自述：我创作这本书来源于一个契机']
  def get_chapter_list(self):
    content_soup = soup.find(name='div', attrs={'id':'yuedu'})
    chapter_soup = content_soup.find(name='ul', class_='ul-36')
    # print(chapter_soup)
    srcs = chapter_soup.find_all('a')
    temp_list = list()
    for src in srcs:
      data_href = src.get('href')
      data_title = src.text
      temp_list.append([self.base_url + data_href,data_title])
    # print(f'章节链接{temp_list}')
    return temp_list

  # {"Id":"3a0a961a-7d87-7c0e-1cfb-5cc1d2d67301",
  #   "BookId":"3a0a95d2-f731-d936-0363-fadbc2d27835",
  #   "TingNo":105,
  #   "FilePath":"http://117.65.18.37:50010/myfiles/host/listen/听书目录/清明上河图密码~冶文彪~读客熊猫君/ef9a3acb94ff455da461767185f24fef.m4a",
  #   "Title":"103_主动投案",
  #   "AsName":"pve1_nas_low",
  #   "PlaysServerUrl":"http://117.65.18.37:52001"}
  def decode_chapter_json(self, b64):
    secret_key = "le95G3hnFDJsBE+1/v9eYw=="
    iv = "IvswQFEUdKYf+d1wKpYLTg=="
    unpad = lambda s: s[0:-s[-1]]
    secret_key_de = base64.b64decode(secret_key)
    iv_de = base64.b64decode(iv)
    cipher = AES.new(secret_key_de, AES.MODE_CBC, iv_de)
    content = base64.b64decode(b64)
    c1 = unpad(cipher.decrypt(content)).decode('utf-8')
    return c1

  def get_download_list_json(self):
    f = open(os.path.join(title, 'download_list.json'), 'r',encoding='utf-8')
    content = f.read()
    json_list = json.loads(content)
    f.close()
    return json_list["list"]

  def remove_ext(self, str):
    (file, ext) = os.path.splitext(str)
    return file

  def check_not_exists_file(self, dir, download_list_json):
    filenames = os.listdir(os.path.join(title,'download'))
    file_list = list(filter(lambda f: os.path.isfile(os.path.join(dir,f)), filenames))
    file_list = list(map(lambda f: self.remove_ext(f), file_list))
    return list(filter(lambda f: not f['title'] in file_list, download_list_json))
    
  def save_download_list_json(self, download_json):
    # print('save_download_list_json')
    # print(download_json)
    save_json_path = os.path.join(title, 'download_list.json')
    if os.path.exists(save_json_path):
      os.remove(save_json_path)
    save_json = {"list": download_json}
    b = json.dumps(save_json)
    with open(os.path.join(title, 'download_list.json'), 'w',encoding='utf-8') as f:
      f.write(b)
      f.close()

  def get_download_list(self, chapter_list):
    download_list = list()
    pattern = re.compile(r"var now=(.*?);", re.MULTILINE | re.DOTALL)
    for cht in chapter_list:
      time.sleep(1)
      print(f'章节地址:{cht[0]}')
      cht_page = self.open_url(cht[0])
      cht_content = BeautifulSoup(cht_page, "html.parser")
      scripts = cht_content.find_all('script')
      # print(scripts)
      # print(len(scripts))
      for sc in scripts:
        if sc.text.count('var now=')>0:
          # print(sc)
          url = pattern.search(sc.prettify()).group(1)
          # print(url)
          download_list.append({'url':url.replace('"',''),'title':cht[1]})
    return download_list

  def download_book(self, src, dir_path, file_name):
    response = requests.get(src, self.headers)
    if not os.path.exists(os.path.join(dir_path,'download')):
      os.makedirs(os.path.join(dir_path,'download'))
    down_path = os.path.join(dir_path,'download', file_name)
    (file, ext) = os.path.splitext(down_path)
    while response.status_code != 200:
      response = requests.get(src, self.headers)
    with open(down_path, 'wb') as f:
      f.write(response.content)

  # def download_chapter(self, download_list):
  #   lock = Lock()
  #   dir_path = title
  #   count = len(download_list)
  #   for index, down_info in enumerate(download_list):
  #     chapter_title = down_info["title"] 
  #     (file, ext) = os.path.splitext(down_info["filePath"])
  #     down_path_ext = os.path.join(dir_path,'download', chapter_title + ext)
  #     # down_path_mp3 = os.path.join(dir_path, chapter_title + "mp3")
  #     if os.path.exists(down_path_ext):
  #       print(f'第{index+1}个章节 {chapter_title} 已存在，跳过.')
  #       continue
  #     time.sleep(1)
  #     lock.acquire()
  #     t = Thread(target=self.download_book, args=(down_info['filePath'], title, chapter_title + ext),
  #                 name=f'{chapter_title}')
  #     t.start()
  #     lock.release()
  #     print(f"第{index+1}个文件 [{chapter_title}] 下载完成，共{count}个章节")
  #     # convert(down_path_ext,ext)

  def download_chapter(self, download_list):
    for index, down_info in enumerate(download_list):
      time.sleep(3)
      chapter_title = down_info["title"] 
      bar = PiecesProgressBar(1,1)
      bar.update()
      # print(f'url == {parse.quote(url, safe=";/?:@&=+$,",encoding="utf-8")}')
      (file, ext) = os.path.splitext(down_info["url"])
      if ext == '.mp3':
        filepath = os.path.join(title,'mp3', chapter_title+ext)
      else:
        filepath = os.path.join(title,'download', chapter_title+ext)
      url_save(url = down_info['url'],
          filepath = filepath,
          bar=bar, refer=None, merge=True,
          faker=False, headers=self.headers)
      bar.done()
      # if not ext == '.mp3':
      #   self.convert(file, ext)

  def convert(self, filename, ext):
    # print(f'in convert filename {filename}')
    if ext != '.mp3':
      print(f'转换{filename + ext}为mp3格式')
      download_dir = os.path.join(title, 'download')
      to_path = os.path.join(download_dir, filename + ".mp3")

      form_path = os.path.join(title, filename+ext)
      print(f'将{filename}转换为mp3格式,file=[{filename}] 到[{to_path}]')
      audio = AudioSegment.from_file(form_path, format=ext)
      audio.export(to_path,format="mp3")


if __name__ == "__main__":
  ytb = Tingbook()
  book_id,start_chapter,end_chapter = ytb.input_info()
  time.sleep(1)
  content = ytb.open_url(f"{ytb.base_url}/show/{book_id}.html")
  time.sleep(1)
  soup, title = ytb.get_book_title(content)
  if not os.path.exists(title):
    print(f'创建文件夹{title}')
    os.makedirs(title)
  
  if not os.path.exists(os.path.join(title,'download')):
    os.makedirs(os.path.join(title,'download'))
  if not os.path.exists(os.path.join(title,'mp3')):
    os.makedirs(os.path.join(title,'mp3'))
  
  print(f'开始从网站上抓取章节信息')
  chapter_list = ytb.get_chapter_list()
  print(chapter_list)
  if end_chapter > 0:
    temp_list = chapter_list[start_chapter:end_chapter]
  else:
    temp_list = chapter_list[start_chapter:]
  print(f'有声读物《{title}》共找到 {len(chapter_list)} 个章节信息')
  print(f'需下载其中 [{temp_list[0][1]}] 至 [{temp_list[-1][1]}] 共 {len(temp_list)} 个章节')
  download_list = ytb.get_download_list(temp_list)
  print(f'有声读物《{title}》共找到 {len(download_list)} 个章节的下载地址')
  # ytb.save_download_list_json(download_list)
  ytb.download_chapter(download_list)
  print(f'已经完成 {title} [{temp_list[0][1]}] 至 [{temp_list[-1][1]}] 共 {len(temp_list)} 个章节的下载')


  # ytb.get_download_list([['https://www.tingbook.cc/jpplay/15227-0-40.html','asdf']])