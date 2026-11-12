import importlib.util,json,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
import yaml
ROOT=Path(__file__).resolve().parents[1]/'scripts'
def module(name):
 spec=importlib.util.spec_from_file_location(name,ROOT/(name+'.py'));m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
wx=module('wxfetch');tr=module('transcript')
class ExtractionTests(unittest.TestCase):
 def fixture(self):
  return '''<meta property="og:title" content="标题: &quot;引号&quot;"><script>var ct = "0"; var nickname = htmlDecode("测试&amp;账号");</script><div id="js_content"><p>正文里可以提及环境异常，不应误报。</p><a href="/s/next">相关</a><script>bad()</script><img data-src="https://mmbiz.qpic.cn/x"></div>'''
 def test_metadata_and_relative_link(self):
  d=wx.parse_article(self.fixture(),'https://mp.weixin.qq.com/s/test')
  self.assertEqual(d['published'],'1970-01-01T08:00:00+08:00');self.assertEqual(d['account'],'测试&账号')
  self.assertNotIn('bad()',d['markdown']);self.assertIn('https://mp.weixin.qq.com/s/next',d['markdown'])
  with tempfile.TemporaryDirectory() as t:
   out=Path(t)/'new';wx.save_article(d,out)
   meta=yaml.safe_load((out/'article.md').read_text().split('---')[1]);self.assertEqual(meta['title'],d['title'])
   original=(out/'article.md').read_bytes()
   with self.assertRaises(FileExistsError):wx.save_article(d,out)
   self.assertEqual((out/'article.md').read_bytes(),original)
 def test_blocked_or_empty_body(self):
  for s in ['<p>需要验证</p>','<div id="js_content"></div>']:
   with self.assertRaises(ValueError):wx.parse_article(s,'https://mp.weixin.qq.com/s/x')
 def test_other_hosts_rejected(self):
  for u in ['file:///tmp/private','http://127.0.0.1/x','https://mp.weixin.qq.com.evil/x','https://user:secret@mp.weixin.qq.com/x']:
   with self.assertRaises(ValueError):wx.checked_url(u,wx.PAGE_HOSTS)
 def test_conflict_checked_before_network(self):
  with tempfile.TemporaryDirectory() as t,patch.object(wx,'download') as download:
   with self.assertRaises(FileExistsError):wx.fetch('https://mp.weixin.qq.com/s/x',t)
   download.assert_not_called()
 def test_redirect_to_other_host_blocked(self):
  import requests
  class R:
   status_code=302;headers={'Location':'http://127.0.0.1/private'}
   def __enter__(self):return self
   def __exit__(self,*args):pass
  with patch.object(requests,'get',return_value=R()) as get:
   with self.assertRaises(ValueError):wx.download('https://mp.weixin.qq.com/s/x',wx.PAGE_HOSTS,100)
   self.assertEqual(get.call_count,1)
 def test_failed_image_is_not_claimed_downloaded(self):
  d=wx.parse_article(self.fixture(),'https://mp.weixin.qq.com/s/x')
  with tempfile.TemporaryDirectory() as t,patch.object(wx,'download',side_effect=ValueError('not an image')):
   out=Path(t)/'extract';wx.save_article(d,out,True)
   self.assertEqual(len(d['image_failures']),1);self.assertIn('https://mmbiz.qpic.cn/x',d['markdown']);self.assertFalse((out/'images').exists())
 def test_images_deduplicate_and_limit_attempts(self):
  d=wx.parse_article(self.fixture(),'https://mp.weixin.qq.com/s/x')
  a='https://mmbiz.qpic.cn/a';b='https://mmbiz.qpic.cn/b'
  d['images']=[a,a,b];d['markdown']=f'![]({a}) ![]({a}) ![]({b})'
  with tempfile.TemporaryDirectory() as t,patch.object(wx,'MAX_IMAGE_DOWNLOADS',1),patch.object(wx,'download',return_value=(b'png','image/png',a)) as download:
   wx.save_article(d,Path(t)/'new',True)
   self.assertEqual(download.call_count,1);self.assertEqual(len(d['image_failures']),1)
   self.assertNotIn(a,d['markdown']);self.assertIn(b,d['markdown'])
 def test_images_share_total_byte_budget(self):
  d=wx.parse_article(self.fixture(),'https://mp.weixin.qq.com/s/x')
  d['images']=['https://mmbiz.qpic.cn/a','https://mmbiz.qpic.cn/b']
  with tempfile.TemporaryDirectory() as t,patch.object(wx,'MAX_IMAGE_BYTES',3),patch.object(wx,'download',return_value=(b'png','image/png','')) as download:
   wx.save_article(d,Path(t)/'new',True)
   self.assertEqual(download.call_count,1);self.assertEqual(download.call_args.args[2],3)
   self.assertEqual(len(d['image_failures']),1)
 def test_subtitles_keep_timing_and_original_language(self):
  d=tr.subtitles('WEBVTT\n\n00:00:01.000 --> 00:00:03.000\n<b>Hello</b> &amp; welcome\n\n00:00:03.000 --> 00:00:05.000\n再见\n')
  self.assertEqual(len(d),2);self.assertEqual(d[0]['text'],'Hello & welcome');self.assertEqual(d[1]['start'],'00:00:03.000')
 def test_empty_subtitle_is_failure(self):
  with self.assertRaises(ValueError):tr.subtitles('WEBVTT\n')

class SetupTests(unittest.TestCase):
 def test_readonly_check_does_not_create_environment(self):
  import subprocess,sys
  with tempfile.TemporaryDirectory() as t:
   env=Path(t)/'not-created'
   result=subprocess.run([sys.executable,str(ROOT/'setup_web.py'),'--venv',str(env)],capture_output=True,text=True)
   self.assertEqual(result.returncode,1);self.assertFalse(env.exists());self.assertFalse(json.loads(result.stdout)['ready'])
 def test_install_refuses_existing_non_environment(self):
  import subprocess,sys
  with tempfile.TemporaryDirectory() as t:
   env=Path(t)/'existing';env.mkdir();sentinel=env/'keep.txt';sentinel.write_text('keep')
   result=subprocess.run([sys.executable,str(ROOT/'setup_web.py'),'--install','--venv',str(env)],capture_output=True,text=True)
   self.assertEqual(result.returncode,1);self.assertEqual(sentinel.read_text(),'keep');self.assertFalse((env/'bin').exists())


class RuntimeTests(unittest.TestCase):
 def test_system_python_uses_prepared_environment(self):
  import types
  runtime=module('web_runtime')
  with tempfile.TemporaryDirectory() as t:
   home=Path(t);venv=home/'.workbuddy/venvs/link-extract';exe=venv/'bin/python';exe.parent.mkdir(parents=True);exe.touch()
   fake=types.SimpleNamespace(prefix='/system',base_prefix='/system',platform='darwin',argv=['wxfetch.py','URL','out'])
   with patch.object(runtime.Path,'home',return_value=home),patch.object(runtime,'sys',fake),patch.object(runtime.os,'execv') as execute:
    runtime.use_web_environment('/skill/wxfetch.py')
    execute.assert_called_once_with(str(exe),[str(exe),'/skill/wxfetch.py','URL','out'])
 def test_explicit_virtual_environment_is_respected(self):
  import types
  runtime=module('web_runtime');fake=types.SimpleNamespace(prefix='/custom',base_prefix='/system',platform='darwin',argv=['doctor.py'])
  with patch.object(runtime,'sys',fake),patch.object(runtime.os,'execv') as execute:
   runtime.use_web_environment('/skill/doctor.py');execute.assert_not_called()
 def test_missing_environment_does_not_install(self):
  import types
  runtime=module('web_runtime');fake=types.SimpleNamespace(prefix='/system',base_prefix='/system',platform='darwin',argv=['doctor.py'])
  with tempfile.TemporaryDirectory() as t,patch.object(runtime.Path,'home',return_value=Path(t)),patch.object(runtime,'sys',fake),patch.object(runtime.os,'execv') as execute:
   runtime.use_web_environment('/skill/doctor.py');execute.assert_not_called();self.assertFalse((Path(t)/'.workbuddy').exists())

if __name__=='__main__':unittest.main()
