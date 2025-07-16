#!/usr/bin/env python3
import os
import base64
import requests
import json
import re
import time
import random
from collections import defaultdict
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Gemini 2.0 Flash API密钥
API_KEY = "AIzaSyDxnQNBD0dtIKtZHpubgv_ZSw7AG_7tYCU"
API_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={API_KEY}"

# 代理设置（默认不使用代理）
PROXIES = None
# 如果需要使用代理，取消下面注释并填写代理地址
# PROXIES = {
#     "http": "http://your-proxy:port",
#     "https": "https://your-proxy:port"
# }

# 重试设置
MAX_RETRIES = 3
RETRY_BACKOFF = 2  # 指数退避因子
MIN_DELAY = 1      # 请求之间的最小延迟秒数
MAX_DELAY = 5      # 请求之间的最大延迟秒数

def get_material_folders(root_dir):
    """获取所有素材文件夹"""
    material_folders = []
    try:
        for item in os.listdir(root_dir):
            item_path = os.path.join(root_dir, item)
            if os.path.isdir(item_path) and item.startswith("Material_"):
                material_folders.append(item_path)
    except Exception as e:
        print(f"读取素材文件夹出错: {e}")
    return material_folders

def get_image_paths(folder):
    """获取文件夹中的所有图片文件"""
    image_paths = []
    try:
        for item in os.listdir(folder):
            if item.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.gif')):
                image_paths.append(os.path.join(folder, item))
    except Exception as e:
        print(f"读取图片文件出错: {e}")
    return image_paths

def extract_material_id(folder_path):
    """从文件夹名称中提取素材ID"""
    folder_name = os.path.basename(folder_path)
    if folder_name.startswith("Material_"):
        return folder_name.split("_", 1)[1]
    return folder_name

def create_requests_session():
    """创建一个带有重试机制的requests会话"""
    session = requests.Session()
    
    # 配置重试策略
    retry_strategy = Retry(
        total=MAX_RETRIES,
        backoff_factor=RETRY_BACKOFF,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["POST"]
    )
    
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    
    # 设置代理（如果有）
    if PROXIES:
        session.proxies.update(PROXIES)
    
    return session

def analyze_image(image_path, session):
    """调用Gemini API分析图片，获取主峰值和次峰值坐标"""
    # 读取并编码图片
    try:
        with open(image_path, 'rb') as f:
            data = f.read()
        b64 = base64.b64encode(data).decode('utf-8')
    except Exception as e:
        print(f"读取图片文件出错: {image_path}, {e}")
        return None, None, None
    
    # 构造提示语
    prompt = (
        "请分析以下图片中的曲线，找出主峰值和次级快速下降的相对峰值。"
        "注意：两个峰值均不要在图片横坐标末端区域的峰值。"
        "请以图片中的时间(x轴)和点击次数(y轴)给出峰值坐标，而不是像素值。"
        "返回格式为JSON: {\"main_peak\":{\"x\":时间值,\"y\":点击次数},\"secondary_peak\":{\"x\":时间值,\"y\":点击次数}}"
    )
    
    # 构造API请求
    payload = {
        "contents": [{
            "parts": [
                {"text": prompt},
                {"inline_data": {
                    "mime_type": "image/jpeg",
                    "data": b64
                }}
            ]
        }]
    }
    
    headers = {'Content-Type': 'application/json'}
    
    # 添加重试逻辑
    for attempt in range(MAX_RETRIES + 1):
        try:
            resp = session.post(API_URL, headers=headers, json=payload, timeout=120)
            resp.raise_for_status()
            result = resp.json()
            
            # 从返回结果中提取文本
            text = ''
            if 'candidates' in result and result['candidates']:
                cand = result['candidates'][0]
                if 'content' in cand and 'parts' in cand['content']:
                    for part in cand['content']['parts']:
                        if 'text' in part:
                            text += part['text']
            
            # 尝试从文本中提取JSON数据
            json_match = re.search(r'({[\s\S]*})', text)
            if json_match:
                try:
                    peaks_data = json.loads(json_match.group(1))
                    return peaks_data.get('main_peak'), peaks_data.get('secondary_peak'), None
                except json.JSONDecodeError as e:
                    return None, None, f"JSON解析失败: {e}, 原始文本: {text}"
            else:
                # 如果没有成功提取到JSON，尝试直接提取坐标对
                coords = re.findall(r'[（(]([0-9]+(?:\.[0-9]+)?)\s*[，,]\s*([0-9]+(?:\.[0-9]+)?)[)）]', text)
                
                if len(coords) >= 1:
                    main_peak = {"x": float(coords[0][0]), "y": float(coords[0][1])}
                else:
                    main_peak = None
                    
                if len(coords) >= 2:
                    secondary_peak = {"x": float(coords[1][0]), "y": float(coords[1][1])}
                else:
                    secondary_peak = None
                    
                return main_peak, secondary_peak, None
                
        except requests.exceptions.RequestException as e:
            error_msg = f"第{attempt+1}次API调用失败: {e}"
            print(error_msg)
            
            if attempt < MAX_RETRIES:
                # 指数退避延迟
                sleep_time = (RETRY_BACKOFF ** attempt) + random.uniform(MIN_DELAY, MAX_DELAY)
                print(f"等待 {sleep_time:.2f} 秒后重试...")
                time.sleep(sleep_time)
            else:
                return None, None, f"API调用失败，已达最大重试次数: {e}"
    
    return None, None, "未知错误，API调用失败"

def load_material_ids(json_path):
    """从素材数据JSON文件中加载素材ID"""
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # 提取所有素材ID
        material_ids = set()
        for item in data:
            if '素材ID' in item and item['素材ID']:
                material_ids.add(str(item['素材ID']))
        
        print(f"从素材数据中加载了 {len(material_ids)} 个素材ID")
        return material_ids
    except Exception as e:
        print(f"加载素材ID时出错: {e}")
        return set()

def main():
    # 确定路径
    root_dir = os.path.dirname(os.path.abspath(__file__))

    while not os.path.exists(os.path.join(root_dir, 'storage')) and os.path.dirname(root_dir) != root_dir:
        root_dir = os.path.dirname(root_dir)
    # 如果没找到包含storage的目录，尝试直接使用工作空间根目录
    # 获取脚本所在目录
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    if not os.path.exists(os.path.join(root_dir, 'storage')):
        root_dir = os.path.abspath(os.path.join(script_dir, '..'))
    
    # 设置数据目录和图片目录
    data_dir = os.path.join(root_dir, 'data')
    image_root = os.path.join(root_dir, 'screenshots')
    
    # 设置输出目录为素材数据分析目录
    output_dir = os.path.join(root_dir, 'json', '素材数据分析')
    os.makedirs(output_dir, exist_ok=True)
    
    # 定义输出文件路径
    output_file = os.path.join(output_dir, 'BYDHG_peaks_analysis.json')
    
    # 检查是否已存在分析结果文件
    if os.path.exists(output_file):
        print(f"分析结果文件已存在: {output_file}")
        print("跳过分析过程...")
        return
    
    # 从素材数据JSON文件加载素材ID
    material_json_path = os.path.join(output_dir, '素材数据.json')
    if not os.path.exists(material_json_path):
        material_json_path = os.path.join(data_dir, '素材数据.json')
    
    if not os.path.exists(material_json_path):
        print(f"无法找到素材数据文件: {material_json_path}")
        print("将分析所有素材文件夹...")
        target_material_ids = None
    else:
        target_material_ids = load_material_ids(material_json_path)
        if not target_material_ids:
            print("未能从素材数据中加载到有效的素材ID，将分析所有素材文件夹...")
            target_material_ids = None
    
    # 创建会话
    session = create_requests_session()
    
    # 获取所有素材文件夹
    all_material_folders = get_material_folders(image_root)
    
    # 如果有目标素材ID，只分析这些ID对应的文件夹
    if target_material_ids:
        material_folders = []
        for folder in all_material_folders:
            material_id = extract_material_id(folder)
            if material_id in target_material_ids:
                material_folders.append(folder)
        print(f"找到 {len(all_material_folders)} 个素材文件夹，将只分析其中 {len(material_folders)} 个目标素材文件夹")
    else:
        material_folders = all_material_folders
        print(f"找到 {len(material_folders)} 个素材文件夹，将分析所有文件夹")
    
    # 创建临时文件夹
    temp_dir = os.path.join(output_dir, 'temp')
    os.makedirs(temp_dir, exist_ok=True)
    
    # 用于存储所有数据的字典
    all_data = {}
    
    # 分析每个素材文件夹
    for folder in material_folders:
        material_id = extract_material_id(folder)
        image_paths = get_image_paths(folder)
        
        print(f"处理素材 {material_id}，包含 {len(image_paths)} 张图片")
        
        # 存储当前素材的数据
        material_data = {
            "material_id": material_id,
            "images": {}
        }
        
        # 分析每张图片
        for img_path in image_paths:
            img_name = os.path.basename(img_path)
            print(f"  分析图片: {img_name}")
            
            main_peak, secondary_peak, error = analyze_image(img_path, session)
            
            if error:
                print(f"  分析失败: {error}")
                
            material_data["images"][img_name] = {
                "main_peak": main_peak,
                "secondary_peak": secondary_peak,
                "error": error
            }
            
            print(f"  分析结果: 主峰值={main_peak}, 次峰值={secondary_peak}")
            
            # 添加请求之间的随机延迟，避免API限流
            delay = random.uniform(MIN_DELAY, MAX_DELAY)
            print(f"  等待 {delay:.2f} 秒后继续...")
            time.sleep(delay)
            
        # 将当前素材数据添加到总数据中
        all_data[material_id] = material_data
        
        # 每处理完一个文件夹就保存一次数据，防止中途中断丢失所有数据
        temp_output_file = os.path.join(temp_dir, f'BYDHG_peaks_analysis_temp_{material_id}.json')
        with open(temp_output_file, 'w', encoding='utf-8') as f:
            json.dump(all_data, f, ensure_ascii=False, indent=2)
        print(f"临时数据已保存到 {temp_output_file}")
    
    # 保存所有数据到JSON文件
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(all_data, f, ensure_ascii=False, indent=2)
        
    print(f"分析完成，结果已保存到 {output_file}")
    
    # 清理临时文件
    for material_id in all_data:
        temp_file = os.path.join(temp_dir, f'BYDHG_peaks_analysis_temp_{material_id}.json')
        if os.path.exists(temp_file):
            try:
                os.remove(temp_file)
            except Exception as e:
                print(f"清理临时文件失败: {temp_file}, {e}")

if __name__ == '__main__':
    main() 