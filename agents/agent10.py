import datetime
import json
import os
import random
import time
import traceback
import re
import google.generativeai as genai
import pandas as pd

# --- 基本配置 ---
API_KEY = "AIzaSyDxnQNBD0dtIKtZHpubgv_ZSw7AG_7tYCU"
MODEL_NAME = "models/gemini-2.0-flash"

# --- 文件路径配置 ---
PRODUCT_JSON_PATH = r"C:\Users\EDY\Desktop\wwj\FangXieZhiLian\json\Product.json"
MERGED_MATERIAL_DATA_PATH = r"C:\Users\EDY\Desktop\wwj\FangXieZhiLian\json\素材数据分析\merged_material_data.json"  # 合并后的素材数据路径
VIDEO_FILE_PATH = r"C:\Users\EDY\Desktop\wwj\FangXieZhiLian\storage\video\留香珠\0605-留香珠-促销-【砍一刀】01-zyjd.mp4"
# 批量处理的视频目录配置
BATCH_VIDEO_DIR = r"C:\Users\EDY\Desktop\wwj\FangXieZhiLian\storage\video\留香珠"

# --- 新增函数：从data目录获取素材ID并查找对应素材名称 ---
def get_material_names_from_ids():
    """
    从data目录获取素材ID，然后在merged_material_data.json中查找对应的素材名称
    
    Returns:
        dict: 素材ID到素材名称的映射字典
    """
    # 获取当前脚本所在目录
    current_dir = os.path.dirname(os.path.abspath(__file__))
    # 获取项目根目录
    root_dir = os.path.dirname(current_dir)
    # 数据目录
    data_dir = os.path.join(root_dir, 'data')
    # 素材ID文件路径
    material_ids_file = os.path.join(data_dir, '素材ID.json')
    
    print(f"查找素材ID文件: {material_ids_file}")
    
    # 检查素材ID文件是否存在
    if not os.path.exists(material_ids_file):
        print(f"错误: 素材ID文件不存在: {material_ids_file}")
        return {}
    
    # 读取素材ID文件
    try:
        with open(material_ids_file, 'r', encoding='utf-8') as f:
            material_ids_data = json.load(f)
        
        material_ids = material_ids_data.get("素材ID列表", [])
        if not material_ids:
            print("警告: 素材ID文件中未找到素材ID列表或列表为空")
            return {}
        
        print(f"从素材ID文件中找到 {len(material_ids)} 个素材ID")
    except Exception as e:
        print(f"读取素材ID文件失败: {e}")
        return {}
    
    # 检查合并素材数据文件是否存在
    if not os.path.exists(MERGED_MATERIAL_DATA_PATH):
        print(f"错误: 合并素材数据文件不存在: {MERGED_MATERIAL_DATA_PATH}")
        return {}
    
    # 读取合并素材数据文件
    try:
        with open(MERGED_MATERIAL_DATA_PATH, 'r', encoding='utf-8') as f:
            merged_material_data = json.load(f)
        
        print(f"成功读取合并素材数据文件，包含 {len(merged_material_data)} 条素材数据")
    except Exception as e:
        print(f"读取合并素材数据文件失败: {e}")
        return {}
    
    # 创建素材ID到素材名称的映射
    material_id_to_name = {}
    found_count = 0
    
    # 遍历素材ID列表，查找对应的素材名称
    for material_id in material_ids:
        material_id_str = str(material_id)
        found = False
        
        # 在合并数据中查找对应的素材ID
        for material_data in merged_material_data:
            if str(material_data.get("素材ID", "")) == material_id_str:
                material_name = material_data.get("素材名称", "")
                if material_name:
                    material_id_to_name[material_id_str] = material_name
                    found = True
                    found_count += 1
                    print(f"找到素材ID {material_id_str} 对应的素材名称: {material_name}")
                break
        
        if not found:
            print(f"警告: 未找到素材ID {material_id_str} 对应的素材名称")
    
    print(f"总共找到 {found_count}/{len(material_ids)} 个素材ID对应的素材名称")
    return material_id_to_name

def analyze_videos_by_material_ids():
    """
    根据data目录中的素材ID查找对应的素材名称，然后分析对应的视频
    """
    print("开始根据素材ID分析视频...")
    
    # 获取素材ID到素材名称的映射
    material_id_to_name = get_material_names_from_ids()
    
    if not material_id_to_name:
        print("错误: 未找到任何素材ID对应的素材名称，无法进行视频分析")
        return
    
    # 初始化Gemini客户端
    try:
        client = genai.Client(api_key=API_KEY)
        print("Gemini客户端初始化成功")
    except Exception as e:
        print(f"Gemini客户端初始化失败: {e}")
        return
    
    # 根据素材名称查找对应的视频文件
    for material_id, material_name in material_id_to_name.items():
        print(f"\n{'='*50}")
        print(f"处理素材ID: {material_id}, 素材名称: {material_name}")
        
        # 在视频目录中查找匹配的视频文件
        video_files = []
        if os.path.exists(BATCH_VIDEO_DIR):
            for file in os.listdir(BATCH_VIDEO_DIR):
                if file.lower().endswith(('.mp4', '.avi', '.mov', '.mkv', '.wmv')):
                    # 检查视频文件名是否包含素材名称
                    if material_name in file:
                        video_files.append(os.path.join(BATCH_VIDEO_DIR, file))
        
        if not video_files:
            print(f"警告: 未找到素材名称 '{material_name}' 对应的视频文件")
            continue
        
        print(f"找到 {len(video_files)} 个匹配的视频文件:")
        for i, video_file in enumerate(video_files, 1):
            print(f"  {i}. {os.path.basename(video_file)}")
        
        # 对每个匹配的视频文件进行分析
        for video_file in video_files:
            print(f"\n分析视频: {os.path.basename(video_file)}")
            
            try:
                # 使用现有的分析函数进行视频分析
                analysis_result = analyze_material_by_video_path(
                    video_file_path=video_file,
                    client=client
                )
                
                if "error" not in analysis_result:
                    print(f"视频分析成功: {video_file}")
                else:
                    print(f"视频分析失败: {video_file}, 错误: {analysis_result['error']}")
            except Exception as e:
                print(f"视频分析过程中发生错误: {e}")
                traceback.print_exc()
    
    print("\n所有视频分析完成")

def fix_json_format(text):
    """修复常见的JSON格式问题"""
    import re
    import json
    
    # 添加调试信息
    print(f"开始修复JSON，原始长度: {len(text)} 字符")
    
    # 移除markdown代码块标记
    text = re.sub(r'^```json\s*|^\s*```\s*|\s*```$', '', text, flags=re.MULTILINE)
    text = text.strip()
    
    # 尝试直接解析
    try:
        json_obj = json.loads(text)
        print("JSON本身格式正确，无需修复")
        return text  # 如果本身就是有效JSON，直接返回
    except json.JSONDecodeError as e:
        print(f"JSON格式错误，需要修复: {e}")
        pass  # 继续尝试修复
    
    # 1. 修复字符串中的换行符
    def fix_string_newlines(match):
        content = match.group(1)
        content = content.replace('\n', '\\n').replace('\r', '\\r').replace('\t', '\\t')
        return f'"{content}"'
    
    original_text = text
    text = re.sub(r'"([^"]*(?:\n[^"]*)*)"', fix_string_newlines, text)
    if original_text != text:
        print("已修复字符串中的换行符")
    
    # 2. 修复常见的结构问题
    # 移除多余的逗号
    original_text = text
    text = re.sub(r',(\s*[}\]])', r'\1', text)
    if original_text != text:
        print("已移除多余的逗号")
    
    # 在字符串后面缺少逗号的情况
    original_text = text
    text = re.sub(r'"\s*\n\s*"', '",\n"', text)
    if original_text != text:
        print("已添加字符串间缺失的逗号")
    
    # 在数组元素后面缺少逗号
    original_text = text
    text = re.sub(r'}\s*\n\s*{', '},\n{', text)
    if original_text != text:
        print("已添加数组元素间缺失的逗号")
    
    # 在对象属性后面缺少逗号
    original_text = text
    text = re.sub(r'"([^"]+)"\s*:\s*"([^"]*)"\s*\n\s*"', r'"\1": "\2",\n"', text)
    if original_text != text:
        print("已添加对象属性间缺失的逗号")
    
    # 修复键值对中间的冒号缺失
    original_text = text
    text = re.sub(r'"([^"]+)"\s+(["{[])', r'"\1": \2', text)
    if original_text != text:
        print("已添加键值对中缺失的冒号")
    
    # 3. 修复数组中缺少引号的项
    # 这种错误通常出现在数组中的某些项缺少开头或结尾的引号
    # 例如: ["item1", item2, "item3"] 中的item2缺少引号
    # 或者: ["item1", **item2**, "item3"] 中的**item2**缺少引号
    original_text = text
    
    # 查找所有数组定义
    array_pattern = r'\[(.*?)\]'
    
    def fix_array_items(match):
        array_content = match.group(1)
        items = []
        in_string = False
        current_item = ""
        i = 0
        
        # 首先尝试分割数组项
        while i < len(array_content):
            char = array_content[i]
            
            # 处理字符串
            if char == '"' and (i == 0 or array_content[i-1] != '\\'):
                in_string = not in_string
                current_item += char
            # 处理逗号（分隔符）
            elif char == ',' and not in_string:
                items.append(current_item.strip())
                current_item = ""
            else:
                current_item += char
            
            i += 1
        
        # 添加最后一项
        if current_item.strip():
            items.append(current_item.strip())
        
        # 检查每一项是否是有效的JSON值
        fixed_items = []
        for item in items:
            item = item.strip()
            
            # 如果项不是以"开头并以"结尾，并且不是有效的JSON值(数字、true、false、null、对象、数组)
            if not (item.startswith('"') and item.endswith('"')) and \
               not (item.startswith('{') and item.endswith('}')) and \
               not (item.startswith('[') and item.endswith(']')) and \
               not item.lower() in ['true', 'false', 'null'] and \
               not re.match(r'^-?\d+(\.\d+)?$', item):
                
                # 特别处理以**开头的Markdown格式文本
                if item.startswith('**') and '**' in item[2:]:
                    item = f'"{item}"'
                    print(f"已修复数组中缺少引号的Markdown格式项: {item}")
                else:
                    # 其他情况，假设它是一个字符串，添加引号
                    item = f'"{item}"'
                    print(f"已修复数组中缺少引号的项: {item}")
            
            fixed_items.append(item)
        
        return '[' + ', '.join(fixed_items) + ']'
    
    # 应用数组项修复
    try:
        # 使用正则表达式查找所有数组并修复
        text = re.sub(array_pattern, fix_array_items, text, flags=re.DOTALL)
        if text != original_text:
            print("已修复数组中缺少引号的项")
    except Exception as e:
        print(f"修复数组项时出错: {e}")
    
    # 4. 修复括号平衡问题
    # 使用栈来跟踪括号匹配
    def fix_brackets(text):
        print("修复括号平衡问题...")
        
        # 初始化栈和位置记录
        stack = []
        unmatched_positions = []
        
        # 第一遍：找出所有不匹配的括号
        for i, char in enumerate(text):
            if char in '{[':
                # 左括号入栈
                stack.append((char, i))
            elif char in '}]':
                if not stack:
                    # 栈为空，说明这是一个多余的右括号
                    matching_char = '{' if char == '}' else '['
                    unmatched_positions.append((i, 'extra_right', char, matching_char))
                else:
                    left_char, left_pos = stack.pop()
                    # 检查括号类型是否匹配
                    if (left_char == '{' and char != '}') or (left_char == '[' and char != ']'):
                        # 类型不匹配，记录错误
                        correct_right = '}' if left_char == '{' else ']'
                        unmatched_positions.append((i, 'wrong_type', char, correct_right))
        
        # 处理栈中剩余的左括号（没有匹配的右括号）
        while stack:
            left_char, left_pos = stack.pop()
            correct_right = '}' if left_char == '{' else ']'
            unmatched_positions.append((len(text), 'missing_right', None, correct_right))
        
        # 按位置倒序排序，这样修复时不会影响后面的位置
        unmatched_positions.sort(reverse=True)
        
        # 第二遍：修复不匹配的括号
        fixed = text
        brackets_fixed = False
        
        for pos, error_type, actual_char, correct_char in unmatched_positions:
            if error_type == 'extra_right':
                # 多余的右括号，在前面添加对应的左括号
                fixed = fixed[:pos] + correct_char + fixed[pos:]
                print(f"在位置 {pos} 添加左括号 '{correct_char}' 以匹配多余的右括号 '{actual_char}'")
                brackets_fixed = True
            elif error_type == 'wrong_type':
                # 错误类型的右括号，替换为正确类型
                fixed = fixed[:pos] + correct_char + fixed[pos+1:]
                print(f"在位置 {pos} 将错误的右括号 '{actual_char}' 替换为正确的右括号 '{correct_char}'")
                brackets_fixed = True
            elif error_type == 'missing_right':
                # 缺少右括号，在末尾添加
                fixed = fixed[:pos] + correct_char + fixed[pos:]
                print(f"在位置 {pos} (末尾) 添加缺失的右括号 '{correct_char}'")
                brackets_fixed = True
        
        return fixed, brackets_fixed
    
    # 应用括号修复
    fixed_text, brackets_fixed = fix_brackets(text)
    
    # 如果修复了括号，使用修复后的文本
    if brackets_fixed:
        text = fixed_text
        print("已修复括号平衡问题")
    
    # 尝试解析修复后的文本
    try:
        json_obj = json.loads(text)
        print("JSON修复成功")
        return text
    except json.JSONDecodeError as e:
        print(f"JSON仍然无效，错误: {e}")
    
    # 5. 最后尝试从文本中提取有效的JSON对象
    json_start = text.find('{')
    if json_start >= 0:
        # 尝试提取最外层的完整JSON对象
        brace_count = 0
        for i, char in enumerate(text[json_start:], json_start):
            if char == '{':
                brace_count += 1
            elif char == '}':
                brace_count -= 1
                if brace_count == 0:
                    try:
                        extracted_json = text[json_start:i+1]
                        json.loads(extracted_json)  # 验证提取的JSON
                        print(f"成功提取有效JSON部分，长度: {len(extracted_json)} 字符")
                        return extracted_json
                    except json.JSONDecodeError:
                        print("提取的JSON部分仍然无效")
    
    # 如果所有尝试都失败，返回原始文本
    print("所有JSON修复尝试都失败")
    return text

def load_product_info():
    """加载产品信息"""
    try:
        with open(PRODUCT_JSON_PATH, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"错误: 产品信息文件未找到: {PRODUCT_JSON_PATH}")
        return None
    except json.JSONDecodeError:
        print(f"错误: 产品信息文件格式错误: {PRODUCT_JSON_PATH}")
        return None

def find_material_data_from_json(material_name=None, material_id=None):
    """
    从合并的JSON文件中查找素材数据，可以通过素材名称或素材ID查找
    
    Args:
        material_name: 素材名称
        material_id: 素材ID
        
    Returns:
        dict: 素材数据和行为曲线数据的合并结果，如果未找到则返回None
    """
    try:
        # 读取合并后的素材数据文件
        with open(MERGED_MATERIAL_DATA_PATH, 'r', encoding='utf-8') as f:
            materials_data = json.load(f)
        
        # 根据提供的条件查找匹配的素材
        for material_data in materials_data:
            # 如果提供了素材名称且匹配
            if material_name and material_data.get('素材名称') == material_name:
                print(f"在合并数据文件中找到素材: {material_name}")
                return material_data
            
            # 如果提供了素材ID且匹配
            if material_id and str(material_data.get('素材ID')) == str(material_id):
                print(f"在合并数据文件中找到素材ID: {material_id}")
                return material_data
        
        # 如果未找到匹配的素材
        if material_name:
            print(f"警告: 在合并数据文件中未找到素材名称: {material_name}")
        if material_id:
            print(f"警告: 在合并数据文件中未找到素材ID: {material_id}")
        return None
        
    except FileNotFoundError:
        print(f"错误: 合并数据文件未找到: {MERGED_MATERIAL_DATA_PATH}")
        return None
    except json.JSONDecodeError:
        print(f"错误: 合并数据文件格式错误: {MERGED_MATERIAL_DATA_PATH}")
        return None
    except Exception as e:
        print(f"读取合并数据文件失败: {e}")
        return None

def format_behavior_curve_data_from_json(material_data):
    """
    从合并的JSON文件中提取并格式化用户行为曲线数据
    
    Args:
        material_data: 从合并JSON获取的素材数据
        
    Returns:
        str: 格式化后的用户行为曲线数据字符串
    """
    if not material_data or "images" not in material_data:
        return "未找到用户行为曲线数据"
    
    behavior_str = ""
    images_data = material_data["images"]
    
    # 处理流失数据
    for image_name, data in images_data.items():
        if "整体流失数" in image_name:
            if data.get("main_peak"):
                main_peak = data["main_peak"]
                behavior_str += f"**主要流失高峰:** 时间点 {main_peak['x']}，流失数 {main_peak['y']}\\n"
            if data.get("secondary_peak"):
                secondary_peak = data["secondary_peak"]
                behavior_str += f"**次要流失高峰:** 时间点 {secondary_peak['x']}，流失数 {secondary_peak['y']}\\n"
    
    # 处理点击数据
    for image_name, data in images_data.items():
        if "整体点击次数" in image_name:
            if data.get("main_peak"):
                main_peak = data["main_peak"]
                behavior_str += f"**主要点击高峰:** 时间点 {main_peak['x']}，点击次数 {main_peak['y']}\\n"
            if data.get("secondary_peak"):
                secondary_peak = data["secondary_peak"]
                behavior_str += f"**次要点击高峰:** 时间点 {secondary_peak['x']}，点击次数 {secondary_peak['y']}\\n"
    
    return behavior_str if behavior_str else "用户行为曲线数据格式异常"

def extract_card_keywords_from_material_name(material_name):
    """从素材名称中提取可能的卡片关键词"""
    # 使用正则表达式提取中括号内的内容作为关键词
    keywords = re.findall(r'【([^】]+)】', material_name)
    return keywords

def parse_video_duration(duration_str):
    """解析视频时长字符串为秒数"""
    try:
        if ":" in duration_str:
            parts = duration_str.split(":")
            if len(parts) == 2:  # MM:SS格式
                minutes, seconds = map(int, parts)
                return minutes * 60 + seconds
            elif len(parts) == 3:  # HH:MM:SS格式
                hours, minutes, seconds = map(int, parts)
                return hours * 3600 + minutes * 60 + seconds
        else:
            # 假设是纯秒数
            return int(duration_str)
    except:
        return 0

def generate_material_analysis_report(client, model_name, video_file_path, material_name, max_retries=3):
    """
    生成素材分析报告
    
    参数:
    client: 已初始化的 genai.Client 实例
    model_name: 使用的Gemini模型名称
    video_file_path: 视频文件路径
    material_name: 素材名称
    max_retries: 最大重试次数
    """
    print(f"开始分析素材: {material_name}")
    
    # 加载产品信息
    product_info = load_product_info()
    if not product_info:
        return {"error": "无法加载产品信息"}
    
    # 从合并的JSON文件中查找素材数据
    material_data = find_material_data_from_json(material_name=material_name)
    if not material_data:
        print(f"警告: 未找到素材 '{material_name}' 的数据，将尝试仅使用视频内容进行分析")
        # 创建一个包含基本信息的空数据对象
        material_data = {
            "素材ID": "未找到",
            "素材名称": material_name,
            "整体成交金额": 0,
            "整体支付ROI": 0,
            "整体点击率": 0,
            "整体转化率": 0,
            "平均观看时长": 0,
            "视频完播率": 0,
            "3秒播放率": 0,
            "素材时长": "00:00"
        }
    
    # 提取素材数据中的关键指标
    material_id = material_data.get("素材ID", "未找到")
    gmv = material_data.get("整体成交金额", 0)
    roi = material_data.get("整体支付ROI", 0)
    ctr = material_data.get("整体点击率", 0)
    cvr = material_data.get("整体转化率", 0)
    avg_watch_time = material_data.get("平均观看时长", 0)
    completion_rate = material_data.get("视频完播率", 0)
    play_rate_3s = material_data.get("3秒播放率", 0)
    video_duration_str = material_data.get("素材时长", "00:00")
    video_duration_seconds = parse_video_duration(video_duration_str)
    
    # 提取调控相关指标
    adjust_cost = material_data.get("追投调控消耗", 0)
    adjust_gmv = material_data.get("追投调控成交金额", 0)
    adjust_roi = material_data.get("追投调控支付ROI", 0)
    adjust_ctr = material_data.get("追投调控点击率", 0)
    adjust_cvr = material_data.get("追投调控转化率", 0)
    
    # 格式化素材数据展示
    material_data_str = "**完整素材数据：**\n"
    for key, value in material_data.items():
        if key != "images" and pd.notna(value):  # 排除images字段并只显示非空值
            material_data_str += f"  * {key}: {value}\n"
    
    # 可选的视觉和音频描述（这些需要通过视频分析获得，这里先设置为待分析）
    visual_description = "需要通过观看视频进行描述"
    audio_description = "需要通过观看视频进行描述"
    rhythm_perception = "需要通过观看视频进行描述"
    
    # 格式化用户行为曲线数据
    behavior_curve_str = format_behavior_curve_data_from_json(material_data)
    
    # 从素材名称中提取卡点关键词
    card_keywords = extract_card_keywords_from_material_name(material_name)
    
    # 构建分析提示词
    prompt = f"""作为一名专业的短视频内容优化与营销分析专家，请对以下提供的PWU留香珠视频素材进行深度分析。该视频旨在通过抖音平台为直播间引流，并最终提升GMV和ROI。在您的分析中，如果某些解读涉及到用户类型（如新老客）或具体意图，但缺乏直接数据支持，请明确指出这是基于内容特征的合理推测或假设。

**背景信息：**
* **产品：** PWU留香珠
* **核心营销目标：** 提升直播间引流效率，最大化GMV和ROI。

**产品详细信息：**
{json.dumps(product_info, ensure_ascii=False, indent=2)}

**待分析视频素材信息：**

* **素材ID：** {material_id}
* **素材名称：** {material_name}
* **核心表现数据：**
    * GMV：{gmv}
    * ROI：{roi}
    * CTR (进入直播间按钮点击率)：{ctr}
    * CVR (直播间内转化率)：{cvr}
    * 平均观看时长：{avg_watch_time} 秒
    * 视频完播率：{completion_rate}
    * 前3秒/5秒播放率：{play_rate_3s}
    * 追投调控消耗：{adjust_cost}
    * 追投调控成交金额：{adjust_gmv}
    * 追投调控支付ROI：{adjust_roi}
    * 追投调控点击率：{adjust_ctr}
    * 追投调控转化率：{adjust_cvr}

{material_data_str}

* **内容特征：**
    * **核心卡片关键词/短语标签：** {', '.join(card_keywords) if card_keywords else "未在素材数据中找到"}
    * **视频时长：** {video_duration_seconds} 秒
    * **（可选）视觉整体描述：** {visual_description}
    * **（可选）音频/BGM描述：** {audio_description}
    * **（可选）整体节奏感知：** {rhythm_perception}
* **用户行为曲线数据（事件与内容时间戳精准对应，并请特别关注关键转化场景/元素出现时刻的用户行为）：**
{behavior_curve_str}

**请基于以上全部信息（如果视频已成功上传并处理，请结合视频内容本身；如果视频未提供或处理失败，请主要基于给定的数据进行分析），进行深入分析并回答以下问题（分析最终需落脚于如何提升GMV和ROI）：**

1.  **关键用户行为节点分析（点击与跳失）：**
    * **高点击时刻分析：** 视频中哪些时间点出现了明显的"进入直播间"点击行为的提升或高峰？请结合对应时刻的**具体画面、文案、声音、卡片关键词呈现、引导方式，特别是是否出现了预设的"高点击高转化镜头"（如痛点解决、功效证明等）**，分析是什么最可能驱动了用户的点击？这些成功的点击引导对整体CTR以及潜在的GMV/ROI有何贡献？
    * **高流失时刻分析：** 视频中哪些时间点出现了显著的用户流失高峰？请结合对应时刻的**具体画面、文案、声音、节奏变化、卡片关键词匹配度**等内容元素，分析是什么最可能导致了用户的离开？**如果流失发生在"高点击高转化镜头"展示期间或之后，可能的原因是什么（例如，呈现方式不佳、信息过载、用户不信任等）？**
    * **开篇用户行为解读：** 开头几秒（例如0-5秒）用户的点击和跳失行为（例如，高跳失是否在筛选非目标用户，还是钩子本身有问题，或卡片关键词与开篇内容预期不符？早期低点击是否正常，或有提升空间？）反映了什么问题或机会点？

2.  **内容要素有效性评估（画面、音频、节奏、Agent1逻辑、核心卡片关键词/短语标签、关键转化场景/元素）：**
    * **画面表现：** 整体视觉呈现（清晰度、美感、创意、镜头运用、转场等）对于吸引用户、传递信息、展示产品（尤其针对留香珠"香味不可视"的特点，是否通过间接视觉有效传达了香气体验）的效果如何？有哪些亮点或不足？
    * **音频与BGM：** 音频（人声、音效）和背景音乐的选择与视频内容、节奏和期望传递的情绪是否匹配？是增强了效果还是分散了注意力？
    * **视频节奏：** 整体节奏（包括信息密度、场景切换速度等）是否恰当？能否抓住用户注意力并引导其完整观看核心信息和行动号召？是否存在拖沓或过快导致信息接收障碍的片段？
    * **Agent1逻辑要素在本视频中的应用效果（请结合产品匹配度和实际用户行为反馈进行评估）：**
        * "文案强句式"是否运用得当、有记忆点，并有效传递了产品价值？
        * "痛点解决匹配度"在此视频中呈现得是否精准、深刻，能否有效激发用户需求并引导其关注解决方案（产品）？
        * "美好场景营造"是否成功，能否让用户产生向往感并与产品核心利益点（如持久留香带来的自信愉悦）关联？
        * "可视化表现方式"是否直观、有冲击力，并能有效展示PWU留香珠的产品特点或使用效果？
    * **核心卡片关键词/短语标签有效性：** 本视频使用的卡片关键词与视频内容（尤其是高光时刻、引导时刻）的匹配度和呼应程度如何？它们是否可能促进了用户的理解、点击，并吸引了精准的目标用户？
    * **关键转化场景/元素分析 (Analysis of Key Conversion Scenes/Elements):**
        * 视频中是否包含了以下（或类似的）被认为具有高点击/高转化潜力的场景或元素？请识别它们出现的具体时间点：
            * **痛点明确解决场景：** (例如，清晰展示衣物异味被消除、污渍被洗净等，并展现使用PWU留香珠后的满足感)
            * **核心功效强力证明/承诺：** (例如，"180天持久留香"的可视化或情境化表达、或"99%除菌除螨"的证书/实验数据/权威认证画面的清晰展示等)
            * **独特价值主张（UVP）的突出展示：** (例如，与其他产品形成鲜明对比的优势点，如香型独特、多效合一等)
            * **强信任背书元素：** (例如，用户好评截图、KOL/KOC推荐片段精华、品牌研发实力或获奖信息展示等)
        * **效果评估（核心：结合用户行为曲线进行精准映射）：** 请结合这些关键转化场景/元素的出现时间点，**精准分析**其与紧邻的用户行为曲线（点击高峰、跳失情况、观看时长变化、互动数据变化等）的对应关系。
            * 它们是否有效地吸引了用户注意力、提升了信任感、并促进了点击意愿？（例如，展示"除菌证书"后1-2秒内，用户跳失是否显著降低，或CTR是否有小幅但明确的提升？）
            * 如果这些关键转化元素存在，但并未带来预期的正面用户行为反馈（例如，展示"180天留香"后反而出现跳失），可能的原因是什么？（例如，呈现方式缺乏说服力、时长分配不当、信息不清晰易懂、与前后内容衔接突兀、不符合用户当前心理预期等）
            * 如果视频中缺失了某些针对PWU留香珠本应有的关键转化元素（例如，对于"持久留香"缺乏有力的支撑信息或场景），这对整体转化和用户信任构建可能造成了什么影响？

3.  **综合诊断与归因（围绕GMV/ROI）：**
    * **整体表现归因：** 综合以上所有分析，这条视频取得当前**整体**GMV和ROI表现的主要原因是什么？请结合整体CTR、CVR、观看时长等过程指标进行全面阐述，并明确指出内容上的优缺点是如何导致这一结果的。
    * **追投调控效果专项分析：**
        * **调控数据解读：** 调控期间的各项核心指标（追投调控消耗、追投调控成交金额、追投调控支付ROI、追投调控点击率、追投调控转化率）表现如何？与视频的整体大盘数据相比，这些指标是更高还是更低？这反映了什么问题或机会？
        * **调控策略与内容匹配度分析：** 基于调控数据与整体数据的差异，请推断并分析调控期间可能的人群定向或出价策略。例如，如果调控CTR远高于整体，但CVR持平或略低，这可能意味着什么？视频的哪些内容元素（如开篇钩子、核心卖点）可能与调控策略下的人群更匹配（或不匹配）？
        * **从调控数据看优化方向：** 调控数据为我们揭示了哪些最关键的优化方向？（例如：调控ROI表现不佳，是因为点击成本过高，还是转化率太低？这分别对应了内容素材的哪些方面需要优化？）
    * **内容层面主要优点（对GMV/ROI的促进因素）：** 内容层面，其最大的1-2个优点（最可能促进了GMV/ROI及各项调控指标的关键因素，例如某个成功的"关键转化场景"或高效的"Agent1逻辑要素"应用）是什么？
    * **内容层面主要缺点（对GMV/ROI的阻碍因素）：** 内容层面，其最大的1-2个缺点或错失的机会点（最可能阻碍了GMV/ROI及各项调控指标提升的关键因素，例如某个失败的"关键转化场景"或缺失的"痛点解决"）是什么？

4.  **给Agent9的具体优化建议：**
    * **针对此条视频的修改建议：** 如果要重新剪辑优化这条视频，你会建议在哪些具体的时间点，对哪些具体的内容元素（画面、文案、BGM、节奏、卡片关键词配合、"关键转化场景/元素"的呈现方式等）进行怎样的修改？目标是什么？（请尽可能具体）
    * **针对后续素材创作的普适性建议：** 从这条视频的分析中，可以提炼出哪些适用于其他类似素材创作或优化的通用规则或注意事项？**特别是，从调控数据中可以吸取哪些关于人群、出价或定向的经验教训，以便指导未来的内容创作方向？**
    * **A/B测试建议：** 基于此视频的分析，有哪些值得进行A/B测试的关键变量或优化点子？（例如，测试不同"痛点解决场景"的呈现时长，或不同"核心功效证明"的视觉方案）

请以JSON格式输出您的分析结果，确保所有键名均使用中文。请严格遵守JSON规范：
1.  不要在列表或对象的最后一个元素后面添加逗号。
2.  在同一个JSON对象内部，**每一个键名必须是唯一的**。绝对不允许出现重复的键名。
3.  **每个键对应的值必须是一个单一的、完整的字符串。** 如果一段分析内容较长，请将所有相关的论点、描述、解释等全部合并到这个单一的字符串值中。您可以在字符串内部使用 \\\\n 来表示换行，以保持可读性。
    例如，对于 "高点击时刻分析"，即使分析内容有很多点，也应该是：
    `"高点击时刻分析": "第一点分析...\\n第二点分析...\\n第三点分析..."`
    而不是 (错误的做法!)：
    `"高点击时刻分析": "第一点分析...",`
    `"高点击时刻分析": "第二点分析...",`

格式如下：
{{
  "素材ID": "{material_id}",
  "素材名称": "{material_name}",
  "分析时间": "{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
  "关键用户行为节点分析": {{
    "高点击时刻分析": "对高点击时刻的详细分析，包含多个要点，用\\n分隔。\\n例如：\\n- 时间点A的点击原因分析...\\n- 时间点B的点击原因分析...",
    "高流失时刻分析": "对高流失时刻的详细分析，包含多个要点，用\\n分隔。\\n例如：\\n- 时间点X的流失原因分析...\\n- 时间点Y的流失原因分析...",
    "开篇用户行为解读": "对开篇用户行为的详细解读，包含多个方面，用\\n分隔。\\n例如：\\n- 开篇钩子有效性评估...\\n- 早期流失与目标人群筛选..."
  }},
  "内容要素有效性评估": {{
    "画面表现": "对画面表现的详细评估，包含多个方面，用\\n分隔。",
    "音频与BGM": "对音频与BGM的详细评估，包含多个方面，用\\n分隔。",
    "视频节奏": "对视频节奏的详细评估，包含多个方面，用\\n分隔。",
    "Agent1逻辑要素应用效果": {{
      "文案强句式应用效果": "对文案强句式应用效果的详细评估，用\\n分隔。",
      "痛点解决匹配度评估": "对痛点解决匹配度的详细评估，用\\n分隔。",
      "美好场景营造效果": "对美好场景营造效果的详细评估，用\\n分隔。",
      "可视化表现方式效果": "对可视化表现方式效果的详细评估，用\\n分隔。"
    }},
    "核心卡片关键词有效性": "对核心卡片关键词有效性的详细评估，用\\n分隔。",
    "关键转化场景/元素分析": {{
        "识别到的关键转化场景/元素": [
            "描述识别到的关键转化场景或元素，包括时间点和内容描述"
         ],
        "效果评估": "对关键转化场景/元素效果的详细评估，包含多个要点，用\\n分隔。
        \\n例如：
        \\n- 场景1的效果分析...
        \\n- 场景2的不足之处..."
    }}
  }},
  "综合诊断与归因": {{
    "整体表现归因": "对视频整体表现的归因分析...",
    "调控效果专项分析": "对调控数据的专项分析，包括数据解读、策略推断和优化方向...",
    "内容层面主要优点": ["优点1的详细描述（对GMV/ROI及各项调控指标的促进作用）...", "优点2的详细描述..."],
    "内容层面主要缺点": ["缺点1的详细描述（对GMV/ROI及各项调控指标的阻碍作用）...", "缺点2的详细描述..."]
  }},
  "优化建议": {{
    "针对此条视频修改建议": ["具体修改建议1的详细描述...", "具体修改建议2的详细描述..."],
    "后续素材创作建议": ["普适性建议1的详细描述...", "普适性建议2的详细描述..."],
    "A/B测试建议": ["A/B测试建议1的详细描述...", "A/B测试建议2的详细描述..."]
  }}
}}

请确保分析深度和具体性，特别关注用户行为曲线数据与视频内容的对应关系，避免泛泛而谈。
"""

    try:
        # 上传视频文件（带重试机制）
        video_file_response = upload_video_with_retry(client, video_file_path, max_retries=3)
        
        # 增加健壮性：检查上传是否成功
        if not video_file_response:
            print("视频上传失败，无法继续分析。")
            return {"error": "视频上传失败，已达到最大重试次数"}
        
        # 等待视频处理完成
        video_file_status = client.files.get(name=video_file_response.name)
        while video_file_status.state.name == "PROCESSING":
            print("视频仍在处理中，请稍候...")
            time.sleep(5)
            video_file_status = client.files.get(name=video_file_response.name)
        
        if video_file_status.state.name == "FAILED":
            print(f"视频处理失败: {video_file_status.state}")
            return {"error": f"视频处理失败: {video_file_status.state}"}
        
        if video_file_status.state.name != "ACTIVE":
            print(f"视频文件未能激活，当前状态: {video_file_status.state.name}")
            return {"error": f"视频文件状态异常: {video_file_status.state.name}"}
        
        print("视频文件已激活，开始分析...")
        
        # 使用重试机制调用Gemini API
        for attempt in range(max_retries):
            try:
                # 在重试前添加随机延迟，避免同时请求
                if attempt > 0:
                    delay = random.uniform(5, 15) + (attempt * 10)  # 5-15秒基础延迟 + 递增延迟
                    print(f"API重试 {attempt + 1}/{max_retries}，等待 {delay:.1f} 秒...")
                    time.sleep(delay)
                
                print(f"调用Gemini API分析视频 (尝试 {attempt + 1}/{max_retries})...")
                response = client.models.generate_content(
                    model=model_name,
                    contents=[video_file_status, prompt]
                )
                
                # 如果成功获得响应，跳出重试循环
                break
                
            except Exception as e:
                error_str = str(e)
                print(f"API调用尝试 {attempt + 1} 失败: {error_str}")
                
                # 检查是否是503服务器过载错误
                if "503" in error_str and "overloaded" in error_str.lower():
                    if attempt < max_retries - 1:
                        wait_time = (attempt + 1) * 30 + random.uniform(10, 30)  # 递增等待时间
                        print(f"服务器过载，等待 {wait_time:.1f} 秒后重试...")
                        time.sleep(wait_time)
                        continue
                    else:
                        print("所有重试尝试都失败，服务器持续过载")
                        return {"error": f"API服务器过载，已重试{max_retries}次: {error_str}"}
                
                # 检查是否是服务器连接问题或其他可重试的错误
                elif any(code in error_str.lower() for code in ["429", "502", "504", "server disconnected", "connection", "timeout"]):
                    if attempt < max_retries - 1:
                        wait_time = (attempt + 1) * 20 + random.uniform(5, 15)
                        print(f"遇到连接问题，等待 {wait_time:.1f} 秒后重试...")
                        time.sleep(wait_time)
                        continue
                    else:
                        return {"error": f"API连接失败，已重试{max_retries}次: {error_str}"}
                
                # 对于不可重试的错误，直接返回
                else:
                    print(f"遇到不可重试的错误: {error_str}")
                    return {"error": f"API调用失败: {error_str}"}
        else:
            # 如果所有重试都失败了
            return {"error": "API调用失败，已达到最大重试次数"}
        
        # 处理响应
        if not hasattr(response, 'text') or response.text is None:
            print("错误：API响应无效")
            if hasattr(response, 'candidates') and response.candidates:
                try:
                    raw_text = response.candidates[0].content.parts[0].text
                    print("成功从candidates中获取响应文本")
                except (IndexError, AttributeError) as e:
                    print(f"无法从candidates中获取文本: {e}")
                    return {"error": "API响应无效"}
            else:
                return {"error": "API响应无效"}
        else:
            raw_text = response.text.strip()
        
        if not raw_text:
            return {"error": "API响应为空"}
        
        # 清理响应文本
        # 检查并去除markdown代码块标记
        if raw_text.startswith("```json"):
            raw_text = raw_text[7:]
        elif raw_text.startswith("```"):
            raw_text = raw_text[3:]
        if raw_text.endswith("```"):
            raw_text = raw_text[:-3]
        
        # 检查是否还有其他markdown代码块
        raw_text = raw_text.strip()
        
        # 输出部分原始文本，帮助调试
        max_debug_length = 500  # 设置一个合理的长度来显示部分文本
        print(f"原始JSON响应前{min(max_debug_length, len(raw_text))}字符:")
        print(raw_text[:max_debug_length] + ("..." if len(raw_text) > max_debug_length else ""))
        
        # 解析JSON响应
        try:
            analysis_result = json.loads(raw_text.strip())
            print("素材分析完成")
            return analysis_result
        except json.JSONDecodeError as e:
            print(f"JSON解析失败，尝试修复... 错误: {e}")
            
            # 尝试修复常见的JSON格式问题
            try:
                fixed_text = fix_json_format(raw_text)
                
                # 如果修复后文本发生了变化，输出一部分帮助调试
                if fixed_text != raw_text:
                    print(f"修复后JSON前{min(max_debug_length, len(fixed_text))}字符:")
                    print(fixed_text[:max_debug_length] + ("..." if len(fixed_text) > max_debug_length else ""))
                
                try:
                    analysis_result = json.loads(fixed_text)
                    print("JSON修复成功")
                    return analysis_result
                except json.JSONDecodeError as e2:
                    print(f"JSON修复解析失败: {e2}")
                    
                    # 最后尝试：创建一个基本的结果对象，包含原始响应
                    return {
                        "error": "JSON解析失败", 
                        "素材ID": material_id,
                        "素材名称": material_name,
                        "分析时间": datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                        "raw_response": raw_text[:10000]  # 限制原始响应的长度
                    }
            except Exception as e3:
                print(f"JSON修复过程失败: {e3}")
                return {"error": "JSON解析失败", "raw_response": raw_text[:10000]}
    
    except Exception as e:
        print(f"分析过程中发生错误: {e}")
        traceback.print_exc()
        return {"error": f"分析失败: {str(e)}"}

def save_analysis_report(analysis_result, material_name, output_dir=r"C:\Users\EDY\Desktop\wwj\FangXieZhiLian\json"):
    """保存分析报告到文件"""
    try:
        # 确保输出目录存在
        os.makedirs(output_dir, exist_ok=True)
        
        # 检查分析结果是否包含错误
        has_error = "error" in analysis_result
        
        # 生成文件名
        safe_material_name = re.sub(r'[<>:"/\\|?*]', '_', material_name)
        if has_error:
            # 如果是错误，添加错误标记到文件名
            output_file = os.path.join(output_dir, f"素材分析报告_{safe_material_name}_ERROR.json")
        else:
            output_file = os.path.join(output_dir, f"素材分析报告_{safe_material_name}.json")
        
        # 保存文件
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(analysis_result, f, ensure_ascii=False, indent=2)
        
        if has_error:
            print(f"分析出现错误，错误报告已保存到: {output_file}")
            
            # 如果有原始响应，保存到单独的文件以便后续调试
            if "raw_response" in analysis_result:
                raw_response_file = os.path.join(output_dir, f"原始响应_{safe_material_name}.txt")
                with open(raw_response_file, 'w', encoding='utf-8') as f:
                    f.write(str(analysis_result.get("raw_response", "")))
                print(f"原始响应已保存到: {raw_response_file}")
        else:
            print(f"分析报告已保存到: {output_file}")
        
        return output_file
    except Exception as e:
        print(f"保存分析报告失败: {e}")
        return None

def extract_material_name_from_video_path(video_file_path):
    """从视频文件路径中提取素材名称"""
    try:
        # 使用正确的路径处理方式
        # 获取文件名（不包含路径）
        filename = os.path.basename(video_file_path)
        # 去掉文件扩展名
        material_name = os.path.splitext(filename)[0]
        return material_name
    except Exception as e:
        print(f"提取素材名称失败: {e}")
        return None

def upload_video_with_retry(client, video_file_path, max_retries=3):
    """带重试机制的视频上传"""
    import time
    
    for attempt in range(max_retries):
        try:
            print(f"正在上传视频文件 (尝试 {attempt + 1}/{max_retries}): {video_file_path}")
            video_file_response = client.files.upload(file=video_file_path)
            print(f"视频上传成功，文件ID: {video_file_response.name}")
            return video_file_response
        except Exception as e:
            print(f"上传尝试 {attempt + 1} 失败: {e}")
            if attempt < max_retries - 1:
                wait_time = (attempt + 1) * 5  # 递增等待时间
                print(f"等待 {wait_time} 秒后重试...")
                time.sleep(wait_time)
            else:
                print("所有上传尝试都失败了")
                return None

def analyze_material_by_video_path(video_file_path, client=None):
    """
    通过视频文件路径分析素材的便捷函数
    
    Args:
        video_file_path: 视频文件路径
        client: Gemini客户端（可选，如果不提供会自动创建）
    
    Returns:
        dict: 分析报告
    """
    # 如果没有提供客户端，自动创建
    if client is None:
        try:
            client = genai.Client(api_key=API_KEY)
            print("Gemini客户端初始化成功")
        except Exception as e:
            print(f"Gemini客户端初始化失败: {e}")
            return {"error": f"客户端初始化失败: {str(e)}"}
    
    # 从视频文件路径提取素材名称
    material_name = extract_material_name_from_video_path(video_file_path)
    if not material_name:
        return {"error": "无法从视频文件路径中提取素材名称"}
    
    # 从BATCH_VIDEO_DIR中提取文件夹名称，用于输出路径
    output_subdir = extract_folder_name_from_path(BATCH_VIDEO_DIR)
    output_dir = os.path.join(r"C:\Users\EDY\Desktop\wwj\FangXieZhiLian\json", output_subdir)
    
    print(f"开始分析素材:")
    print(f"  视频文件: {video_file_path}")
    print(f"  素材名称: {material_name}")
    print(f"  输出目录: {output_dir}")
    
    # 执行分析
    analysis_result = generate_material_analysis_report(
        client=client,
        model_name=MODEL_NAME,
        video_file_path=video_file_path,
        material_name=material_name
    )
    
    # 自动保存结果到指定目录
    if "error" not in analysis_result:
        output_file = save_analysis_report(analysis_result, material_name, output_dir)
        if output_file:
            analysis_result["saved_to"] = output_file
        print(f"素材分析完成！报告已保存到: {output_file}")
    else:
        print(f"分析失败: {analysis_result['error']}")
    
    return analysis_result

def extract_folder_name_from_path(path):
    """
    从路径中提取文件夹名称
    例如，从 "C:/Users/EDY/Desktop/wwj/FangXieZhiLian/storage/video/留香珠" 提取 "留香珠"
    
    Args:
        path: 路径字符串
        
    Returns:
        str: 提取的文件夹名称，如果无法提取则返回"default"
    """
    try:
        # 使用os.path.normpath标准化路径（处理正反斜杠）
        normalized_path = os.path.normpath(path)
        # 分割路径
        parts = normalized_path.split(os.sep)
        
        # 查找"video"在路径中的位置
        video_index = -1
        for i, part in enumerate(parts):
            if part.lower() == "video":
                video_index = i
                break
        
        # 如果找到"video"且后面还有路径部分，返回"video"后面的第一个文件夹名
        if video_index >= 0 and video_index + 1 < len(parts):
            return parts[video_index + 1]
        
        # 如果找不到"video"或没有后续路径，返回最后一个路径部分
        if len(parts) > 0:
            return parts[-1]
        
        # 兜底返回"default"
        return "default"
    except Exception as e:
        print(f"提取文件夹名称失败: {e}")
        return "default"


    """
    批量分析指定目录下的所有视频文件
    
    Args:
        video_directory: 视频文件目录
        client: Gemini客户端
    
    Returns:
        dict: 分析结果统计信息
    """
    import time
    import random
    
    print(f"\n=== 开始批量分析视频文件 ===")
    print(f"视频目录: {video_directory}")
    
    # 从视频目录提取子目录名，用于输出路径
    output_subdir = extract_folder_name_from_path(video_directory)
    default_output_dir = os.path.join(r"C:\Users\EDY\Desktop\wwj\FangXieZhiLian\json", output_subdir)
    
    # 确保输出目录存在
    os.makedirs(default_output_dir, exist_ok=True)
    print(f"输出目录: {default_output_dir}")
    
    # 获取所有视频文件
    video_files = []
    if os.path.exists(video_directory):
        for file in os.listdir(video_directory):
            if file.lower().endswith(('.mp4', '.avi', '.mov', '.mkv', '.wmv')):
                video_files.append(os.path.join(video_directory, file))
    else:
        print(f"错误: 视频目录不存在: {video_directory}")
        return {"error": "视频目录不存在"}
    
    if not video_files:
        print("错误: 指定目录下没有找到视频文件")
        return {"error": "没有找到视频文件"}
    
    print(f"找到 {len(video_files)} 个视频文件:")
    for i, video_file in enumerate(video_files, 1):
        print(f"  {i}. {os.path.basename(video_file)}")
    
    # 分析结果统计
    analysis_results = []
    successful_analyses = []
    partial_analyses = []  # 部分成功的分析（有错误但有部分数据）
    failed_analyses = []
    
    # 逐个分析视频
    for i, video_file_path in enumerate(video_files, 1):
        print(f"\n{'='*50}")
        print(f"分析进度: {i}/{len(video_files)} ({i/len(video_files)*100:.1f}%)")
        print(f"当前视频: {os.path.basename(video_file_path)}")
        print(f"{'='*50}")
        
        # 从视频文件路径提取素材名称
        material_name = extract_material_name_from_video_path(video_file_path)
        if not material_name:
            print(f"无法提取素材名称，跳过: {video_file_path}")
            failed_analyses.append({
                "video_file": video_file_path,
                "error": "无法提取素材名称"
            })
            continue
        
        print(f"素材名称: {material_name}")
        
        # 检查是否已存在分析报告
        safe_material_name = re.sub(r'[<>:"/\\|?*]', '_', material_name)
        output_file = os.path.join(default_output_dir, f"素材分析报告_{safe_material_name}.json")
        error_output_file = os.path.join(default_output_dir, f"素材分析报告_{safe_material_name}_ERROR.json")
        
        # 处理已存在的报告
        if os.path.exists(output_file) or os.path.exists(error_output_file):
            result = handle_existing_report(video_file_path, material_name, output_file, error_output_file, 
                                           successful_analyses, partial_analyses, analysis_results)
            if result:  # 如果处理了已存在的报告，继续下一个视频
                continue
        
        try:
            # 在分析前添加延迟，避免API过载
            if i > 1:  # 第一个视频不需要延迟
                delay = random.uniform(15, 25)  # 15-25秒随机延迟
                print(f"等待 {delay:.1f} 秒以避免API过载...")
                time.sleep(delay)
            
            # 调用单个视频分析函数，会自动保存结果到指定目录
            analysis_result = analyze_material_by_video_path(
                video_file_path=video_file_path,
                client=client
            )
            
            # 处理分析结果
            handle_analysis_result(analysis_result, video_file_path, material_name, default_output_dir,
                                  successful_analyses, partial_analyses, failed_analyses, analysis_results)
            
            # 处理API过载错误，添加额外延迟
            if "error" in analysis_result and ("overloaded" in str(analysis_result.get('error', "")).lower() 
                                             or "503" in str(analysis_result.get('error', ""))):
                extra_delay = random.uniform(30, 60)
                print(f"检测到API过载，额外等待 {extra_delay:.1f} 秒...")
                time.sleep(extra_delay)
                
        except KeyboardInterrupt:
            print(f"\n⚠️  用户中断了批量分析过程")
            print(f"已完成 {len(successful_analyses)} 个视频的分析")
            print(f"可以重新运行程序继续分析剩余视频（程序会自动跳过已分析的视频）")
            break
            
        except Exception as e:
            print(f"❌ 处理视频时发生错误: {e}")
            traceback.print_exc()
            failed_analyses.append({
                "video_file": video_file_path,
                "error": f"处理异常: {str(e)}"
            })
            
            # 在出现异常后也添加延迟
            delay = random.uniform(10, 20)
            print(f"异常后等待 {delay:.1f} 秒继续处理...")
            time.sleep(delay)
        
        # 定期输出进度信息
        if i % 3 == 0 or i == len(video_files):
            print_progress_stats(i, video_files, successful_analyses, partial_analyses, failed_analyses)
    
    # 打印最终统计结果
    print_final_stats(video_files, successful_analyses, partial_analyses, failed_analyses)
    
    return {
        "total_count": len(video_files),
        "success_count": len(successful_analyses),
        "partial_count": len(partial_analyses),
        "failed_count": len(failed_analyses),
        "successful_analyses": successful_analyses,
        "partial_analyses": partial_analyses,
        "failed_analyses": failed_analyses,
        "analysis_results": analysis_results
    }

def handle_existing_report(video_file_path, material_name, output_file, error_output_file, 
                          successful_analyses, partial_analyses, analysis_results):
    """处理已存在的报告文件"""
    # 确保输出目录存在
    output_dir = os.path.dirname(output_file)
    os.makedirs(output_dir, exist_ok=True)
    
    # 检查报告是否已存在于指定的输出目录
    if os.path.exists(output_file):
        print(f"分析报告已存在，跳过分析: {output_file}")
        # 加载已存在的报告
        try:
            with open(output_file, 'r', encoding='utf-8') as f:
                existing_result = json.load(f)
            successful_analyses.append({
                "video_file": video_file_path,
                "material_name": material_name,
                "output_file": output_file,
                "analysis_result": existing_result
            })
            analysis_results.append(existing_result)
            return True
        except Exception as e:
            print(f"加载已存在报告失败，将重新分析: {e}")
    
    # 检查是否存在错误报告
    if os.path.exists(error_output_file):
        print(f"错误报告已存在，跳过分析: {error_output_file}")
        try:
            with open(error_output_file, 'r', encoding='utf-8') as f:
                existing_error_result = json.load(f)
            partial_analyses.append({
                "video_file": video_file_path,
                "material_name": material_name,
                "output_file": error_output_file,
                "analysis_result": existing_error_result,
                "error": existing_error_result.get("error", "未知错误")
            })
            # 仍然添加到分析结果中，因为可能包含部分数据
            analysis_results.append(existing_error_result)
            return True
        except Exception as e:
            print(f"加载已存在错误报告失败，将重新分析: {e}")
    
    return False

def handle_analysis_result(analysis_result, video_file_path, material_name, output_dir,
                          successful_analyses, partial_analyses, failed_analyses, analysis_results):
    """处理分析结果，根据结果类型分类保存"""
    # 确保输出目录存在
    os.makedirs(output_dir, exist_ok=True)
    
    # 获取保存的文件路径（如果在analyze_material_by_video_path中已保存）
    saved_file = analysis_result.get("saved_to")
    if not saved_file:
        # 手动保存结果到指定目录
        saved_file = save_analysis_report(analysis_result, material_name, output_dir)
        
    if "error" in analysis_result:
        # 检查是否有部分数据
        has_partial_data = any(key not in ["error", "raw_response", "saved_to"] for key in analysis_result.keys())
            
        if has_partial_data:
            print(f"⚠️ 分析部分成功(包含部分数据但有错误): {analysis_result['error']}")
            print(f"  部分数据已保存到: {saved_file}")
            
            partial_analyses.append({
                "video_file": video_file_path,
                "material_name": material_name,
                "output_file": saved_file,
                "analysis_result": analysis_result,
                "error": analysis_result.get("error", "未知错误")
            })
            analysis_results.append(analysis_result)
        else:
            print(f"❌ 分析失败: {analysis_result['error']}")
            print(f"  错误信息已保存到: {saved_file}")
            
            failed_analyses.append({
                "video_file": video_file_path,
                "error": analysis_result.get("error", "未知错误"),
                "output_file": saved_file
            })
    else:
        print(f"✅ 分析成功: {saved_file}")
        
        successful_analyses.append({
            "video_file": video_file_path,
            "material_name": material_name,
            "output_file": saved_file,
            "analysis_result": analysis_result
        })
        analysis_results.append(analysis_result)
                
def print_progress_stats(current_index, video_files, successful_analyses, partial_analyses, failed_analyses):
    """打印当前进度统计信息"""
    print(f"\n📊 当前进度统计:")
    print(f"   总数: {len(video_files)}")
    print(f"   已处理: {current_index}")
    print(f"   完全成功: {len(successful_analyses)}")
    print(f"   部分成功: {len(partial_analyses)}")
    print(f"   完全失败: {len(failed_analyses)}")
    print(f"   剩余: {len(video_files) - current_index}")
    
def print_final_stats(video_files, successful_analyses, partial_analyses, failed_analyses):
    """打印最终统计结果"""
    total_count = len(video_files)
    success_count = len(successful_analyses)
    partial_count = len(partial_analyses)
    failed_count = len(failed_analyses)
    
    print(f"\n{'='*50}")
    print(f"📋 批量分析完成")
    print(f"{'='*50}")
    print(f"总视频数: {total_count}")
    print(f"完全成功: {success_count} ✅")
    print(f"部分成功: {partial_count} ⚠️")
    print(f"完全失败: {failed_count} ❌")
    print(f"总成功率: {(success_count + partial_count)/total_count*100:.1f}%")
    print(f"完全成功率: {success_count/total_count*100:.1f}%")
    
    if failed_analyses:
        print(f"\n❌ 完全失败的视频:")
        for fail in failed_analyses:
            print(f"  - {os.path.basename(fail['video_file'])}: {fail['error']}")
    
    if partial_analyses:
        print(f"\n⚠️ 部分成功的视频:")
        for partial in partial_analyses:
            print(f"  - {os.path.basename(partial['video_file'])}: {partial['error']}")
    
    if successful_analyses:
        print(f"\n✅ 完全成功的视频:")
        for success in successful_analyses:
            print(f"  - {os.path.basename(success['video_file'])}")

def test_module(test_type="basic"):
    """
    测试模块功能
    
    Args:
        test_type: 测试类型，可以是  "single"(单视频测试), 
                  "batch"(批量分析测试), "json"(JSON处理测试)
    """
    # 根据测试类型执行不同的测试
    if test_type == "single":
        _test_single_video_analysis()
    elif test_type == "json":
        _test_json_processing()
    else:
        print(f"⚠️ 未知的测试类型: {test_type}")
        print("可用的测试类型:  single, batch, json")


def _test_single_video_analysis():
    """测试单个视频分析"""
    # 检查视频文件是否存在
    if not os.path.exists(VIDEO_FILE_PATH):
        print(f"✗ 视频文件不存在: {VIDEO_FILE_PATH}")
        return
    
    
    try:
        # 初始化Gemini客户端
        client = genai.Client(api_key=API_KEY)
        
        # 分析视频
        analyze_material_by_video_path(
            video_file_path=VIDEO_FILE_PATH,
            client=client
        )
        
    except Exception as e:
        print(f"✗ 测试过程中发生错误: {e}")
        traceback.print_exc()



def _test_json_processing():
    """测试JSON处理功能"""
    print("开始测试JSON格式修复功能...")
    
    # 测试JSON修复
    test_json_samples = [
        # 1. 有效JSON
        '{"name": "测试", "value": 123}',
        
        # 2. Markdown包裹的JSON
        '```json\n{"name": "测试", "value": 123}\n```',
        
        # 3. 有换行问题的JSON
        '{"name": "测试\n换行", "value": 123}',
        
        # 4. 缺少逗号的JSON
        '{"name": "测试"\n"value": 123}',
        
        # 5. 括号不平衡的JSON
        '{"name": "测试", "value": 123',
        
        # 6. 严重损坏的JSON
        'name: 测试, value= 123'
    ]
    
    print("\n测试样例结果:")
    for i, sample in enumerate(test_json_samples, 1):
        print(f"\n样例 {i}:")
        print(f"原始文本: {sample}")
        fixed = fix_json_format(sample)
        print(f"修复后: {fixed}")
        
        try:
            json.loads(fixed)
            print("✅ JSON解析成功")
        except json.JSONDecodeError as e:
            print(f"❌ JSON解析失败: {e}")
    
    print("\nJSON处理测试完成")

if __name__ == "__main__":
    import sys
    
    # 解析命令行参数
    test_type = "json"  # 默认测试类型
    
    if len(sys.argv) > 1:
        test_type = sys.argv[1].lower()
    
    if test_type == "material_ids":
        # 根据素材ID分析视频
        analyze_videos_by_material_ids()
    else:
        # 运行测试
        test_module(test_type) 