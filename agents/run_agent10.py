import os
import sys
from google import genai
from agent10 import batch_analyze_videos, BATCH_VIDEO_DIR, API_KEY

def analyze_batch_videos():
    """
    运行agent10的批量视频分析功能
    """
    print("开始批量分析视频...")
    
    # 初始化Gemini客户端
    try:
        client = genai.Client(api_key=API_KEY)
        print("Gemini客户端初始化成功")
    except Exception as e:
        print(f"Gemini客户端初始化失败: {e}")
        return
    
    # 检查视频目录是否存在
    if not os.path.exists(BATCH_VIDEO_DIR):
        print(f"错误: 视频目录不存在: {BATCH_VIDEO_DIR}")
        return
    
    # 检查目录中是否有视频文件
    video_files = [f for f in os.listdir(BATCH_VIDEO_DIR) 
                  if f.lower().endswith(('.mp4', '.avi', '.mov', '.mkv', '.wmv'))]
    
    if not video_files:
        print(f"错误: 视频目录中没有视频文件: {BATCH_VIDEO_DIR}")
        return
    
    print(f"找到 {len(video_files)} 个视频文件")
    
    # 运行批量分析
    results = batch_analyze_videos(BATCH_VIDEO_DIR, client)
    
    print("批量分析完成!")
    return results

if __name__ == "__main__":
    analyze_batch_videos() 