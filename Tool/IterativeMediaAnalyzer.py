import requests
import json
import time
import os
import pandas as pd

def get_latest_excel_file(folder_path="form"):
    """查找指定文件夹下最新的Excel文件（.xls/.xlsx）"""
    if not os.path.exists(folder_path):
        print(f"❌ 文件夹不存在: {folder_path}")
        return None
    excel_files = [f for f in os.listdir(folder_path) if (f.endswith('.xls') or f.endswith('.xlsx')) and not f.startswith('~$')]
    if not excel_files:
        print(f"⚠️ 未找到Excel文件于: {folder_path}")
        return None
    # 按修改时间排序，取最新
    excel_files.sort(key=lambda f: os.path.getmtime(os.path.join(folder_path, f)), reverse=True)
    latest_file = os.path.join(folder_path, excel_files[0])
    print(f"🆕 自动选取最新Excel文件: {latest_file}")
    return latest_file

def load_cardinal_numbers(file_path="Tool/cardinal_number"):
    """加载基数文件"""
    try:
        # 默认值
        cardinal_numbers = {
            "cpm": 157.64,
            "play3s": "30.35%",
            "cvr": "6.25%",
            "click_rate": "4.06%"
        }
        
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                for line in lines:
                    if ":" in line:
                        key, value = line.split(":", 1)
                        key = key.strip().lower()
                        value = value.strip()
                        
                        if "cpm" in key:
                            cardinal_numbers["cpm"] = float(value)
                        elif "3秒播放率" in key:
                            cardinal_numbers["play3s"] = value
                        elif "整体转化率" in key:
                            cardinal_numbers["cvr"] = value
                        elif "整体点击率" in key:
                            cardinal_numbers["click_rate"] = value
            
            print(f"✅ 成功加载基数文件，基数值为: {cardinal_numbers}")
        else:
            print(f"⚠️ 基数文件不存在，使用默认值: {cardinal_numbers}")
        
        return cardinal_numbers
    except Exception as e:
        print(f"❌ 加载基数文件失败: {e}")
        # 返回默认值
        return {
            "cpm": 157.64,
            "play3s": "30.35%",
            "cvr": "6.25%",
            "click_rate": "4.06%"
        }

# 加载基数值
CARDINAL_NUMBERS = load_cardinal_numbers()

# Gemini 2.0 Flash API密钥（如需更换请在此处修改）
API_KEY = "AIzaSyDxnQNBD0dtIKtZHpubgv_ZSw7AG_7tYCU"
API_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={API_KEY}"

# AI分析提示词模板
AI_PROMPT_TEMPLATE = '''你是一名短视频素材运营与优化专家。请根据以下素材的关键信息，结合行业基数标准，从如下几个诊断维度给出最优的下一步运营或内容优化指令：

1. 若"3秒完播率"低于{cardinal_play3s}：系统判定为"钩子"（开头）有问题。指令会是："更换钩子"，甚至会根据历史爆款数据，建议"换成一个什么样的钩子"。
2. 若"整体点击率"低于{cardinal_click_rate}：对比基数，判断是画面吸引力不足还是内容关联度不够。
3. 若"整体转化率"低于{cardinal_cvr}：系统判定为"转化环节"有问题。指令可能会指出："你的转化话术与前面的人群叙事不匹配"或"你没有使用历史上转化效果最好的那个镜头/话术"，并要求进行修正。
4. 若"CPM（获客成本）"高于{cardinal_cpm}：系统判定为"痛点"没有打准。指令会是：说明与目标人群不匹配，需要从文案和画面层面提高目标受众精准度。

素材信息如下：
- 素材名称：{name}
- 素材ID：{material_id}
- 素材消耗：{cost}元
- 3秒完播率：{play3s}
- CPM：{cpm}
- 转化率：{cvr}
- 整体点击率：{click_rate}
- 整体展现次数：{impression}

请用一句话输出最优指令。
输出要求：你必须列出所有指定诊断维度与基数对比情况，并给出最优的下一步运营或内容优化指令。

如果你被问到"你是什么模型/是谁"等身份相关问题，必须严格回答：您好，我是运行在gemini-2.5-pro-preview-05-06模型上的AI助手，很高兴在Cursor IDE中为您提供帮助，你可以直接告诉我你的具体需求，比如"帮我写一个Python爬虫"、"解释一下这段报错"、"生成一个Node.js项目模板"等等。'''

def call_gemini_ai(prompt):
    headers = {'Content-Type': 'application/json'}
    payload = {
        "contents": [{
            "parts": [
                {"text": prompt}
            ]
        }]
    }
    for attempt in range(3):
        try:
            resp = requests.post(API_URL, headers=headers, json=payload, timeout=60)
            resp.raise_for_status()
            result = resp.json()
            # 提取AI返回文本
            text = ''
            if 'candidates' in result and result['candidates']:
                cand = result['candidates'][0]
                if 'content' in cand and 'parts' in cand['content']:
                    for part in cand['content']['parts']:
                        if 'text' in part:
                            text += part['text']
            return text.strip()
        except Exception as e:
            print(f"[AI] 第{attempt+1}次调用失败: {e}")
            time.sleep(2 + attempt * 2)
    return "[AI] 分析失败，未能获取指令。"

def filter_high_cost_materials(file_path, cost_min=1000, cost_max=10000):
    """筛选整体消耗在指定区间的素材，并输出AI分析指令到控制台"""
    if not file_path or not os.path.exists(file_path):
        print(f"❌ 文件不存在: {file_path}")
        return
    print(f"📖 正在读取文件: {file_path}")
    try:
        # 创建保存AI分析结果的目录
        script_dir = os.path.dirname(os.path.abspath(__file__))
        root_dir = script_dir
        while not os.path.exists(os.path.join(root_dir, 'json')) and os.path.dirname(root_dir) != root_dir:
            root_dir = os.path.dirname(root_dir)
        
        # 如果没找到json目录，则在当前目录创建
        if not os.path.exists(os.path.join(root_dir, 'json')):
            root_dir = os.path.dirname(os.path.abspath(__file__))
            os.makedirs(os.path.join(root_dir, 'json', '素材数据分析'), exist_ok=True)
        
        output_dir = os.path.join(root_dir, 'json', '素材数据分析')
        os.makedirs(output_dir, exist_ok=True)
        
        # 尝试加载BYDHG_peaks_analysis.json文件
        peaks_data = {}
        peaks_file_path = os.path.join(output_dir, 'BYDHG_peaks_analysis.json')
        if os.path.exists(peaks_file_path):
            try:
                with open(peaks_file_path, 'r', encoding='utf-8') as peaks_file:
                    peaks_data = json.load(peaks_file)
                print(f"✅ 成功加载八大人群分析数据: {peaks_file_path}")
            except Exception as e:
                print(f"⚠️ 加载八大人群分析数据失败: {e}")
                peaks_data = {}
        else:
            print(f"⚠️ 八大人群分析数据文件不存在: {peaks_file_path}")
        
        # 生成输出文件名，使用当前时间戳
        timestamp = time.strftime("%Y%m%d_%H%M%S", time.localtime())
        output_file = os.path.join(output_dir, f'AI分析结果.txt')
        
        df = pd.read_excel(file_path)
        print(f"✅ 成功读取数据 - 共 {len(df)} 条记录")
        # 字段自动识别
        cost_column = next((c for c in ['整体消耗', '消耗', '总消耗', '花费', 'cost'] if c in df.columns), None)
        name_column = next((c for c in ['素材名称', '素材标题', '标题', '名称', 'title', 'name'] if c in df.columns), None)
        id_column = next((c for c in ['素材ID', '素材id', 'material_id', '视频ID'] if c in df.columns), None)
        play3s_column = next((c for c in ['3秒播放率', '3s播放率'] if c in df.columns), None)
        cpm_column = next((c for c in ['CPM', 'cpm', '获客成本'] if c in df.columns), None)  # 保留原始CPM列识别，用于备用
        cvr_column = next((c for c in ['整体转化率', '转化率', 'CVR', 'cvr'] if c in df.columns), None)
        click_rate_column = next((c for c in ['整体点击率', '点击率', 'CTR', 'ctr'] if c in df.columns), None)
        impression_column = next((c for c in ['整体展现次数', '展现次数', '展示次数', '曝光量', 'impressions'] if c in df.columns), None)
        if not cost_column or not name_column:
            print("❌ 缺少必要字段")
            return
        # 清理消耗列
        if df[cost_column].dtype == 'object':
            df[cost_column] = df[cost_column].astype(str).str.replace(',', '').str.replace(' ', '').str.replace('¥', '').str.replace('$', '').str.replace('￥', '')
        df[cost_column] = pd.to_numeric(df[cost_column], errors='coerce')
        # 筛选区间
        filtered_df = df[(df[cost_column] >= cost_min) & (df[cost_column] <= cost_max)].copy()
        if len(filtered_df) == 0:
            print(f"⚠️ 未找到整体消耗在{cost_min}-{cost_max}区间的素材")
            return
        # 排序
        filtered_df = filtered_df.sort_values(by=cost_column, ascending=False)
        print(f"\n💰 找到 {len(filtered_df)} 个整体消耗在{cost_min}-{cost_max}区间的素材:")
        print("=" * 60)
        print(f"AI分析指令将保存到: {output_file}")
        print("=" * 60)
        
        # 打开文件准备写入
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(f"AI分析指令 - 生成时间: {timestamp}\n")
            f.write("=" * 60 + "\n\n")
            
            # 处理每个素材
            for _, row in filtered_df.iterrows():
                name = row[name_column] if pd.notna(row[name_column]) else "未命名素材"
                cost = row[cost_column]
                material_id = row[id_column] if id_column and pd.notna(row[id_column]) else "-"
                play3s = row[play3s_column] if play3s_column and play3s_column in row and pd.notna(row[play3s_column]) else "未知"
                
                # 获取展现次数
                impression = row[impression_column] if impression_column and impression_column in row and pd.notna(row[impression_column]) else 0
                
                # 转换可能包含逗号的展现次数
                if isinstance(impression, str):
                    impression = impression.replace(',', '').replace(' ', '')
                
                # 计算CPM：(整体消耗 ÷ 整体展现次数) × 1000
                try:
                    if impression and float(impression) > 0:
                        calculated_cpm = (float(cost) / float(impression)) * 1000
                        cpm = f"{calculated_cpm:.2f}"  # 保留两位小数
                    else:
                        # 如果没有展现次数或为0，尝试使用原始CPM列的值
                        cpm = row[cpm_column] if cpm_column and cpm_column in row and pd.notna(row[cpm_column]) else "未知"
                except ValueError as e:
                    print(f"计算CPM时出错: {e}, 使用原始CPM列")
                    cpm = row[cpm_column] if cpm_column and cpm_column in row and pd.notna(row[cpm_column]) else "未知"
                
                cvr = row[cvr_column] if cvr_column and cvr_column in row and pd.notna(row[cvr_column]) else "未知"
                click_rate = row[click_rate_column] if click_rate_column and click_rate_column in row and pd.notna(row[click_rate_column]) else "未知"
                
                # 确保impression是字符串格式，用于显示
                impression_str = str(impression) if impression else "未知"
                
                prompt = AI_PROMPT_TEMPLATE.format(name=name, material_id=material_id, cost=cost, play3s=play3s, cpm=cpm, cvr=cvr, click_rate=click_rate, impression=impression_str,
                                                 cardinal_play3s=CARDINAL_NUMBERS["play3s"],
                                                 cardinal_click_rate=CARDINAL_NUMBERS["click_rate"],
                                                 cardinal_cvr=CARDINAL_NUMBERS["cvr"],
                                                 cardinal_cpm=CARDINAL_NUMBERS["cpm"])
                ai_result = call_gemini_ai(prompt)
                # 从八大人群分析数据中提取主要和次要受众群体信息
                audience_info = ""
                if peaks_data and str(material_id) in peaks_data:
                    material_data = peaks_data[str(material_id)]
                    # 查找八大人群分布数据
                    for img_name, img_data in material_data["images"].items():
                        if img_name.startswith("八大人群分布人数"):
                            main_audience = img_data.get("main_peak", {}).get("x", "未知")
                            secondary_audience = img_data.get("secondary_peak", {}).get("x", "未知")
                            audience_info = f"\n\n主要受众群体: {main_audience}, 次要受众群体: {secondary_audience}"
                            print(f"素材ID: {material_id} - 主要受众群体: {main_audience}, 次要受众群体: {secondary_audience}")
                            break
                
                # 合并AI分析结果和受众群体信息
                combined_result = ai_result + audience_info
                
                # 将结果写入文件
                f.write(f"素材: {name}\n")
                f.write(f"素材ID: {material_id}\n")
                f.write(f"消耗: {cost}元\n")
                f.write(f"3秒完播率: {play3s}\n")
                f.write(f"CPM: {cpm}\n")
                f.write(f"转化率: {cvr}\n")
                f.write(f"整体点击率: {click_rate}\n")
                f.write(f"整体展现次数: {impression_str}\n")
                f.write(f"AI指令: {combined_result}\n")
                f.write("-" * 40 + "\n\n")
                
                # 在控制台显示进度
                print(f"  {name}-{material_id} 消耗：{cost}，分析完成")
                time.sleep(1)
        
        print("=" * 60)
        print(f"✅ 共找到 {len(filtered_df)} 个素材并完成AI分析")
        print(f"✅ 分析结果已保存到: {output_file}")
    except Exception as e:
        print(f"❌ 处理数据时出错: {e}")
        import traceback
        traceback.print_exc()

def main():
    print("=" * 60)
    print("🔍 素材消耗区间筛选+AI分析工具")
    print("=" * 60)
    latest_file = get_latest_excel_file()
    if not latest_file:
        return
    filter_high_cost_materials(latest_file, cost_min=1000, cost_max=30000)

if __name__ == "__main__":
    main()