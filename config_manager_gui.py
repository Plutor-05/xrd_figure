"""
配置管理器 - 用于保存和加载XRD分析程序的设置
"""

import json
import os
import tkinter as tk
from tkinter import messagebox

class ConfigManager:
    """配置管理器类"""
    
    def __init__(self, config_file="xrd_config.json"):
        self.config_file = config_file
        self.default_config = {
            # 峰检测参数
            'peak_height': 100,
            'peak_distance': 15,
            'peak_prominence': 50,
            'peak_width': 2,
            'match_tolerance': 0.2,
            
            # 显示参数
            'figure_width': 22,
            'figure_height': 13,
            'line_width': 1.2,
            'marker_size': 10,
            'font_size': 12,
            'title_size': 18,
            
            # 颜色设置
            'exp_data_color': 'black',
            'unmatched_color': 'red',
            'grid_alpha': 0.4,
            'legend_alpha': 0.9,
            
            # 数据处理参数
            'intensity_threshold': 0,
            'angle_min': 10,
            'angle_max': 70,
            'smooth_window': 1,
            
            # 输出设置
            'save_dpi': 300,
            'auto_save': True,
            'show_statistics': True,
            'show_unmatched': True
        }
    
    def load_config(self):
        """加载配置"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    # 合并默认配置和加载的配置
                    merged_config = self.default_config.copy()
                    merged_config.update(config)
                    return merged_config
            else:
                return self.default_config.copy()
        except Exception as e:
            print(f"加载配置失败: {e}")
            return self.default_config.copy()
    
    def save_config(self, config):
        """保存配置"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"保存配置失败: {e}")
            return False
    
    def reset_to_default(self):
        """重置为默认配置"""
        return self.default_config.copy()
    
    def validate_config(self, config):
        """验证配置的有效性"""
        errors = []
        
        # 验证数值范围
        validations = [
            ('peak_height', 1, 10000, "峰高阈值应在1-10000之间"),
            ('peak_distance', 1, 200, "峰间距离应在1-200之间"),
            ('peak_prominence', 1, 5000, "峰突出度应在1-5000之间"),
            ('peak_width', 0.1, 100, "峰宽度应在0.1-100之间"),
            ('match_tolerance', 0.01, 5.0, "匹配容差应在0.01-5.0之间"),
            ('figure_width', 4, 30, "图形宽度应在4-30之间"),
            ('figure_height', 3, 20, "图形高度应在3-20之间"),
            ('line_width', 0.1, 5.0, "线条宽度应在0.1-5.0之间"),
            ('marker_size', 1, 50, "标记大小应在1-50之间"),
            ('font_size', 6, 30, "字体大小应在6-30之间"),
            ('title_size', 8, 40, "标题大小应在8-40之间"),
            ('grid_alpha', 0.0, 1.0, "网格透明度应在0.0-1.0之间"),
            ('legend_alpha', 0.0, 1.0, "图例透明度应在0.0-1.0之间"),
            ('intensity_threshold', 0, 100000, "强度阈值应在0-100000之间"),
            ('angle_min', 0, 90, "最小角度应在0-90之间"),
            ('angle_max', 10, 180, "最大角度应在10-180之间"),
            ('smooth_window', 1, 50, "平滑窗口应在1-50之间"),
            ('save_dpi', 50, 2400, "保存DPI应在50-2400之间"),
        ]
        
        for key, min_val, max_val, message in validations:
            if key in config:
                value = config[key]
                if not isinstance(value, (int, float)) or value < min_val or value > max_val:
                    errors.append(message)
        
        # 验证角度范围的逻辑关系
        if config.get('angle_min', 0) >= config.get('angle_max', 180):
            errors.append("最小角度应小于最大角度")
        
        # 验证颜色设置
        valid_colors = ['black', 'blue', 'red', 'green', 'orange', 'purple', 'brown', 'pink', 'gray', 'cyan', 'magenta']
        if config.get('exp_data_color') not in valid_colors:
            errors.append("实验数据颜色设置无效")
        if config.get('unmatched_color') not in valid_colors:
            errors.append("未匹配峰颜色设置无效")
        
        return errors

# 示例用法
if __name__ == "__main__":
    manager = ConfigManager()
    
    # 加载配置
    config = manager.load_config()
    print("当前配置:")
    for key, value in config.items():
        print(f"  {key}: {value}")
    
    # 验证配置
    errors = manager.validate_config(config)
    if errors:
        print("配置验证错误:")
        for error in errors:
            print(f"  - {error}")
    else:
        print("配置验证通过")
