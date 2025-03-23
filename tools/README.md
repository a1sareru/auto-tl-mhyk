# 自用tools

该目录下是开发者自用的工具，用于调试或者自用的其他功能。

这份说明是为了避免开发者自己忘了怎么用而写的，请不要太在意这个目录下的所有内容。

## `merge_srt.py`

该脚本用于将多个视频对应的字幕文件（SRT）合并为一个整体字幕文件，并自动调整时间轴以保证连续播放时字幕正确对应。

### 用法

```sh
python merge_srt.py [-yrb <路径前缀>]
```

**参数说明**
- `-yrb` 或 `--yml-relative-base`：可选参数，指定 `merge.yaml` 中路径的相对基准目录。若未指定，则以脚本所在目录为基准。

`merge_srt.yml` 文件的示例：

```yaml
- video_paths:
  - 01.mp4
  - 02.mp4
  - 03.mp4
- srt_paths:
  - 01.srt
  - 02.srt
  - 03.srt
```

### 功能说明
1. 读取脚本同级目录下的 `merge_srt.yml` 文件，获取视频文件路径和对应的字幕文件路径。
2. 遍历所有字幕文件，根据每个视频的时长自动偏移字幕时间轴，使其适配拼接后的视频。
3. 合并所有字幕为一个新的 `merged.srt` 文件，保证编号连续、时间轴准确。
4. 输出合并结果路径，并打印每个视频的编码信息（包括视频与音频编码、分辨率、帧率、采样率等）。

### 注意事项
- 依赖：
  ```sh
  pip install moviepy ffmpeg-python pyyaml
  ```
- `merge.yaml` 文件必须为如下格式，包含 `video_paths` 与 `srt_paths` 两个字段，且数量一致：
  ```yaml
  - video_paths:
      - path/to/video1.mp4
      - path/to/video2.mp4
  - srt_paths:
      - path/to/sub1.srt
      - path/to/sub2.srt
  ```
- 合并后的字幕输出为 `merged.srt`，位于当前工作目录或 `-yrb` 指定的目录下。

## `generate_long_pics.py`

该脚本用于将多个图片合并成长图，并可选地生成 PDF 文件。适用于将 `slides` 目录下的图片内容拼接成长条形图像，方便阅读或归档。

### 用法

```sh
python generate_long_pics.py --slides <图片文件夹路径> [--size 4] [--pdf]
```

**参数说明**
- `--slides` : 输入的图片文件夹路径（必填）。
- `--size`   : 每组合并的图片数量，默认为 4，可根据需要调整。
- `--pdf`    : 是否生成 PDF 文件，添加该参数时会输出 PDF。

### 处理逻辑
1. 读取 `--slides` 目录下的所有图片，并按编号排序。
2. 以 `--size` 为单位，将图片拼接成长图，并保存至 `slides-long` 目录。
3. 若指定 `--pdf` 选项，则将生成的长图合并为 PDF 文件。

### 注意事项
- 依赖 `PIL` (Pillow) 进行图像处理和 `fpdf` 进行 PDF 生成，请确保已安装：
  ```sh
  pip install pillow fpdf
  ```
- 输出的长图文件存放在 `slides-long/` 目录，PDF 文件名为 `slides-long.pdf`。
- 默认每 4 张图片拼接为一张长图，可通过 `--size` 参数修改。
- 若 `--pdf` 选项启用，则会将长图合并为单一 PDF 文件。

## `replace.py`
该脚本用于根据同级目录下的 `replace.yml` 文件对文本文件中的特定词语进行批量替换。

适用于标准化术语、清洗翻译文本、批量文本修改等需求。

### 用法

```sh
python replace.py --input <待处理文本文件路径>
```

**参数说明**
- `--input` : 需要进行替换处理的文本文件路径（必填）。

### 功能说明
1. 自动加载与脚本同目录下的 `replace.yml` 配置文件。
2. 读取指定的输入文本文件内容。
3. 根据配置中定义的替换对（键值对形式）对文本进行逐项替换。
4. 将替换后的内容保存为一个新文件，命名为 `<原文件名>-new.<扩展名>`。

### `replace.yml` 示例格式

```yaml
旧词1: 新词1
旧词2: 新词2
```

### 注意事项
- 替换配置文件必须命名为 `replace.yml`，并放置于脚本同目录下。
- 所有替换操作为全字面量匹配，区分大小写。
- 输出文件与原始文件在同一目录，文件名自动添加 `-new` 后缀。


## `test_paddle.py`

这是为了测试 PaddleOCR 实际能力所写的脚本。

该脚本使用 PaddleOCR 进行日语文本识别。适用于对单张图片中的日语文本进行 OCR.

### 用法

```sh
python test_paddle.py <图片路径>
```

**参数说明**
- `<图片路径>` : 要进行 OCR 识别的图片文件路径（必填）。

### 处理逻辑
1. 读取输入图片。
2. 使用 PaddleOCR 进行文本检测和识别，语言设定为日语（japan）。
3. 输出识别结果，包括文本内容和置信度。

### 注意事项
- 依赖 `paddleocr` 进行 OCR 识别，请确保其已安装：
  ```sh
  pip install paddleocr
  ```
- 识别效果可能受图片质量影响，建议使用清晰的高分辨率图片。
- 目前仅支持日语文本识别，其他语言请自行调整 `lang` 参数。
