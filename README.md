# 方榭智联 - 短视频素材分析与优化工具集

## 项目概述
方榭智联是一套短视频素材分析与优化工具集，旨在帮助运营人员高效分析短视频素材效果、识别人群错配问题，并提供数据驱动的优化建议。该工具集集成了AI分析能力，可自动化处理数据提取、分析报告生成和优化指令推荐等任务。

## 功能特点

### 核心工具
- **媒体素材分析** (`IterativeMediaAnalyzer.py`): 从Excel文件读取素材数据，结合行业基数标准，使用Gemini AI生成优化指令
- **人群错配分析** (`audience_mismatch_analysis.py`): 对比曝光人群与转化人群数据，识别潜在的人群错配问题并生成可视化报告
- **JSON数据分析** (`json_analyzer.py`): 将JSON格式的分析数据转换为Excel或CSV格式的结构化报告
- **行为节点提取** (`extract_behavior_analysis.py`): 从JSON文件中提取关键用户行为节点分析数据
- **素材ID处理** (`extract_material_id.py`): 提取和管理素材ID信息
- **视频分析代理** (`agents/agent10.py`): 批量分析视频素材，结合素材ID匹配和视频内容分析

### 辅助功能
- 多格式数据转换（Excel/JSON/CSV）
- 自动化报告生成
- 批量处理与分析能力
- 飞书集成（`feishu_write.py`）
- 成本过滤与素材筛选

## 安装指南

### 环境要求
- Python 3.8+
- Windows操作系统（批处理脚本兼容）
- 网络连接（用于AI API调用）

### 依赖安装
1. 克隆或下载项目到本地
2. 安装依赖包：
```bash
pip install pandas numpy matplotlib requests pillow google-generativeai openpyxl
```

### 配置设置
1. 复制配置模板并修改：
```bash
copy feishu_config_template.json feishu_config.json
```
2. 在相关脚本中配置API密钥：
   - Gemini API密钥（在`IterativeMediaAnalyzer.py`、`audience_mismatch_analysis.py`等文件中）

## 使用方法

### 快速开始
运行主批处理脚本执行完整分析流程：
```bash
run_all.bat
```

### 单独工具使用

#### 1. 媒体素材分析
```bash
cd Tool
python IterativeMediaAnalyzer.py
```
该工具会自动读取`form`目录下最新的Excel文件，进行分析并生成AI优化指令。

#### 2. 人群错配分析
```python
from Tool.audience_mismatch_analysis import AudienceMismatchAnalysis

analyzer = AudienceMismatchAnalysis(
    impression_img_path='曝光人群.png',
    conversion_img_path='转化人群.png'
)
result = analyzer.analyze()
```

#### 3. JSON数据分析
```bash
cd Tool
python json_analyzer.py
```
分析结果将保存到`analysis_report`目录。

#### 4. 视频批量分析
```bash
cd agents
python run_agent10.py
```

## 项目结构
```
FangXieZhiLian/
├── .gitignore                   # Git忽略文件
├── .vscode/
│   └── settings.json            # VS Code配置文件
├── README.md                    # 项目说明文档
├── Tool/                        # 核心工具脚本
│   ├── IterativeMediaAnalyzer.py            # 迭代媒体分析器：从Excel文件读取素材数据，结合行业基数标准，使用Gemini AI生成优化指令
│   ├── audience_mismatch_analysis.py        # 人群错配分析工具：对比曝光人群与转化人群数据，识别潜在的人群错配问题并生成可视化报告
│   ├── capture_click_chart.py               # 点击图表捕获工具：使用Playwright自动化从网页提取视频素材的点击图表
│   ├── cardinal_number/                     # 行业基数标准数据目录：存储各行业的基准数据
│   ├── download_videos.py                   # 视频下载工具：从网页中提取视频标题和URL并下载视频
│   ├── extract_behavior_analysis.py         # 行为分析提取工具：从JSON文件中提取关键用户行为节点分析数据
│   ├── extract_excel_to_json.bat            # Excel转JSON批处理脚本：批量执行Excel到JSON的转换
│   ├── extract_excel_to_json.py             # Excel转JSON工具：将Excel格式的素材数据转换为JSON格式
│   ├── extract_material_id.bat              # 素材ID提取批处理脚本：批量执行素材ID提取
│   ├── extract_material_id.py               # 素材ID提取工具：从Excel文件中提取素材ID并保存为JSON格式
│   ├── feishu_write.py                      # 飞书写入工具：提供与飞书多维表格交互的功能，实现数据的写入和更新
│   ├── filter_high_cost_materials.py        # 高消耗素材筛选工具：筛选出'整体消耗'大于阈值的素材并上传到飞书
│   ├── gemini_image_peak_analysis.bat       # Gemini图像峰值分析批处理文件：批量执行图像峰值分析
│   ├── gemini_image_peak_analysis.py        # Gemini图像峰值分析工具：使用Gemini API分析图片中的曲线峰值
│   ├── json_analyzer.py                     # JSON分析器：将JSON格式的分析数据转换为Excel或CSV格式的结构化报告
│   └── production_deployment_tool.py        # 生产环境部署工具：抖音素材潜力预测系统的生产环境部署工具
├── agents/                    # 自动化代理脚本
│   ├── agent10.py                           # 代理10：基于Gemini 2.0 Flash的素材分析框架，实现素材ID与名称的映射查找和批量视频分析
│   └── run_agent10.py                       # 运行代理10的脚本
├── feishu_config.json           # 飞书配置文件：存储飞书API的配置信息
├── feishu_config_template.json  # 飞书配置模板文件：飞书配置的模板，用于创建新的配置
├── merge_data.bat              # 数据合并批处理文件：合并多个数据源的数据
├── merge_data_extract.bat      # 迭代批处理文件：迭代分析
├── run_agent10.bat             # 运行代理10的批处理文件：启动agent10进行素材分析
└── run_all.bat                 # 运行所有分析流程的主批处理文件：一键执行所有分析流程
```

## 注意事项
1. **文件路径配置**：部分脚本中使用了绝对路径，需要根据实际部署环境修改
2. **API密钥安全**：请勿将API密钥提交到版本控制系统
3. **数据备份**：重要分析数据建议定期备份
4. **性能考虑**：批量视频分析可能需要较长时间，建议分批处理
5. **依赖更新**：定期更新依赖包以获得最新功能和安全修复

## 许可证
[MIT License](LICENSE)