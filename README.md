# 方向性智联 - 视频素材分析工具

这是一个视频素材分析工具，主要用于分析抖音平台上的PWU留香珠产品视频素材。该工具通过调用Gemini API来分析视频内容，并结合素材数据（如点击率、转化率、ROI等）生成全面的素材分析报告。

## 功能特点

1. **单个视频分析**：分析指定视频文件的内容，生成详细的分析报告
2. **批量视频分析**：批量处理指定目录下的所有视频文件
3. **数据整合**：从merged_material_data.json文件中获取素材的核心表现数据（如GMV、ROI、CTR、CVR等）
4. **用户行为分析**：分析视频中用户的点击和流失行为，识别关键时间点
5. **内容要素评估**：评估视频的画面表现、音频与BGM、视频节奏等内容要素
6. **综合诊断与归因**：分析视频表现的原因，包括调控效果分析
7. **优化建议**：提供针对视频的修改建议和后续素材创作建议
8. **Excel数据处理**：将Excel格式的素材数据转换为JSON格式
9. **图表截图与分析**：自动截取图表并进行峰值分析

## 目录结构

```
FangXieZhiLian/
├── agents/
│   ├── agent10.py        # 主要分析代码文件
│   └── run_agent10.py    # 运行脚本
├── json/
│   ├── Product.json      # 产品信息文件
│   ├── 素材数据分析/
│   │   ├── merged_material_data.json  # 合并后的素材数据
│   │   ├── 素材数据.json              # 从Excel提取的素材数据
│   │   ├── BYDHG_peaks_analysis.json  # 峰值分析结果
│   │   └── 素材数据分析格式.txt       # 数据格式说明
│   └── 不一定很贵/       # 分析报告输出目录
├── Tool/
│   ├── extract_excel_to_json.py       # Excel数据转换为JSON工具
│   ├── extract_excel_to_json.bat      # Excel数据转换批处理脚本
│   ├── extract_material_id.py         # 提取素材ID工具
│   ├── extract_material_id.bat        # 提取素材ID批处理脚本
│   ├── gemini_image_peak_analysis.py  # 图片峰值分析工具
│   ├── gemini_image_peak_analysis.bat # 图片峰值分析批处理脚本
│   ├── capture_click_chart.py         # 图表截图工具
│   ├── download_videos.py             # 视频下载工具
|   ├── filter_high_cost_materials.py  # 裂变脚本
|   ├── feishu_write.py                # 飞书写入功能
|   ├── json.analysis.py               # 素材报告切割功能
│   └── production_deployment_tool.py  # 素材潜力预测系统
├── screenshots/          # 截图保存目录
│   └── errors/           # 错误截图保存目录
├── storage/
│   └── video/
│       └── 留香珠/       # 视频文件目录
│           └── 0605-留香珠-促销-【砍一刀】01-zyjd.mp4  # 示例视频文件
├── data/
│   ├── 素材数据.xlsx     # 原始素材数据Excel文件
│   └── 素材ID.json       # 提取的素材ID
|
├── feishu_config.json    # API配置文件
├── merge_data.bat        # 数据处理自动化工具
├── run_all.bat           # 素材筛选和上传、裂变上传
└── .gitignore            # Git忽略文件配置
```

## 使用方法

### 数据处理自动化工具

最简单的方法是运行根目录下的merge_data.bat批处理脚本，它会自动执行完整的数据处理流程：

```
cd FangXieZhiLian
merge_data.bat
```

该脚本会自动执行以下步骤：
1. 提取素材ID
2. 使用Playwright截取图表
3. 执行Excel数据转换
4. 执行图片峰值分析
5. 合并素材数据和峰值分析结果


### 素材潜力预测系统+自动上传

### 结果查看：https://x1zbu25b72k.feishu.cn/base/CJvAbVltnaITVKsfdqFcQYQ7nwf?table=tbls20qCGDuPDHZK&view=vewzzXMCVT#CategorySuggested
```
cd FangXieZhiLian
run_all.bat
```

### 单个视频分析

```python
from agents.agent10 import analyze_material_by_video_path
from google import genai

# 初始化Gemini客户端
client = genai.Client(api_key="YOUR_API_KEY")

# 分析单个视频
video_path = r"C:\Users\EDY\Desktop\wwj\FangXieZhiLian\storage\video\留香珠\0605-留香珠-促销-【砍一刀】01-zyjd.mp4"
result = analyze_material_by_video_path(video_path, client)
```

### 批量视频分析

```python
from agents.agent10 import batch_analyze_videos
from google import genai

# 初始化Gemini客户端
client = genai.Client(api_key="YOUR_API_KEY")

# 批量分析视频
video_dir = r"C:\Users\EDY\Desktop\wwj\FangXieZhiLian\storage\video\留香珠"
results = batch_analyze_videos(video_dir, client)
```

## 分析报告

分析报告以JSON格式保存，包含以下主要部分：

1. **关键用户行为节点分析**：高点击时刻分析、高流失时刻分析、开篇用户行为解读
2. **内容要素有效性评估**：画面表现、音频与BGM、视频节奏、Agent1逻辑要素应用效果、核心卡片关键词有效性、关键转化场景/元素分析
3. **综合诊断与归因**：整体表现归因、调控效果专项分析、内容层面主要优点和缺点
4. **优化建议**：针对此条视频的修改建议、后续素材创作建议、A/B测试建议

## 数据格式

### 素材数据格式

素材数据使用以下JSON格式：

```json
{
    "素材ID": "",
    "素材名称": "",
    "素材时长": "",
    "整体消耗": "",
    "整体支付ROI": "",
    "整体成交金额": "",
    "整体转化率": "",
    "整体点击率": "",
    "3秒播放率": "",
    "平均观看时长": "",
    "视频完播率": "",
    "追投调控消耗": "",
    "追投调控成交金额": "",
    "追投调控支付ROI": "",
    "追投调控点击率": "",
    "追投调控转化率": "",
    "基础消耗": "",
    "images": {
        "整体流失数_20250515_175020.png": {
            "main_peak": {
                "x": "00:00",
                "y": 1050
            },
            "secondary_peak": {
                "x": "00:06",
                "y": 225
            },
            "error": null
        },
        "整体点击次数_20250515_175020.png": {
            "main_peak": {
                "x": "00:00",
                "y": 340
            },
            "secondary_peak": {
                "x": "00:04",
                "y": 10
            },
            "error": null
        }
    }
}
```

## 依赖项

- Python 3.8+
- google-generativeai
- pandas
- playwright (用于图表截图)
- 其他标准库：datetime, json, os, random, time, traceback, re

## 安装

1. 克隆仓库
```
git clone https://github.com/yourusername/FangXieZhiLian.git
cd FangXieZhiLian
```

2. 安装依赖
```
pip install -r requirements.txt
```

3. 配置API密钥
在agents/agent10.py文件中设置您的Gemini API密钥：
```python
API_KEY = "YOUR_API_KEY"
```

## Git忽略配置

项目的.gitignore文件配置了以下忽略规则：

```
data
json
storage
video_download.log
screenshots/
__pycache__/
```

这确保了大型数据文件、视频和截图不会被包含在Git仓库中。

## 注意事项

1. 使用前需要设置有效的Gemini API密钥
2. 视频文件需要放在指定的目录中
3. 分析过程可能会消耗较多的API调用次数
4. 分析结果保存在json目录下的对应子目录中
5. 确保Playwright已正确安装并配置，用于图表截图功能
6. 运行merge_data.bat前，确保data目录中有有效的素材数据Excel文件 

## 快速启动

### 启动素材潜力预测系统
```
start_prediction_system.bat
```

### 启动素材分析系统
```
run_agent10.bat
```

### 启动高成本素材筛选工具
```
run_cost_filter.bat
``` 