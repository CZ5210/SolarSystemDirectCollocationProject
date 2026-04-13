import sys
import os
import shutil
import queue
from Param import OUTPUT_CONFIG

# 自定义stdout重定向类
class TextRedirector:
    def __init__(self, text_widget, queue):
        self.text_widget = text_widget
        self.queue = queue
        self.old_stdout = sys.stdout
    
    def write(self, string):
        self.queue.put(string)
    
    def flush(self):
        pass
    
    def __enter__(self):
        sys.stdout = self
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        sys.stdout = self.old_stdout

def clean_output_directory():
    """清理输出目录"""
    try:
        output_dir = OUTPUT_CONFIG["directory"]
        if os.path.exists(output_dir):
            # 移除目录及其所有内容
            shutil.rmtree(output_dir)
            print(f"已清理输出目录: {output_dir}")
        # 重新创建目录结构
        os.makedirs(output_dir, exist_ok=True)
        porkchop_dir = OUTPUT_CONFIG["porkchop_directory"]
        os.makedirs(porkchop_dir, exist_ok=True)
        print(f"已创建输出目录结构")
    except Exception as e:
        print(f"清理输出目录时出错: {e}")
