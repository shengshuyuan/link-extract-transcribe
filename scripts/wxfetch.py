#!/usr/bin/env python3
"""Extract a public WeChat article into a NEW output directory. No browser extension."""
import argparse
import datetime as dt
import hashlib
import html
import json
from pathlib import Path
import re
import sys
from urllib.parse import urljoin, urlsplit, urldefrag

HEADERS = {'User-Agent': 'Mozilla/5.0', 'Accept-Language': 'zh-CN,zh;q=0.9'}
PAGE_HOSTS = {'mp.weixin.qq.com'}
IMAGE_HOSTS = {'mmbiz.qpic.cn', 'mmbiz.qlogo.cn'}
MAX_IMAGE_DOWNLOADS = 20
MAX_IMAGE_BYTES = 32 * 1024 * 1024

def checked_url(url, hosts):
    p = urlsplit(url)
    if p.scheme not in ('http', 'https') or p.hostname not in hosts or p.username or p.password or p.port not in (None, 80, 443):
        raise ValueError('仅支持公开微信文章地址或微信图片 CDN；不访问其他主机')
    return urldefrag(url)[0]

def download(url, hosts, limit, image=False):
    import requests
    for _ in range(6):
        url = checked_url(url, hosts)
        with requests.get(url, headers=HEADERS, timeout=(10, 25), stream=True, allow_redirects=False) as r:
            if r.status_code in (301,302,303,307,308):
                url = checked_url(urljoin(url, r.headers.get('Location','')), hosts)
                continue
            r.raise_for_status()
            mime = r.headers.get('Content-Type','').split(';')[0].lower()
            if image and mime not in {'image/jpeg','image/png','image/gif','image/webp'}:
                raise ValueError('图片返回的内容类型不是受支持的图片')
            if not image and mime not in {'text/html','application/xhtml+xml'}:
                raise ValueError('文章返回的内容类型不是 HTML')
            data=bytearray()
            for chunk in r.iter_content(65536):
                data.extend(chunk)
                if len(data)>limit: raise ValueError('响应过大，已停止下载')
            if image:
                raw=bytes(data)
                if not (raw.startswith((b'\xff\xd8\xff',b'\x89PNG\r\n\x1a\n',b'GIF87a',b'GIF89a')) or (raw.startswith(b'RIFF') and raw[8:12]==b'WEBP')):
                    raise ValueError('图片签名与内容不符')
            return bytes(data), mime, url
    raise ValueError('跳转次数过多')

def js_var(src, name):
    m=re.search(r'var\s+'+re.escape(name)+r'\s*=\s*(?:htmlDecode\()?"((?:\\.|[^"\\])*)"',src)
    if not m:return ''
    try:return html.unescape(json.loads('"'+m[1]+'"'))
    except json.JSONDecodeError:return html.unescape(m[1])

def parse_article(src,url):
    from bs4 import BeautifulSoup
    from markdownify import markdownify
    soup=BeautifulSoup(src,'html.parser')
    content=soup.find(id='js_content')
    if content is None or not content.get_text(strip=True):
        raise ValueError('未取得正文：页面可能需要验证、已删除或仅包含图片。请提供有权使用的正文；不绕过验证')
    def meta(prop):
        node=soup.find('meta',attrs={'property':prop})
        return node.get('content','').strip() if node else ''
    title=meta('og:title') or js_var(src,'msg_title') or '未提供标题'
    ct=re.search(r'var\s+ct\s*=\s*["\x27]?(\d+)',src)
    published=''
    if ct:
        published=dt.datetime.fromtimestamp(int(ct[1]),dt.timezone(dt.timedelta(hours=8))).isoformat()
    for node in content.find_all(['script','style','iframe']):node.decompose()
    images=[]
    for img in content.find_all('img'):
        image_url=img.get('data-src') or img.get('src')
        if not image_url or image_url.startswith('data:'):
            img.decompose();continue
        image_url=urljoin(url,image_url);images.append(image_url);img['src']=image_url
    for a in content.find_all('a',href=True):
        target=urljoin(url,a['href'])
        if urlsplit(target).scheme in ('http','https'):a['href']=target
        else:del a['href']
    body=markdownify(str(content),heading_style='ATX')
    body=re.sub(r'\n{3,}','\n\n',body).strip()
    return {'title':title,'account':js_var(src,'nickname'),'author':meta('og:article:author') or js_var(src,'author'),
            'published':published,'source':url,'images':images,'markdown':body,
            'scope':'提取到的页面正文；完整性尚需核对','image_failures':[]}

def save_article(data,outdir,download_images=False):
    out=Path(outdir)
    out.mkdir(parents=True,exist_ok=False)  # Never overwrite a previous extraction or vault note.
    if download_images:
        used_bytes = 0
        for index, url in enumerate(dict.fromkeys(data['images'])):
            try:
                if index >= MAX_IMAGE_DOWNLOADS:
                    raise ValueError('已达到图片下载数量上限，保留远程链接')
                remaining = MAX_IMAGE_BYTES - used_bytes
                if remaining <= 0:
                    raise ValueError('已达到图片下载总大小上限，保留远程链接')
                raw,mime,_=download(url,IMAGE_HOSTS,min(12*1024*1024, remaining),image=True)
                if len(raw) > remaining:
                    raise ValueError('图片超过剩余总大小，保留远程链接')
                used_bytes += len(raw)
                ext={'image/jpeg':'jpg','image/png':'png','image/gif':'gif','image/webp':'webp'}[mime]
                name='images/'+hashlib.sha256(url.encode()).hexdigest()[:16]+'.'+ext
                (out/'images').mkdir(exist_ok=True)
                (out/name).write_bytes(raw)
                data['markdown']=data['markdown'].replace(url,name)
            except Exception as exc:
                data['image_failures'].append({'url':url,'error':str(exc)})
    front='\n'.join(k+': '+json.dumps(data[k],ensure_ascii=False) for k in ['title','account','author','published','source','scope'])
    (out/'article.md').write_text('---\n'+front+'\n---\n\n# '+data['title']+'\n\n'+data['markdown']+'\n',encoding='utf-8')
    (out/'article.json').write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')
    return out

def fetch(url,outdir,download_images=False):
    checked_url(url,PAGE_HOSTS)
    if Path(outdir).exists():raise FileExistsError('输出目录已存在，请换一个新目录；不会覆盖原文件')
    raw,_,final=download(url,PAGE_HOSTS,8*1024*1024)
    data=parse_article(raw.decode('utf-8',errors='replace'),final)
    save_article(data,outdir,download_images)
    return data

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('url');p.add_argument('outdir',help='必须是尚不存在的新目录')
    p.add_argument('--download-images',action='store_true')
    args=p.parse_args()
    try:
        d=fetch(args.url,args.outdir,args.download_images)
        print(json.dumps({'status':'extracted_unreviewed','title':d['title'],'chars':len(d['markdown']),'image_failures':len(d['image_failures']),'output':str(Path(args.outdir).resolve())},ensure_ascii=False))
    except Exception as e:
        print(json.dumps({'status':'error','message':str(e)},ensure_ascii=False),file=sys.stderr);return 1
    return 0
if __name__=='__main__':
    from web_runtime import use_web_environment
    use_web_environment(__file__)
    sys.exit(main())
