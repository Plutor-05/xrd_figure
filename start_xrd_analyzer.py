"""
XRD峰匹配分析程序启动器
简化版本，便于用户快速启动程序
"""

import sys
import os
import tkinter as tk
from tkinter import messagebox
import logging

# 添加当前目录到Python路径
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('xrd_analyzer.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)

def check_dependencies():
    """检查必要的依赖包"""
    required_packages = {
        'pandas': 'pandas',
        'matplotlib': 'matplotlib', 
        'scipy': 'scipy',
        'numpy': 'numpy'
    }
    
    missing_packages = []
    
    for package_name, import_name in required_packages.items():
        try:
            __import__(import_name)
        except ImportError:
            missing_packages.append(package_name)
    
    if missing_packages:
        error_msg = f"缺少必要的依赖包: {', '.join(missing_packages)}\n\n"
        error_msg += "请使用以下命令安装:\n"
        error_msg += f"pip install {' '.join(missing_packages)}"
        
        messagebox.showerror("依赖包缺失", error_msg)
        return False
    
    return True

def main():
    """主函数"""
    try:
        # 检查依赖包
        if not check_dependencies():
            return
        
        # 导入主程序
        from xrd_analyzer_gui import XRDAnalyzerGUI
        
        # 创建主窗口
        root = tk.Tk()
        
        # 设置窗口属性
        root.title("XRD峰匹配分析程序 v3.0")
        root.geometry("1400x900")
        root.minsize(1200, 800)
        
        # 设置窗口居中
        root.update_idletasks()
        x = (root.winfo_screenwidth() // 2) - (1400 // 2)
        y = (root.winfo_screenheight() // 2) - (900 // 2)
        root.geometry(f"1400x900+{x}+{y}")
        
        # 创建应用实例
        app = XRDAnalyzerGUI(root)
        
        # 启动程序
        root.mainloop()
        
    except ImportError as e:
        error_msg = f"导入模块失败: {str(e)}\n\n请确保所有必要文件都在同一目录下。"
        messagebox.showerror("导入错误", error_msg)
        
    except Exception as e:
        error_msg = f"程序启动失败: {str(e)}\n\n请检查程序完整性或联系技术支持。"
        messagebox.showerror("启动失败", error_msg)
        logging.error(f"程序启动失败: {e}", exc_info=True)

if __name__ == "__main__":
    main()
