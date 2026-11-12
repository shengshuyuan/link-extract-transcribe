#!/usr/bin/env python3
"""Normalize SRT/VTT or transcribe local media with an already-downloaded faster-whisper model."""
import argparse,html,json,re,sys
from pathlib import Path

def subtitles(text):
    segments=[]
    pattern=r'(?m)^\s*((?:\d{2}:)?\d{2}:\d{2}[,.]\d{3})\s*-->\s*((?:\d{2}:)?\d{2}:\d{2}[,.]\d{3})[^\n]*\n([\s\S]*?)(?=\n\s*\n|\Z)'
    for m in re.finditer(pattern,text):
        body=html.unescape(re.sub('<[^>]+>','',m[3])).strip()
        if body:segments.append({'start':m[1].replace(',','.'),'end':m[2].replace(',','.'),'text':body})
    if not segments:raise ValueError('未读到有效的SRT/VTT字幕；请提供完整字幕或改用语音转写')
    return segments

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('input');p.add_argument('outdir',help='必须是尚不存在的新目录')
    p.add_argument('--model-dir',help='已下载的 faster-whisper 模型目录；脚本不会下载模型')
    p.add_argument('--language',help='如 zh；省略时自动识别，不强行当成中文')
    a=p.parse_args();out=Path(a.outdir);src=Path(a.input)
    try:
        if out.exists():raise FileExistsError('输出目录已存在，不会覆盖原文件')
        if not src.is_file():raise ValueError('输入文件不存在')
        if src.suffix.lower() in {'.srt','.vtt'}:
            segments=subtitles(src.read_text(encoding='utf-8-sig'));method='provided_subtitles';language='unknown'
        else:
            if not a.model_dir or not Path(a.model_dir).is_dir():raise ValueError('无字幕时需要预先安装faster-whisper并准备模型目录；不会自动下载或上传音频')
            from faster_whisper import WhisperModel
            model=WhisperModel(a.model_dir,device='cpu',compute_type='int8',local_files_only=True)
            stream,info=model.transcribe(str(src),language=a.language)
            segments=[{'start':x.start,'end':x.end,'text':x.text.strip()} for x in stream if x.text.strip()]
            if not segments:raise ValueError('没有识别到可用语音，不生成假文字稿')
            language=info.language;method='faster-whisper-local'
        out.mkdir(parents=True,exist_ok=False)
        (out/'transcript.txt').write_text('\n\n'.join(x['text'] for x in segments)+'\n',encoding='utf-8')
        data={'input_name':src.name,'method':method,'language':language,'review_status':'待核对','segments':segments}
        (out/'transcript.json').write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')
        print(json.dumps({'status':'transcribed_unreviewed','method':method,'segments':len(segments),'output':str(out.resolve())},ensure_ascii=False))
    except Exception as exc:
        print(json.dumps({'status':'error','message':str(exc)},ensure_ascii=False),file=sys.stderr);return 1
    return 0
if __name__=='__main__':sys.exit(main())
