# 字幕与音视频

## 字幕优先

先检查 `yt-dlp` 是否存在；以下为公开、已授权且当前工具支持的单个链接命令，不保证任意站点成功。自动字幕和人工字幕的来源要区分。

```sh
yt-dlp --no-playlist --skip-download --write-subs --write-auto-subs --sub-langs "zh.*,en.*" --paths "一个新的临时目录" -o "%(id)s.%(ext)s" "视频链接"
```

查到字幕后先选一份合适语言的实际文件，检查时长覆盖，再规范化，不重复下载音频。若工具报告站点不支持、要求登录、验证或访问受限，停下说明，改用用户有权提供的字幕或媒体文件。不使用cookie提取或换代理绕过。

```sh
python3 "/技能实际安装路径/scripts/transcript.py" "输入字幕.vtt" "一个新的文字稿目录"
```

上述脚本输出文字稿与带时间段JSON；字幕未注明语言时标unknown，不根据文件后缀假设中文。保留原字幕文件作依据。字幕规范化不自动翻译，也不宣称已经人工校对。

## 没有字幕

若有权下载媒体且工具支持，可先只下音频：

```sh
yt-dlp --no-playlist -x --audio-format m4a --paths "一个新的临时目录" -o "%(id)s.%(ext)s" "视频链接"
```

这一步需要 `yt-dlp` 和 `ffmpeg`。本地音视频无需重新下载；faster-whisper可以解码本地媒体。只有已经安装好faster-whisper并准备好模型时运行：

```sh
python3 "/技能实际安装路径/scripts/transcript.py" "输入音视频.mp4" "一个新的文字稿目录" --model-dir "/已下载的faster-whisper模型目录"
```

脚本使用CPU/int8，慢速机器不适合现场跑长音频。不会自动拉取模型、上传文件或收费。首次准备模型可能需要联网、大量空间和时间，应提前完成并用短音频试跑，避免在正式任务中临时下载。缺依赖时可先用字幕样例验证；这证明字幕流程，不代表语音转写已实测。

不强行指定中文：省略 `--language` 时识别原语言。需要中文译文时另存翻译，保留原语言文字稿与时间段；人名、数字、否定词需要抽查。

## 云端是另选方案

本包不提供付费云API调用脚本，也不自动上传OSS。用户明确选择云转写时，再核对当前官方接口、费用与数据处理要求；一次性说明将上传什么、发给哪家服务，再按用户授权操作。API Key不写入技能包、提示词或截图，认证失败不静默降级或换服务。

上游依据：[yt-dlp 参数](https://github.com/yt-dlp/yt-dlp#subtitle-options)、[faster-whisper 用法](https://github.com/SYSTRAN/faster-whisper#usage)。
