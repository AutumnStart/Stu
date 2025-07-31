#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import numpy as np
import matplotlib.pyplot as plt
from PIL import Image
import time
import json
import pandas as pd
import base64
import requests
from matplotlib.font_manager import FontProperties

# 配置Gemini API密钥和URL
API_KEY = "AIzaSyDxnQNBD0dtIKtZHpubgv_ZSw7AG_7tYCU"
API_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={API_KEY}"

class AudienceMismatchAnalysis:
    def __init__(self, impression_img_path, conversion_img_path, output_path='人群错配分析结果.png', threshold=40):
        """
        初始化人群错配分析类
        
        Args:
            impression_img_path: 曝光人群图片路径
            conversion_img_path: 转化人群图片路径
            output_path: 分析报告输出路径
            threshold: 错配判断阈值(百分比)
        """
        self.impression_img_path = impression_img_path
        self.conversion_img_path = conversion_img_path
        self.output_path = output_path
        self.threshold = threshold
        self.impression_data = None
        self.conversion_data = None
        self.mismatch_result = None
        # 验证Gemini API配置
        if not API_KEY or not API_URL:
            raise ValueError("必须提供有效的Gemini API密钥和URL")
    
    def get_mime_type(self, file_path):
        """根据文件扩展名获取正确的MIME类型"""
        ext = os.path.splitext(file_path)[1].lower()
        mime_types = {
            '.png': 'image/png',
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.bmp': 'image/bmp',
            '.gif': 'image/gif',
            '.webp': 'image/webp'
        }
        return mime_types.get(ext, 'image/jpeg')  # 默认使用jpeg
        
    def extract_data_from_image(self, img_path):
        """
        使用Gemini API从图片中智能提取人群分布数据
        
        Args:
            img_path: 图片路径
            
        Returns:
            dict: 人群类别和对应的数值
        """
        try:
            # 读取图片并转换为base64编码
            with Image.open(img_path) as img:
                # 将图片转换为RGB模式（如果不是）
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                
                # 保存到临时缓冲区
                import io
                buffer = io.BytesIO()
                img.save(buffer, format="JPEG")
                img_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
            
            # 定义提示词，指导模型提取结构化数据
            prompt = """
            你是一个专业的数据提取助手。请分析这张人群分布图，提取人群类别及其对应的数值。
            要求：
            1. 识别所有人群类别名称
            2. 提取每个类别的具体数值
            3. 忽略图表标题、坐标轴标签等非数据文本
            4. 以JSON格式返回，键为人群类别，值为对应的数值
            5. 如果无法识别，返回空JSON
            
            示例输出：{"年轻人": 35.2, "中年人": 42.1, "老年人": 22.7}
            """
            
            # 获取正确的MIME类型
            mime_type = self.get_mime_type(img_path)
            
            # 构建请求体
            request_body = {
                "contents": [
                    {
                        "parts": [
                            {"text": prompt},
                            {
                                "inlineData": {
                                    "mimeType": mime_type,
                                    "data": img_base64
                                }
                            }
                        ]
                    }
                ],
                "generationConfig": {
                    "responseMimeType": "application/json"
                }
            }
            
            # 发送请求到Gemini API
            max_retries = 3
            retry_delay = 2
            headers = {'Content-Type': 'application/json'}
            
            for attempt in range(max_retries):
                try:
                    response = requests.post(API_URL, headers=headers, json=request_body)
                    response.raise_for_status()  # 检查HTTP错误
                    
                    # 解析响应
                    response_data = response.json()
                    if 'candidates' in response_data and len(response_data['candidates']) > 0:
                        content = response_data['candidates'][0]['content']['parts'][0]['text'].strip()
                        
                        # 提取JSON部分
                        if '{' in content and '}' in content:
                            json_str = content[content.index('{'):content.rindex('}')+1]
                            data = json.loads(json_str)
                            print(f"成功从图片提取数据: {data}")
                            return data
                        else:
                            raise ValueError("无法从Gemini响应中提取JSON数据")
                    else:
                        raise ValueError("Gemini API返回空响应")
                        
                except Exception as e:
                    if attempt < max_retries - 1:
                        print(f"Gemini API请求失败，重试中({attempt+1}/{max_retries})...")
                        print(f"错误信息: {str(e)}")
                        time.sleep(retry_delay)
                        retry_delay *= 2  # 指数退避
                    else:
                        raise
                        
        except Exception as e:
            print(f"使用Gemini API提取图片数据出错: {img_path}")
            print(f"错误信息: {e}")
            raise
        

    
    def analyze(self):
        """
        分析曝光人群和转化人群的错配情况
        
        Returns:
            dict: 错配分析结果
        """
        # 提取数据
        self.impression_data = self.extract_data_from_image(self.impression_img_path)
        self.conversion_data = self.extract_data_from_image(self.conversion_img_path)
        
        return self.analyze_with_data(self.impression_data, self.conversion_data)
        
    def analyze_with_data(self, impression_data, conversion_data):
        """
        使用提供的曝光和转化数据进行错配分析
        
        Args:
            impression_data: 曝光人群数据字典
            conversion_data: 转化人群数据字典
            
        Returns:
            dict: 错配分析结果
        """
        self.impression_data = impression_data
        self.conversion_data = conversion_data
        
        # 计算各人群在曝光和转化中的占比
        total_impression = sum(self.impression_data.values())
        total_conversion = sum(self.conversion_data.values())
        
        impression_percentage = {k: v/total_impression*100 for k, v in self.impression_data.items()}
        conversion_percentage = {k: v/total_conversion*100 for k, v in self.conversion_data.items()}
        
        # 分析错配情况
        self.mismatch_result = {}
        for category in set(list(impression_percentage.keys()) + list(conversion_percentage.keys())):
            imp_pct = impression_percentage.get(category, 0)
            conv_pct = conversion_percentage.get(category, 0)
            
            # 计算差异
            diff = conv_pct - imp_pct
            diff_ratio = abs(diff / max(imp_pct, 0.1))  # 避免除以零
            
            # 判断是否错配
            is_mismatch = diff_ratio > 0.2  # 40%阈值，可调整
            
            self.mismatch_result[category] = {
                'impression_percentage': imp_pct,
                'conversion_percentage': conv_pct,
                'difference': diff,
                'difference_ratio': diff_ratio,
                'is_mismatch': is_mismatch,
                'suggestion': self._generate_suggestion(category, diff, is_mismatch)
            }
        
        return self.mismatch_result
    
    def _generate_suggestion(self, category, diff, is_mismatch):
        """
        根据错配情况生成优化建议
        """
        if not is_mismatch:
            return "人群匹配良好，无需调整"
        
        if diff > 0:  # 转化占比高于曝光占比
            return f"调整钩子策略：针对{category}人群，保留核心卖点，但修改前3秒场景/话术，增加对该人群的曝光，因为该人群转化效果好但曝光占比低"
        else:  # 曝光占比高于转化占比
            return f"保留钩子策略：针对{category}人群，考虑更换为更适合该人群的产品，因为当前产品对该人群吸引力强但转化效果差"
    
    def generate_report(self, output_path, mismatch_result=None):
        """
        生成分析报告并保存为图片
        
        Args:
            output_path: 输出图片路径
            mismatch_result: 可选，外部提供的错配分析结果
        """
        if mismatch_result is not None:
            self.mismatch_result = mismatch_result
        elif self.mismatch_result is None:
            self.analyze()
        
        # 创建数据表格
        data = []
        for category, result in self.mismatch_result.items():
            data.append([
                category,
                f"{result['impression_percentage']:.2f}%",
                f"{result['conversion_percentage']:.2f}%",
                f"{result['difference']:.2f}%",
                "是" if result['is_mismatch'] else "否",
                result['suggestion']
            ])
        
        # 创建DataFrame
        df = pd.DataFrame(data, columns=['人群类别', '曝光占比', '转化占比', '差异', '是否错配', '优化建议'])
        
        # 绘制图表
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 12))
        
        # 设置中文字体
        plt.rcParams['font.sans-serif'] = ['SimHei']
        plt.rcParams['axes.unicode_minus'] = False
        
        # 绘制柱状图
        categories = list(self.mismatch_result.keys())
        imp_pcts = [self.mismatch_result[c]['impression_percentage'] for c in categories]
        conv_pcts = [self.mismatch_result[c]['conversion_percentage'] for c in categories]
        
        x = np.arange(len(categories))
        width = 0.35
        
        ax1.bar(x - width/2, imp_pcts, width, label='曝光占比')
        ax1.bar(x + width/2, conv_pcts, width, label='转化占比')
        
        ax1.set_title('人群曝光与转化占比对比')
        ax1.set_xticks(x)
        ax1.set_xticklabels(categories)
        ax1.legend()
        
        # 绘制表格
        ax2.axis('tight')
        ax2.axis('off')
        table = ax2.table(cellText=data,
                          colLabels=df.columns,
                          loc='center',
                          cellLoc='center')
        
        # 调整表格样式以确保文字完整显示
        table.auto_set_font_size(False)
        table.set_fontsize(7)  # 减小字体大小
        table.scale(1, 2)  # 增加行高
        
        # 自动设置列宽
        for i in range(len(df.columns)):
            table.auto_set_column_width(i)
        
        # 特别调整'优化建议'列的宽度
        suggestion_col_index = df.columns.get_loc('优化建议')
        table.auto_set_column_width(suggestion_col_index)
        
        plt.tight_layout()
        
        # 保存图表
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        
        return output_path
    
    def generate_optimization_instructions(self, output_file, mismatch_result=None):
        """
        生成具体的优化指令文本文件
        
        Args:
            output_file: 输出文件路径
            mismatch_result: 可选，外部提供的错配分析结果
        """
        if mismatch_result is not None:
            self.mismatch_result = mismatch_result
        elif self.mismatch_result is None:
            self.analyze()
        
        # 分类存储不同类型的优化建议
        adjust_strategy = []
        keep_strategy = []
        no_action = []
        
        for category, result in self.mismatch_result.items():
            if not result['is_mismatch']:
                no_action.append(f"• {category}：人群匹配良好，无需调整")
            elif result['difference'] > 0:
                adjust_strategy.append(f"• {category}：调整钩子策略 - 保留核心卖点，修改前3秒场景/话术，增加对该人群的曝光（当前曝光占比{result['impression_percentage']:.2f}%，转化占比{result['conversion_percentage']:.2f}%）")
            else:
                keep_strategy.append(f"• {category}：保留钩子策略 - 考虑更换为更适合该人群的产品（当前曝光占比{result['impression_percentage']:.2f}%，转化占比{result['conversion_percentage']:.2f}%）")
        
        # 生成优化指令文本
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write("# 人群错配分析 - 优化指令\n\n")
            
            f.write("## 数据采集与对齐\n")
            f.write("- 曝光人群画像数据来源：八大人群分布人数整体展现次数\n")
            f.write("- 转化人群画像数据来源：八大人群分布人数整体成交金额\n\n")
            
            f.write("## 智能诊断与识别\n")
            f.write(f"- 共分析了{len(self.mismatch_result)}个人群类别\n")
            f.write(f"- 发现{len(adjust_strategy) + len(keep_strategy)}个人群存在错配问题\n\n")
            
            f.write("## 具体化优化指令\n")
            
            if adjust_strategy:
                f.write("\n### 需要调整钩子策略的人群\n")
                f.write("这些人群转化效果好但曝光占比低，建议保留核心卖点，修改前3秒场景/话术，增加对该人群的曝光：\n\n")
                f.write("\n".join(adjust_strategy))
                f.write("\n")
            
            if keep_strategy:
                f.write("\n### 需要保留钩子策略的人群\n")
                f.write("这些人群曝光占比高但转化效果差，建议考虑更换为更适合该人群的产品：\n\n")
                f.write("\n".join(keep_strategy))
                f.write("\n")
            
            if no_action:
                f.write("\n### 无需调整的人群\n")
                f.write("这些人群曝光与转化匹配良好，无需特别调整：\n\n")
                f.write("\n".join(no_action))
                f.write("\n")
        
        return output_file

def main(material_folder=None):
    screenshots_dir = r"./screenshots"
    
    # 如果指定了材料文件夹，则只分析该文件夹
    if material_folder:
        material_folders = [material_folder]
    else:
        # 否则分析所有除errors外的文件夹
        material_folders = []
        for item in os.listdir(screenshots_dir):
            item_path = os.path.join(screenshots_dir, item)
            if os.path.isdir(item_path) and item != 'errors':
                material_folders.append(item)
    
    # 遍历所有材料文件夹
    for folder in material_folders:
        base_path = os.path.join(screenshots_dir, folder)
        print(f"\n正在分析文件夹: {base_path}")
        
        # 查找八大人群分布人数整体展现次数和成交金额的图片
        impression_files = [f for f in os.listdir(base_path) if "八大人群分布人数整体展现次数" in f]
        conversion_files = [f for f in os.listdir(base_path) if "八大人群分布人数整体成交金额" in f]
        
        if not impression_files:
            print(f"错误: 在文件夹 {base_path} 中未找到八大人群分布人数整体展现次数的图片")
            continue
        if not conversion_files:
            print(f"错误: 在文件夹 {base_path} 中未找到八大人群分布人数整体成交金额的图片")
            continue
        
        # 取第一个匹配的文件
        impression_img_path = os.path.join(base_path, impression_files[0])
        conversion_img_path = os.path.join(base_path, conversion_files[0])
        
        # 设置输出路径为当前材料文件夹
        output_img_path = os.path.join(base_path, "人群错配分析结果.png")
        output_instructions_path = os.path.join(base_path, "人群错配分析优化指令.md")
        
        print(f"曝光图片路径: {impression_img_path}")
        print(f"转化图片路径: {conversion_img_path}")
        
        # 检查文件是否存在
        if not os.path.exists(impression_img_path):
            print(f"错误: 曝光图片不存在: {impression_img_path}")
            continue
        if not os.path.exists(conversion_img_path):
            print(f"错误: 转化图片不存在: {conversion_img_path}")
            continue
            
        # 创建分析器
        analyzer = AudienceMismatchAnalysis(impression_img_path, conversion_img_path)

        impression_data = analyzer.extract_data_from_image(impression_img_path)
        conversion_data = analyzer.extract_data_from_image(conversion_img_path)
        mismatch_result = analyzer.analyze_with_data(impression_data, conversion_data)
        
        # 使用分析结果生成报告
        report_path = analyzer.generate_report(output_img_path, mismatch_result)
        instructions_path = analyzer.generate_optimization_instructions(output_instructions_path, mismatch_result)
        
        print(f"分析报告图表已生成: {report_path}")
        print(f"优化指令已生成: {instructions_path}")
        

def batch_analyze():
    """
    批量分析screenshots目录下除errors外的所有文件夹
    """
    main()
        

if __name__ == "__main__":
    batch_analyze()