# auto-tl-mhyk

>有问题可以直接提 issue，
>或者联系邮箱 [kmbk.kr.dev[AT]outlook.jp](mailto:kmbk.kr.dev@outlook.jp).

>写 README 的主要目的是防止开发者自己想不起来用法。
>看得懂或者看不懂都是正常的。

## 测试效果 (Evaluation)

> 测试环境：个人笔记本电脑。

使用 `02_frame.py` 进行时轴生成：
* 登录故事/1话/2min 30s，用时 25s
* 主线剧情/1章/共约90min，用时约 8min

## ⚠️ 目前已知的问题

### 1. 分辨率/视频尺寸适配

开发者的手机在经过黑边切除的处理后输出的比例为 `9:16`，
后面的脚本基本上据此进行设计。
因此，可能会由于算数四舍五入出现效果不佳的情况，请酌情自行调整。

(2025/03/23) 发现部分老师用的尺寸并非 `9:16` ，
增加了 `9:19.5` 的适配（但由于缺少测试用例，该模式未经充分测试）

>如果需要其他尺寸，可自行修改 `02_frame.py`，增加相关选项和配置；
>也可向开发者提交可参考的录屏示例文件。

### 2. 【未再次复现】一次性识别较长的剧情时，准确率下降

【更新】用目前 (2025/03/26) 的 `02_frame.py` 脚本，
尝试处理时长约 1h 30min 的单章主线剧情，
结果表现尚可，故不确定该问题是否仍存在。

> 以下是先前的记录。

原因可能是触及了opencv或者ffmpeg库的某种限制，但并不是很确定。
触发此问题是因为想把三个视频合并了一起轴（大约20分钟），结果轴的准确率大大降低。

## 1 目录结构（部分）

```
├── 02_frame.py        # 从视频中提取帧，计算相似度，生成字幕
├── 03_ocr.py          # 对字幕图片进行 OCR 识别，并可选地翻译成中文
├── README.md          # 项目说明文档
├── kuroyuri.png       # 参考图像，用于相似度计算
├── requirements.txt   # 依赖包列表
└── tools/             # 开发者自用工具（介绍略）
```

再简要介绍一下几个脚本。
* `02_frame.py`: 接受无黑边的 `9:16` 或 `9:19.5` 视频文件作为输入，输出带时轴的字幕文件(srt)。
* `03_ocr.py`: （效果很烂）接收上一个脚本的可选功能生成的 `slides` 目录作为输入，输出 OCR 的结果。

### 如何开始使用

下载本仓库源代码。
- 方法1: 右上角绿色 `Code` 按钮 → ' Download ZIP'），并解压代码
- 方法2:  `git clone` 本仓库

> 假设解压后得到的目录为**工作目录**。

确认本地安装了 `Python` 和 `ffmpeg`，并保证它们的实际安装路径均已加入环境变量（Environment Variable）中。

确认能够开启当前电脑的命令行/终端工具：Windows 的 `CMD` 或 `PowerShell`，MacOS/Linux 的 `Terminal`.
- 命令行工具可以通过 **键入命令**、**回车(Enter)键提交** 来完成你指定的任务
- 用命令行可以通过形如 `python p.py` 的命令来执行 Python 脚本

确认以上两行的工作都已完成且可用：对于您选择使用的命令行工具，新开一个窗口
- 使用 `python --version` 命令，能够得到版本号回显；
- 使用 `ffmpeg -version` 命令，能够得到版本号及部分配置信息。

在命令行中切换到**工作目录**。
- 例如你的工作目录是 `D:\auto-tl-mhyk-main\`，则使用下列命令：
  ```sh
  cd "D:\auto-tl-mhyk-main\"
  ```
  其中，`cd` 是 change directory 的意思。

使用以下命令安装相关依赖：

```sh
pip install -r requirements.txt
```

安装成功后，便可按照下列介绍中的示例进行使用。

## 2 分文件介绍

本项目包含多个脚本，分别用于帧提取与相似度计算、OCR 识别与翻译等任务。

**最有用的只有 `02_frame.py` 这一个脚本。**

### 2.1 使用 `02_frame.py` 前：手动裁切视频黑边

安装 `ffmpeg` 工具，确保命令行可以调用。

使用以下命令检测视频中黑边的位置和大小：

```sh
ffmpeg -i input.mp4 -vf cropdetect -f null -
```

输出信息中会显示类似 `crop=width:height:x:y` 的值，请选择合适的取值。
其中，`x` 和 `y` 为有效区域的起始坐标，`width` 和 `height` 是有效区域的宽和长。

💡 tips（建议进行的优化）：比如说你需要裁剪视频上下的黑边，假设你认为合适的参数是 `crop=w:h:x:y`，
如果 `x` 此时是一个很小的值，则推荐使用 `crop=w+2*x:h:0:y` 作为你的新参数。

接下来，根据检测到的 crop 值裁切视频，去除黑边：

```sh
ffmpeg -i input.mp4 -vf "crop=width:height:x:y" output.mp4
```

替换 `width:height:x:y` 为第一步检测到的值。

### 2.2 `02_frame.py`
该脚本用于从视频中提取帧，应用锐化和二值化处理，并计算与参考图像的相似度，最终生成字幕文件。

可选地，还可提取关键帧，便于阅读。
这个 `--slides` 功能的设计初衷是为了方便我和我的朋友阅读剧情 ~~看竖屏幻灯片录屏实在太坐牢了~~。

⭐️ **原理**

对话框右下角的黑百合图案在字幕加载完成时会闪动，通过监测该区域图形变化实现切帧打轴功能。
因此，当视频尺寸不符合预期时 (`9:16` 或 `9:19.5`)，识别的结果应该会非常不理想
->所以直接选择拒绝识别。

**用法**
```sh
python 02_frame.py --input <输入视频路径> [--output <输出目录>] [--debug] [--slides]
```

**参数说明**
* `--input`  : 输入视频文件路径（必填）。
* `--debug`  : 启用调试模式，保存临时帧图像及相似度数据（可选）。
    * 启用时，处理后的帧图像和相似度数据将保存至视频所在目录下的 `tmp_debug_frame/` 文件夹。
* `--slides` : 保存每条字幕结束时间对应的对话框图片（可选）。
* `--enable-merge` : 启用相似对话框图片合并功能（不推荐开启）。
    * ⚠️ 该功能有可能导致错误的合并，一般情况下不建议使用（除非对你来说分轴比合轴容易）。
    * 若启用此功能，相似度高于 `0.996` 的连续对话框将被视为同一内容合并，节省输出数量。
    * 合并过程中：
        * 原始对话框图片将重命名为 `####-a.png`
        * 对应字幕被合并的对话框图片保存为 `####-merged-x.png`（`x` 表示第几张被合并）
    * 若不添加该选项，则不考虑检查/合并相邻相似字幕。

**处理逻辑**
1. 读取输入视频信息（帧率、宽度、高度）。
2. 自动识别视频的宽高比（支持 `9:16` 与 `9:19.5` ），并加载对应预设参数。
3. 载入参考图像 `kuroyuri.png`（路径可在脚本最上方手动修改），并转换为灰度图。
4. 逐帧读取视频：
    - 裁剪目标区域
    - 应用锐化处理
    - 进行二值化
    - 计算与参考图像的相似度
5. 根据相似度数据识别高相似度区间，生成字幕文件 (`.srt`)。
6. 若启用 `--slides`，提取高相似度间隔的代表帧作为幻灯片。

**注意事项**
* 依赖 `opencv-python` 进行图像处理，请确保其已安装。
* 默认使用 `kuroyuri.png` 作为参考图像，路径和相似度阈值均可在脚本顶部常量中手动修改。
* 若启用 `--debug`，输出目录中会保存处理后的帧图像和 `_a.csv` 相似度数据表（位于输入视频目录下的 `tmp_debug_frame` 文件夹中）。
* 生成的字幕文件将与输入视频同目录，文件名与视频同名，扩展名为 `.srt`。
* `--slides` 选项会在输入视频目录创建 `{video}-slides` 文件夹，保存幻灯片帧。

**使用示例**
```sh
python 02_frame.py --input input.mp4 --debug --slides
```

#### 💡 进阶：自定义参考图像与相似度阈值（kuroyuri.png & THRESHOLD_RATIO）

`THRESHOLD_RATIO` 是一个介于 `0` 到 `1` 之间的浮点数，用于判断当前帧是否足够接近参考图像，从而触发“检测到时间轴结束点”的判断。
但它并不是一个绝对的相似度阈值，而是相对于视频中出现的「帧相似度最大值」进行缩放的比值。

>例如，若某段视频中「帧相似度最大值」为 `0.987`，且设定 `THRESHOLD_RATIO = 0.97`，则实际使用的判断阈值为 `0.987 × 0.97 ≈ 0.957`。

阈值越高，只有与参考图像几乎完全一致的帧才会触发识别；阈值越低，则更容易触发，但可能会误识别噪点。

如果你发现默认的 `kuroyuri.png` 无法正确识别闪图，或者使用的录屏尺寸较为特殊，可以使用 `--debug` 模式来生成你自己的参考图像。

**步骤如下：**
1. 使用 `--debug` 模式运行 `02_frame.py`，例如：
   ```sh
   python 02_frame.py --input input.mp4 --debug
   ```
2. 进入输出目录，找到某一帧中图像清晰显示黑百合图案的图片（一般为类似 `frame_xxx.png` 的文件）。
3. 使用任意图片编辑工具（如截图工具）将黑百合区域裁剪出来，保存为 `kuroyuri.png`（或任意你喜欢的名称），替换脚本中 `KUROYURI_PATH` 的值。

**提示：**
- 如果你从当前视频中提取了参考图像（记得将 `KUROYURI_PATH` 修改为对应路径！），为了提高检测准确度，可能需要适当调整该脚本预设参数 `THRESHOLD_RATIO` 的值，例如：
  ```python
  THRESHOLD_RATIO = 0.95
  ```
- 你可以在 `02_frame.py` 脚本顶部修改 `KUROYURI_PATH` 与 `THRESHOLD_RATIO` 。
- `THRESHOLD_RATIO` 具体是调高还是调低其实我也不是很确定，建议多试试（既然你能看懂并进行这段操作，那么自行调参想必不在话下🥺）；
  - 调高的理由是 similarity 的平均数大概率会上升，调低的理由是可能会错误筛除掉一些本应识别的闪烁；
  - 个人倾向于调高，因为此时的对比对象从本仓库提供的「某一话截取的图像」变成了「当前视频的某一张图像」，理论上来说 peak 类 similarity 值的分布密度会变大；
  - 但是如果发现总是出现被错误筛除的帧的话，请考虑调低。

### 2.3 `03_ocr.py`

⚠️ 使用前，请参照 [官网文档](https://paddlepaddle.github.io/PaddleOCR/latest/quick_start.html)
在本地安装 `paddlepaddle`。
CPU 版本和 GPU 版本：请按需选择 ~~我没装过 GPU 版本，不知道~~。

该脚本用于从上一节得到的 `{video}-slides` 目录下的图像中提取字幕文本。
它使用 paddleOCR 识别字幕内容。

输出的 CSV 文件可以直接用表格处理软件打开，如果发生任何编码问题请自行查阅相关资料解决。

做这个脚本是主要为了方便对轴，不过做完了发现不怎么用得上。

**Evaluation**

在个人笔记本上使用该脚本对 6min 50s 的一话活动剧情用上一节的脚本生成的 `{video}-slides` 目录进行 OCR 操作，用时约 1min 47s.

**警告：虽然提供了 `--chn` 选项但是不建议使用，效果实在是太烂了。由于优化工作繁琐细碎且优化空间有限，所以开发者后续并不打算使用或优化这个功能。**

**用法**
```sh
python 03_ocr.py --slides <slides目录路径> [--chn]
```

**参数说明**
* `--slides` : 幻灯片帧所在的目录路径（必填）。
* `--chn`         : 启用日语到中文的自动翻译（可选）。

**处理逻辑**
1. 读取 `slides` 目录下的 PNG 图片。
2. 依次进行 OCR 识别，提取文本内容：
    - 自动检测角色名称，并替换为英文名称。
    - 进行额外的单行 OCR，提高准确度。
    - 计算字符串相似度，优化文本结果。
3. 生成 CSV 文件，记录提取的日语字幕。
4. 若启用 `--chn`，对识别的文本进行日语到中文翻译，并追加至 CSV 文件。

**注意事项**
* 依赖 `paddleocr` 进行 OCR 识别，请确保其已安装。
* 默认会在 `slides` 的同级目录生成 `{video}-ocr-results.csv` 作为输出文件。
* `--chn` 选项使用 `translate` 库进行翻译，翻译质量有限。

**使用示例**
```sh
python 03_ocr.py --slides slides/ --chn
```

## Roadmap

有空的话调研一下 `02_frame.py` 是否需要做分片处理的优化。

## 闲聊

前面忘了后面忘了，来都来了不如看看我家的*打轴*工作区：

![show_my_workspace](_assets/show_my_workspace.png)