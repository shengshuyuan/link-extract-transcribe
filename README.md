# link-extract-transcribe

在 WorkBuddy 中提取链接、字幕和本地音视频内容，再按 Obsidian 笔记库的规则整理、分类和保存。不需要浏览器剪藏插件。

这是一个 **AI 技能 + Python 辅助脚本**，需要 WorkBuddy 等支持技能的助手执行提炼和入库流程；不是独立的全站爬虫或 Obsidian 插件。

## 能做什么

| 材料 | 处理方式 | 需要准备 |
|---|---|---|
| 公开公众号文章 | 提取实际读到的正文和元数据，可选下载图片 | Python 3.10+ 和网页依赖 |
| 普通网页 | 使用助手当前可用的网页读取能力 | 宿主提供读取工具；本包没有通用网页抓取脚本 |
| 本地文本、Markdown | 助手直接读取后整理 | 支持本地文件读取的助手 |
| SRT / VTT 字幕 | 规范化文字稿，保留时间段 | Python 3.10+，不需要语音模型 |
| 平台视频、播客 | 优先使用可取得的字幕 | 可选 yt-dlp；下载音频另需 ffmpeg |
| 本地音视频 | 使用本地 faster-whisper 转写 | 另装 faster-whisper，准备已下载的模型目录 |

网页或平台有登录、验证码、付费限制时可能无法读取。脚本不绕过验证，不提取浏览器 Cookie，不自动下载语音模型、上传媒体或调用付费接口。语音转写和平台支持需要在自己的环境中验证。

## 安装到 WorkBuddy

1. 下载 [技能安装包](dist/link-extract-transcribe-workbuddy.zip)。不要把整个 GitHub 源码 ZIP 当成技能包上传。
2. 在 WorkBuddy 的技能页面，通过添加/上传技能入口导入 ZIP，完成检测并启用。入口名称随客户端版本可能不同。
3. 新开一个对话，选择 `link-extract-transcribe`。请助手定位技能实际安装目录并补齐网页环境：

```text
请定位 link-extract-transcribe 的实际安装目录，检查 Python 是否为 3.10 或更高版本，执行该目录下的 scripts/setup_web.py --install，完成后重新检查并报告 ready 和实际使用的 Python 路径。不要只把命令交给我，不安装语音模型。
```

安装脚本会创建或复用独立虚拟环境，并安装 `requests`、`beautifulsoup4`、`markdownify`。三个库均导入成功才输出 `ready: true`，不会修改系统 Python。只查看环境时运行同一脚本且不带 `--install`，此时不创建环境或安装依赖。

默认环境位于 `~/.workbuddy/venvs/link-extract`，技能安装目录以实际客户端为准。`doctor.py`、`wxfetch.py` 从系统 Python 启动时，会使用已经准备好的默认环境；明确使用其他虚拟环境时尊重该选择，不自动安装。Windows 使用安装脚本输出的 `Scripts/python.exe`。

## 第一次使用：先准备笔记库

下载仓库源码，复制 [`examples/obsidian-starter`](examples/obsidian-starter) 到自己的文档目录。用 Obsidian 打开这个文件夹，在 WorkBuddy 选择同一个文件夹作为工作目录。已有笔记库可保留自己的结构，但需准备规则、索引和模板，参照示例补齐。

可以先把 [`examples/practice.txt`](examples/practice.txt) 复制到笔记库的 `00-inbox` 做离线练习，再处理实际链接。

```text
请使用 link-extract-transcribe，先读取这个笔记库的 README.md、知识库规则.md、分类规则.json、材料索引.md 和 90-templates。
整理这份材料：【链接或本地相对路径】。我想了解：【问题】。
先核对来源是否处理过；按已有分类选择目录，说明实际读到的内容和缺失。先给草稿和拟保存位置，不覆盖旧文件。
```

确认草稿后：

```text
请按刚才确认的草稿和分类新增保存，原文或文字稿放 10-sources，分类笔记放对应目录，追加材料索引。检查文件和引用后报告结果，不覆盖旧文件。
```

默认先预览。长期自动新增需用户明确授权，并将规则中的 `save_mode` 设为 `auto_new_only`、`auto_new_only_authorized` 设为 `true`，同时记录到知识库规则。分类始终依据同一组规则；授权改变的是保存方式。自动新增的笔记仍标为“待核对”。同一来源返回已有笔记，重新提取需另存版本。

## 在命令行运行脚本

以下从仓库根目录运行。安装网页依赖需要联网，只需按需执行一次：

```sh
python3 scripts/setup_web.py --install
python3 scripts/setup_web.py
python3 scripts/doctor.py
python3 scripts/wxfetch.py 'https://mp.weixin.qq.com/s/文章ID' outputs/article-001
python3 scripts/transcript.py examples/sample.srt outputs/subtitles-001
```

替换文章占位链接，输出目录必须尚不存在。`wxfetch.py` 输出 `article.md`、`article.json` 和可选图片；字幕脚本输出文字稿及带时间段 JSON。CLI 接受显式输出路径；在技能流程中，由助手检查路径位于用户选择的 Vault 内。

本地语音转写可在自己选择的环境中另装 `faster-whisper`，然后用该环境的 Python 执行：

```sh
python scripts/transcript.py input.mp4 outputs/audio-001 --model-dir /path/to/local-model
```

不提供 `--language` 时识别原语言。翻译另存，不能把译文称为逐字原文。更多说明：[公众号](references/wechat.md)、[字幕与媒体](references/media.md)、[分类与保存](references/note-workflow.md)。

## 测试和打包

开发测试请先下载或克隆完整仓库源码；技能安装包不含 tests 和 examples。开发测试需安装网页依赖和 PyYAML；测试使用临时目录与模拟响应，不请求真实文章或下载模型。

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements-dev.txt
.venv/bin/python -m unittest discover -s tests -v
python3 scripts/build_package.py
```

Windows 将 `.venv/bin/python` 替换为 `.venv\Scripts\python.exe`。安装包写到 `dist/link-extract-transcribe-workbuddy.zip`，只包含技能说明、引用文档、运行脚本和网页依赖清单。

离线测试覆盖元数据、正文缺失、域名与跳转限制、图片失败、禁止覆盖、字幕时间段、安装检查和运行环境切换。它们不代表所有真实链接均可读，也不替代 WorkBuddy 内的实际分类和保存验证。
