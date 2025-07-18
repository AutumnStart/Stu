import os
import sys
from google import genai
from agent10 import analyze_videos_by_material_ids, API_KEY

def analyze_by_material_ids():
    """
    运行agent10的根据素材ID分析视频功能
    """
    print("开始根据素材ID分析视频...")
    
    # 直接调用analyze_videos_by_material_ids函数
    analyze_videos_by_material_ids()
    
    print("根据素材ID分析视频完成!")

if __name__ == "__main__":
    analyze_by_material_ids() 