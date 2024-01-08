# tingshu_spider
爬取下载有声小说
需安装bs4，Crypto，pydub

从悦听吧下载音频文件

例：
http://yuetingba.cn/book/detail/3a0a95d2-f731-d936-0363-fadbc2d27835/0

``` python
python .\yuetingba.py

悦听吧bookId: 3a0a95d2-f731-d936-0363-fadbc2d27835/0
起始章节数【从1开始，默认第1章】：
终止章节数【默认不限】
```
确认后从网页上爬取小说章节信息
['3a0a961a-7d86-ad0b-a6b6-2eab7d76a244', '000_作者自述']
根据章节code向服务器请求章节加密信息
解密后得到章节下载地址
```json
{
  "Id":"3a0a961a-7d87-7c0e-1cfb-5cc1d2d67301", 
  "BookId":"3a0a95d2-f731-d936-0363-fadbc2d27835",
  "TingNo":105,
  "FilePath":"http://117.65.18.37:50010/myfiles/host/listen/听书目录/清明上河图密码~冶文彪~读客熊猫君/ef9a3acb94ff455da461767185f24fef.m4a",
  "Title":"103_主动投案",
  "AsName":"pve1_nas_low",   
  "PlaysServerUrl":"http://117.65.18.37:52001"
}

```
将下载地址列表保存到 {小说名}/download_list.json

下载文件到{小说名}/download 目录中

如果download_list.json已存在，直接使用保存的url地址下载音频文件
