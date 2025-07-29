"""
配置文件管理模块
负责加载和管理程序配置参数
"""

import configparser
from pathlib import Path


class ConfigManager:
    """配置文件管理器"""
    
    def __init__(self, config_file='config.ini'):
        self.config_file = Path(config_file)
        self.config = configparser.ConfigParser()
        self.load_config()
    
    def load_config(self):
        """加载配置文件"""
        if self.config_file.exists():
            try:
                self.config.read(self.config_file, encoding='utf-8')
                print(f"已加载配置文件: {self.config_file}")
            except Exception as e:
                print(f"读取配置文件失败: {e}，使用默认配置")
                self.load_default_config()
        else:
            print("未找到配置文件，使用默认配置")
            self.load_default_config()
    
    def load_default_config(self):
        """加载默认配置"""
        self.config.read_string('''
[峰值检测参数]
angle_tolerance = 0.5
min_intensity_ratio = 0.05
peak_detection_distance = 10

[标注样式]
annotation_fontsize = 8
annotation_offset_y = 50
annotation_colors = red,blue,green,orange,purple,brown,pink

[图形设置]
figure_width = 12
figure_height = 7
display_dpi = 100
save_figure = True
save_filename = xrd_pattern_annotated.png
save_format = png
save_dpi = 300

[数据线条]
line_colors = #6E7DDE,#FF5733,#33FF57,#3357FF,#FF33A1,#A133FF,#33FFA1
line_width = 1.0
line_alpha = 1.0

[坐标轴]
show_x_ticks = True
show_y_ticks = True
tick_fontsize = 12
axis_label_fontsize = 14

[图例]
show_legend = True
legend_location = upper right
legend_fontsize = 10

[网格]
show_grid = False
grid_alpha = 0.5
grid_color = gray
        ''')
    
    def get_float(self, section, key, fallback=0.0):
        """获取浮点数配置"""
        try:
            return self.config.getfloat(section, key)
        except:
            return fallback
    
    def get_int(self, section, key, fallback=0):
        """获取整数配置"""
        try:
            return self.config.getint(section, key)
        except:
            return fallback
    
    def get_bool(self, section, key, fallback=False):
        """获取布尔配置"""
        try:
            return self.config.getboolean(section, key)
        except:
            return fallback
    
    def get_string(self, section, key, fallback=''):
        """获取字符串配置"""
        try:
            return self.config.get(section, key)
        except:
            return fallback
    
    def get_list(self, section, key, fallback=None):
        """获取列表配置"""
        if fallback is None:
            fallback = []
        try:
            value = self.config.get(section, key)
            return [item.strip() for item in value.split(',')]
        except:
            return fallback
    
    def get_current_font(self):
        """获取当前使用的字体"""
        return self.get_string('字体设置', 'current_font', 'Microsoft YaHei')
    
    def get_current_symbols(self):
        """获取当前使用的符号列表"""
        symbols_str = self.get_string('符号设置', 'current_symbols', '●,■,▲,◆')
        return [s.strip() for s in symbols_str.split(',')]
    
    def get_fallback_symbol(self):
        """获取备用符号"""
        return self.get_string('符号设置', 'fallback_symbol', '●')
    
    def print_current_config(self):
        """打印当前配置参数"""
        print("\n" + "="*50)
        print("当前配置参数")
        print("="*50)
        
        # 峰值检测参数
        print("📊 峰值检测参数:")
        print(f"  角度容差: ±{self.get_float('峰值检测参数', 'angle_tolerance', 0.5)}°")
        print(f"  最小强度比例: {self.get_float('峰值检测参数', 'min_intensity_ratio', 0.05)*100:.1f}%")
        print(f"  峰间距: {self.get_int('峰值检测参数', 'peak_detection_distance', 10)} 点")
        
        # 图形设置
        print("\n🎨 图形设置:")
        print(f"  图形尺寸: {self.get_int('图形设置', 'figure_width', 12)} x {self.get_int('图形设置', 'figure_height', 7)} 英寸")
        print(f"  标注字体大小: {self.get_int('标注样式', 'annotation_fontsize', 8)}")
        print(f"  是否保存图片: {'是' if self.get_bool('图形设置', 'save_figure', True) else '否'}")
        
        # 字体设置
        print("\n🔤 字体设置:")
        current_font = self.get_current_font()
        print(f"  当前字体: {current_font}")
        
        # 符号设置
        print("\n🔣 符号设置:")
        current_symbols = self.get_current_symbols()
        print(f"  当前符号组: {' '.join(current_symbols)}")
        fallback_symbol = self.get_fallback_symbol()
        print(f"  备用符号: {fallback_symbol}")
        
        print("\n💡 提示: ")
        print("  - 可以编辑 config.ini 文件来修改这些参数")
        print("  - 当前使用兼容性最佳的几何符号组")
        print("="*50)
