import pandas as pd
import matplotlib.pyplot as plt
import matplotlib as mpl
from pathlib import Path
import numpy as np
import os
import re
import configparser
from scipy.signal import find_peaks
from typing import List, Tuple, Dict, Optional

def move_figure_to_center(fig):
    """将Matplotlib窗口移动到屏幕中央。"""
    try:
        manager = fig.canvas.manager
        window = manager.window
        backend = plt.get_backend().lower()

        if 'tk' in backend:
            window.update_idletasks()
            screen_width = window.winfo_screenwidth()
            screen_height = window.winfo_screenheight()
            width = window.winfo_width()
            height = window.winfo_height()
            x = (screen_width // 2) - (width // 2)
            y = (screen_height // 2) - (height // 2)
            window.geometry(f'{width}x{height}+{x}+{y}')

        elif 'qt' in backend:
            screen_geometry = window.screen().geometry()  # type: ignore
            geom = window.frameGeometry()
            geom.moveCenter(screen_geometry.center())
            window.move(geom.topLeft())

        elif 'wx' in backend:
            window.Center()

    except Exception:
        pass

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

class XRDAnalyzer:
    """XRD数据分析器，整合绘图、数据清洗和峰值标注功能"""
    
    def __init__(self, config_manager=None):
        # 配置管理器
        self.config = config_manager or ConfigManager()
        
        # 字体设置 - 确保支持扑克符号和中文
        try:
            # 设置支持中文和特殊符号的字体
            # 优先使用系统中可用的中文字体
            mpl.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei', 'SimSun', 'KaiTi', 'FangSong']
            mpl.rcParams['axes.unicode_minus'] = False
            
            # 测试扑克符号是否可用
            test_symbols = ['♠', '♥', '♦', '♣']
            print(f"扑克符号测试: {' '.join(test_symbols)}")
            
        except Exception as e:
            print(f"字体设置警告: {e}")
            # 使用默认字体设置
            mpl.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei']
            mpl.rcParams['axes.unicode_minus'] = False
        
        # 获取脚本目录
        self.script_dir = Path(__file__).resolve().parent
        
        # 从配置文件加载参数
        self.load_config_parameters()
        
    def load_config_parameters(self):
        """从配置文件加载参数"""
        # 峰值检测参数
        self.angle_tolerance = self.config.get_float('峰值检测参数', 'angle_tolerance', 0.5)
        self.min_intensity_ratio = self.config.get_float('峰值检测参数', 'min_intensity_ratio', 0.05)
        self.peak_detection_distance = self.config.get_int('峰值检测参数', 'peak_detection_distance', 10)
        
        # 标注样式
        self.annotation_fontsize = self.config.get_int('标注样式', 'annotation_fontsize', 8)
        self.annotation_offset_y = self.config.get_int('标注样式', 'annotation_offset_y', 50)
        self.annotation_colors = self.config.get_list('标注样式', 'annotation_colors', 
                                                     ['red', 'blue', 'green', 'orange', 'purple', 'brown', 'pink'])
        
        # 图形设置
        self.figure_width = self.config.get_int('图形设置', 'figure_width', 12)
        self.figure_height = self.config.get_int('图形设置', 'figure_height', 7)
        self.display_dpi = self.config.get_int('图形设置', 'display_dpi', 100)
        self.save_figure = self.config.get_bool('图形设置', 'save_figure', True)
        self.save_filename = self.config.get_string('图形设置', 'save_filename', 'xrd_pattern_annotated.png')
        self.save_format = self.config.get_string('图形设置', 'save_format', 'png')
        self.save_dpi = self.config.get_int('图形设置', 'save_dpi', 300)
        
        # 数据线条
        self.line_colors = self.config.get_list('数据线条', 'line_colors', 
                                               ['#6E7DDE', '#FF5733', '#33FF57', '#3357FF', '#FF33A1', '#A133FF', '#33FFA1'])
        self.line_width = self.config.get_float('数据线条', 'line_width', 1.0)
        self.line_alpha = self.config.get_float('数据线条', 'line_alpha', 1.0)
        
        # 坐标轴
        self.show_x_ticks = self.config.get_bool('坐标轴', 'show_x_ticks', True)
        self.show_y_ticks = self.config.get_bool('坐标轴', 'show_y_ticks', True)
        self.tick_fontsize = self.config.get_int('坐标轴', 'tick_fontsize', 12)
        self.axis_label_fontsize = self.config.get_int('坐标轴', 'axis_label_fontsize', 14)
        
        # 图例
        self.show_legend = self.config.get_bool('图例', 'show_legend', True)
        self.legend_location = self.config.get_string('图例', 'legend_location', 'upper right')
        self.legend_fontsize = self.config.get_int('图例', 'legend_fontsize', 10)
        
        # 网格
        self.show_grid = self.config.get_bool('网格', 'show_grid', False)
        self.grid_alpha = self.config.get_float('网格', 'grid_alpha', 0.5)
        self.grid_color = self.config.get_string('网格', 'grid_color', 'gray')
        
        # 固定参数
        self.setup_fixed_parameters()
        
    def setup_fixed_parameters(self):
        """设置固定参数"""
        # 标记设置
        self.marker_style = None
        self.marker_size = 4
        self.marker_edge_color = 'black'
        
        # 标题和标签 - 使用英文
        self.title_text = 'XRD Test Results with Phase Identification'
        self.title_fontsize = 18
        self.title_fontweight = 'bold'
        self.title_color = 'black'
        self.title_pad = 20
        
        self.xlabel_text = '2θ (degrees)'
        self.ylabel_text = 'Intensity (a.u.)'
        self.axis_label_color = 'black'
        self.axis_label_fontweight = 'normal'
        
        # 刻度设置
        self.tick_color = 'black'
        self.tick_direction = 'in'
        self.tick_length = 6
        self.tick_width = 1.0
        
        # 图例设置
        self.legend_frameon = True
        self.legend_fancybox = True
        self.legend_shadow = False
        self.legend_alpha = 0.9
        
        # 网格设置
        self.grid_linestyle = '--'
        self.grid_linewidth = 0.5
        
        # 坐标轴范围
        self.x_range = None
        self.y_range = None
        self.y_min = 0
        
        # 背景和边框
        self.figure_facecolor = "#eef3fa"
        self.plot_facecolor = "#FFFFFF"
        self.spine_color = 'black'
        self.spine_linewidth = 1.0
        self.hide_top_spine = True
        self.hide_right_spine = True
        
        self.save_bbox_inches = 'tight'
        
        # 峰值检测参数
        self.peak_detection_height = None
        self.peak_detection_prominence = None
        self.annotation_arrow_props = dict(arrowstyle='->', lw=1, alpha=0.7)
        
    def search_reference_files(self, search_path: Optional[str] = None) -> List[Path]:
        """搜索参考文件"""
        if search_path is None:
            search_dir = self.script_dir
        else:
            search_dir = Path(search_path)
            
        # 查找以reference_开头的txt文件
        reference_files = sorted(search_dir.glob('reference_*.txt'))
        return reference_files
    
    def load_reference_data(self, reference_files: List[Path]) -> Dict:
        """加载参考数据"""
        reference_data = {}
        
        for ref_file in reference_files:
            try:
                # 读取参考文件
                data = []
                phase_name = ""
                symbol = ""
                
                # 优先从文件名中提取相名称（保留原有命名方式）
                file_stem = ref_file.stem  # 去掉扩展名
                if file_stem.startswith('reference_'):
                    phase_name = file_stem[10:]  # 去掉'reference_'前缀
                
                with open(ref_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        if line.startswith('# Phase:') and not phase_name:
                            # 只有当文件名中没有相名称时才使用文件内容中的相名称
                            phase_name = line.split(':', 1)[1].strip()
                        elif line.startswith('# Symbol:'):
                            symbol = line.split(':', 1)[1].strip()
                        elif line and not line.startswith('#'):
                            # 解析数据行：2-Theta,PhaseName,Symbol
                            parts = line.split(',')
                            if len(parts) >= 3:
                                try:
                                    two_theta = float(parts[0])
                                    data.append(two_theta)
                                except ValueError:
                                    continue
                
                if data and phase_name:
                    reference_data[phase_name] = {
                        'two_theta': data,
                        'symbol': symbol,
                        'file': ref_file
                    }
                    
            except Exception as e:
                print(f"加载参考文件 {ref_file} 时出错: {e}")
                
        return reference_data
    
    def get_files_to_plot(self, directory: Path) -> List[Path]:
        """扫描目录，让用户选择要绘制的文件"""
        data_files = sorted([f for f in directory.glob('*.txt') 
                           if not f.name.startswith('reference_')])
        
        if not data_files:
            print(f"错误：在目录 '{directory}' 中未找到任何实验数据文件。")
            return []

        print("找到以下实验数据文件:")
        for i, file in enumerate(data_files):
            print(f"  {i + 1}: {file.name}")

        while True:
            try:
                choice = input("请选择要绘制的文件编号（用逗号或空格分隔，或输入 'all' 选择全部）: ").strip().lower()
                if not choice:
                    continue
                if choice == 'all':
                    return data_files

                indices = [int(i) - 1 for i in choice.replace(',', ' ').split()]
                
                selected_files = []
                valid_selection = True
                for i in indices:
                    if 0 <= i < len(data_files):
                        selected_files.append(data_files[i])
                    else:
                        print(f"错误：编号 {i + 1} 无效。")
                        valid_selection = False
                        break
                
                if valid_selection:
                    return selected_files
            except ValueError:
                print("输入无效，请输入数字编号。")
    
    def select_reference_files(self, reference_files: List[Path]) -> List[Path]:
        """让用户选择参考文件"""
        if not reference_files:
            print("未找到任何参考文件。")
            return []
            
        print("\n找到以下参考文件:")
        for i, file in enumerate(reference_files):
            print(f"  {i + 1}: {file.name}")
        
        while True:
            try:
                choice = input("请选择要用于标注的参考文件编号（用逗号或空格分隔，或输入 'all' 选择全部，'none' 跳过标注）: ").strip().lower()
                if not choice:
                    continue
                if choice == 'all':
                    return reference_files
                if choice == 'none':
                    return []

                indices = [int(i) - 1 for i in choice.replace(',', ' ').split()]
                
                selected_files = []
                valid_selection = True
                for i in indices:
                    if 0 <= i < len(reference_files):
                        selected_files.append(reference_files[i])
                    else:
                        print(f"错误：编号 {i + 1} 无效。")
                        valid_selection = False
                        break
                
                if valid_selection:
                    return selected_files
            except ValueError:
                print("输入无效，请输入数字编号。")
    
    def find_peaks_in_data(self, two_theta: np.ndarray, intensity: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """在实验数据中找到峰值"""
        # 自动设定峰值检测参数
        max_intensity = np.max(intensity)
        
        if self.peak_detection_height is None:
            height = max_intensity * self.min_intensity_ratio
        else:
            height = max_intensity * self.peak_detection_height
            
        if self.peak_detection_prominence is None:
            prominence = max_intensity * 0.02  # 2%的突出度
        else:
            prominence = max_intensity * self.peak_detection_prominence
        
        # 找峰
        peaks, _ = find_peaks(intensity, 
                             height=height,
                             distance=self.peak_detection_distance,
                             prominence=prominence)
        
        peak_angles = two_theta[peaks]
        peak_intensities = intensity[peaks]
        
        return peak_angles, peak_intensities
    
    def match_peaks_to_references(self, peak_angles: np.ndarray, peak_intensities: np.ndarray, 
                                reference_data: Dict) -> Dict:
        """将实验峰值与参考数据匹配 - 优先匹配强度更高的峰"""
        matches = {}
        
        # 创建峰值信息列表，按强度排序
        peak_info = [(peak_angles[i], peak_intensities[i], i) for i in range(len(peak_angles))]
        peak_info.sort(key=lambda x: x[1], reverse=True)  # 按强度降序排列
        
        # 记录已经匹配的峰值索引，避免重复匹配
        used_peak_indices = set()
        
        for phase_name, ref_data in reference_data.items():
            phase_matches = []
            
            for ref_angle in ref_data['two_theta']:
                best_match = None
                best_intensity = 0
                
                # 在角度容差范围内寻找强度最高的峰
                for angle, intensity, idx in peak_info:
                    if idx in used_peak_indices:
                        continue
                        
                    angle_diff = abs(angle - ref_angle)
                    if angle_diff <= self.angle_tolerance:
                        # 找到角度匹配的峰，选择强度最高的
                        if intensity > best_intensity:
                            best_match = {
                                'exp_angle': angle,
                                'ref_angle': ref_angle,
                                'intensity': intensity,
                                'diff': angle_diff,
                                'peak_idx': idx
                            }
                            best_intensity = intensity
                
                # 如果找到匹配，添加到结果中并标记峰值为已使用
                if best_match:
                    phase_matches.append(best_match)
                    used_peak_indices.add(best_match['peak_idx'])
            
            if phase_matches:
                matches[phase_name] = {
                    'matches': phase_matches,
                    'symbol': ref_data['symbol'],
                    'count': len(phase_matches)
                }
        
        return matches
    
    def add_peak_annotations(self, ax, matches: Dict, max_intensity: float):
        """在图上添加峰值标注"""
        phase_names = list(matches.keys())
        
        for i, (phase_name, match_data) in enumerate(matches.items()):
            color = self.annotation_colors[i % len(self.annotation_colors)]
            symbol = match_data['symbol']
            
            # 确保符号正确显示
            if symbol in ['♠', '♥', '♦', '♣']:
                # 使用扑克符号
                display_symbol = symbol
            else:
                # 如果不是扑克符号，使用默认标记
                display_symbol = '●'
            
            for match in match_data['matches']:
                x = match['exp_angle']
                y = match['intensity']
                
                # 计算标注位置
                annotation_y = y + self.annotation_offset_y + (i * 20)  # 不同相错开显示
                
                # 添加标注 - 使用英文格式
                annotation_text = f"{display_symbol} {phase_name}\n{x:.2f}°"
                
                # 添加标注，使用系统字体设置
                ax.annotate(annotation_text,
                           xy=(x, y),
                           xytext=(x, annotation_y),
                           fontsize=self.annotation_fontsize,
                           color=color,
                           ha='center',
                           va='bottom',
                           arrowprops=dict(arrowstyle='->', color=color, lw=1, alpha=0.7),
                           bbox=dict(boxstyle='round,pad=0.3', facecolor='white', 
                                   edgecolor=color, alpha=0.8))
        
        # 添加相识别图例
        if matches:
            legend_elements = []
            for i, (phase_name, match_data) in enumerate(matches.items()):
                color = self.annotation_colors[i % len(self.annotation_colors)]
                symbol = match_data['symbol']
                count = match_data['count']
                
                # 确保图例中的符号正确显示
                if symbol in ['♠', '♥', '♦', '♣']:
                    display_symbol = symbol
                else:
                    display_symbol = '●'
                
                from matplotlib.lines import Line2D
                legend_elements.append(Line2D([0], [0], marker='o', color='w', 
                                            markerfacecolor=color, markersize=8,
                                            label=f"{display_symbol} {phase_name} ({count} peaks)"))  # 使用英文
            
            # 创建第二个图例 - 使用系统字体设置
            legend2 = ax.legend(handles=legend_elements, 
                              loc='upper left',
                              fontsize=self.annotation_fontsize,
                              title="Phase Identification",
                              title_fontsize=self.annotation_fontsize + 1)
            
            ax.add_artist(legend2)
    
    def load_xrd_data(self, file_path: Path) -> Tuple[Optional[np.ndarray], Optional[np.ndarray]]:
        """加载XRD实验数据"""
        try:
            # 自动识别分隔符
            with open(file_path, 'r', encoding='utf-8') as f:
                first_line = f.readline()
            
            if ',' in first_line:
                data = pd.read_csv(file_path, sep=',', header=None, engine='python')
                for col in data.columns:
                    data[col] = data[col].astype(str).str.strip().str.rstrip(',')
                    data[col] = pd.to_numeric(data[col], errors='coerce')
            else:
                data = pd.read_csv(file_path, sep=r'\s+', header=None, engine='python')
            
            two_theta = np.array(data[0].values)
            intensity = np.array(data[1].values)
            
            return two_theta, intensity
            
        except Exception as e:
            print(f"加载文件 {file_path} 时出错: {e}")
            return None, None
    
    def print_analysis_summary(self, all_matches: Dict):
        """打印分析结果摘要"""
        if not all_matches:
            print("\n未识别出任何相。")
            return
            
        print(f"\n{'='*50}")
        print("相识别分析结果摘要")
        print(f"{'='*50}")
        
        total_peaks = sum(match_data['count'] for match_data in all_matches.values())
        print(f"总计识别相数: {len(all_matches)}")
        print(f"总计匹配峰数: {total_peaks}")
        print(f"角度容差设置: ±{self.angle_tolerance}°")
        
        print(f"\n{'相名称':<20} {'符号':<5} {'匹配峰数':<8} {'主要峰位 (°)'}")
        print("-" * 60)
        
        for phase_name, match_data in all_matches.items():
            symbol = match_data['symbol']
            count = match_data['count']
            
            # 获取前3个最强的峰位
            matches = sorted(match_data['matches'], key=lambda x: x['intensity'], reverse=True)
            main_peaks = [f"{m['exp_angle']:.2f}" for m in matches[:3]]
            main_peaks_str = ", ".join(main_peaks)
            
            # 确保符号正确显示
            print(f"{phase_name:<20} {symbol:<5} {count:<8} {main_peaks_str}")
        
        print(f"{'='*50}")
        
        # 添加符号说明
        print("\n符号说明:")
        unique_symbols = set(match_data['symbol'] for match_data in all_matches.values())
        for symbol in unique_symbols:
            print(f"  {symbol} - 扑克牌符号")
        print()
        
        # 打印详细的标注信息
        print("标注信息:")
        for phase_name, match_data in all_matches.items():
            print(f"  相 {phase_name} ({match_data['symbol']}):")
            for i, match in enumerate(match_data['matches'][:5]):  # 只显示前5个
                print(f"    {match['exp_angle']:.2f}° (理论值: {match['ref_angle']:.2f}°, 偏差: {match['diff']:.3f}°)")
            if len(match_data['matches']) > 5:
                print(f"    ... 还有 {len(match_data['matches']) - 5} 个匹配峰")
        print()
    
    def plot_xrd_with_annotations(self):
        """主要的绘图和标注函数"""
        print("\n开始XRD数据分析...")
        print(f"当前配置:")
        print(f"  - 角度容差: ±{self.angle_tolerance}°")
        print(f"  - 最小强度比例: {self.min_intensity_ratio*100:.1f}%")
        print(f"  - 峰间距: {self.peak_detection_distance} 点")
        
        # 获取要绘制的文件
        files_to_plot = self.get_files_to_plot(self.script_dir)
        if not files_to_plot:
            return
        
        # 获取参考文件
        reference_files = self.search_reference_files()
        selected_references = self.select_reference_files(reference_files)
        
        # 加载参考数据
        reference_data = {}
        if selected_references:
            reference_data = self.load_reference_data(selected_references)
            print(f"\n已加载 {len(reference_data)} 个参考相的数据")
        
        # 创建图形
        fig, ax = plt.subplots(figsize=(self.figure_width, self.figure_height),
                              facecolor=self.figure_facecolor,
                              dpi=self.display_dpi,
                              subplot_kw={'facecolor': self.plot_facecolor})
        
        all_two_theta = []
        all_matches = {}
        max_intensity_overall = 0
        
        # 绘制数据并进行峰值匹配
        for i, file_path in enumerate(files_to_plot):
            two_theta, intensity = self.load_xrd_data(file_path)
            if two_theta is None or intensity is None:
                continue
                
            all_two_theta.extend(two_theta)
            max_intensity_overall = max(max_intensity_overall, np.max(intensity))
            
            # 绘制XRD曲线
            color = self.line_colors[i % len(self.line_colors)]
            ax.plot(two_theta, intensity,
                   label=file_path.name,
                   color=color,
                   linewidth=self.line_width,
                   linestyle='-',
                   alpha=self.line_alpha,
                   marker=self.marker_style,
                   markersize=self.marker_size,
                   markeredgecolor=self.marker_edge_color,
                   markerfacecolor=color)
            
            # 如果有参考数据，进行峰值匹配
            if reference_data:
                peak_angles, peak_intensities = self.find_peaks_in_data(two_theta, intensity)
                matches = self.match_peaks_to_references(peak_angles, peak_intensities, reference_data)
                
                if matches:
                    print(f"\n文件 {file_path.name} 的相识别结果:")
                    for phase, match_data in matches.items():
                        print(f"  {match_data['symbol']} {phase}: {match_data['count']} 个匹配峰")
                    
                    # 合并所有匹配结果用于标注
                    for phase, match_data in matches.items():
                        if phase not in all_matches:
                            all_matches[phase] = match_data
                        else:
                            # 合并匹配结果，去重
                            existing_angles = {m['exp_angle'] for m in all_matches[phase]['matches']}
                            for match in match_data['matches']:
                                if match['exp_angle'] not in existing_angles:
                                    all_matches[phase]['matches'].append(match)
                                    all_matches[phase]['count'] += 1
        
        if not ax.has_data():
            print("没有成功加载任何数据，无法生成图像。")
            return
        
        # 添加峰值标注
        if all_matches:
            self.add_peak_annotations(ax, all_matches, max_intensity_overall)
            self.print_analysis_summary(all_matches)
        
        # 设置图形属性
        self.setup_plot_appearance(ax, all_two_theta)
        
        # 显示和保存图形
        plt.tight_layout(pad=1.5)
        fig.canvas.draw()
        plt.pause(0.1)
        move_figure_to_center(fig)
        
        if self.save_figure:
            save_path = self.script_dir / self.save_filename
            plt.savefig(save_path, format=self.save_format, dpi=self.save_dpi,
                       bbox_inches=self.save_bbox_inches, facecolor=self.figure_facecolor)
            print(f"\n图片已保存为: {save_path}")
        
        plt.show()
    
    def setup_plot_appearance(self, ax, all_two_theta):
        """设置图形外观"""
        # 标题和标签
        ax.set_title(self.title_text,
                    fontsize=self.title_fontsize,
                    fontweight=self.title_fontweight,
                    color=self.title_color,
                    pad=self.title_pad)
        
        ax.set_xlabel(self.xlabel_text,
                     fontsize=self.axis_label_fontsize,
                     color=self.axis_label_color,
                     fontweight=self.axis_label_fontweight)
        
        ax.set_ylabel(self.ylabel_text,
                     fontsize=self.axis_label_fontsize,
                     color=self.axis_label_color,
                     fontweight=self.axis_label_fontweight)
        
        # 图例
        if self.show_legend:
            legend = ax.legend(fontsize=self.legend_fontsize,
                              loc=self.legend_location,
                              frameon=self.legend_frameon,
                              fancybox=self.legend_fancybox,
                              shadow=self.legend_shadow)
            legend.get_frame().set_alpha(self.legend_alpha)
        
        # 网格
        if self.show_grid:
            ax.grid(True, which='major', linestyle=self.grid_linestyle, 
                   alpha=self.grid_alpha, color=self.grid_color, 
                   linewidth=self.grid_linewidth)
        
        # 坐标轴范围
        if self.x_range is not None:
            ax.set_xlim(self.x_range)
        elif all_two_theta:
            ax.set_xlim(min(all_two_theta), max(all_two_theta))
        
        if self.y_range is not None:
            ax.set_ylim(self.y_range)
        else:
            ax.set_ylim(bottom=self.y_min)
        
        # 刻度
        ax.tick_params(axis='both', which='major', labelsize=self.tick_fontsize,
                      colors=self.tick_color, direction=self.tick_direction,
                      length=self.tick_length, width=self.tick_width)
        
        if not self.show_x_ticks:
            ax.tick_params(axis='x', which='both', bottom=False, top=False, labelbottom=False)
        if not self.show_y_ticks:
            ax.tick_params(axis='y', which='both', left=False, right=False, labelleft=False)
        
        # 边框
        for spine in ax.spines.values():
            spine.set_color(self.spine_color)
            spine.set_linewidth(self.spine_linewidth)
        
        if self.hide_top_spine:
            ax.spines['top'].set_visible(False)
        if self.hide_right_spine:
            ax.spines['right'].set_visible(False)

# ==================== 数据清洗功能 ====================

class XRDCardProcessor:
    """XRD卡片数据处理器"""
    
    def __init__(self):
        self.symbols = {'1': '♠', '2': '♥', '3': '♦', '4': '♣'}
    
    def search_for_files(self, search_path='.'):
        """在指定路径下递归搜索所有的.txt文件"""
        found_files = []
        print(f"\n正在路径 '{search_path}' 及其所有子文件夹中搜索 .txt 文件...")
        
        for dirpath, _, filenames in os.walk(search_path):
            for filename in filenames:
                if filename.endswith('.txt') and not filename.startswith('reference_'):
                    full_path = os.path.join(dirpath, filename)
                    found_files.append(full_path)
        
        return found_files
    
    def select_file_from_list(self, file_list):
        """提供一个文件列表让用户通过数字选择"""
        if not file_list:
            return None
        
        print("\n--- 文件选择 ---")
        print("请从以下找到的文件中选择一个进行处理:")
        for i, filepath in enumerate(file_list, 1):
            print(f"  [{i}] {os.path.basename(filepath)}  (位于: {os.path.dirname(filepath)})")
        
        while True:
            try:
                choice = int(input(f"请输入您的选择 (1-{len(file_list)}): "))
                if 1 <= choice <= len(file_list):
                    return file_list[choice - 1]
                else:
                    print(f"[提示] 无效选择，请输入1到{len(file_list)}之间的数字。")
            except ValueError:
                print("[错误] 请输入一个有效的数字。")
    
    def get_search_path(self):
        """引导用户提供一个搜索路径"""
        print("\n[提示] 未在当前目录找到卡片文件。进入高级搜索模式。")
        print("您可以提供一个文件夹路径，程序将在那里进行深度搜索。")
        
        while True:
            path = input("请输入要搜索的文件夹路径 (直接回车则退出程序): ")
            if not path:
                return None
            if os.path.isdir(path):
                return path
            else:
                print("[错误] 您输入的不是一个有效的文件夹路径，请检查后重试。")
    
    def select_symbol(self):
        """选择标注符号"""
        print("\n--- 符号选择 ---")
        print("  [1] ♠ (黑桃)")
        print("  [2] ♥ (红心)")
        print("  [3] ♦ (方块)")
        print("  [4] ♣ (梅花)")
        choice = input("请输入您的选择 (1-4): ")
        return self.symbols.get(choice, '♠')
    
    def get_intensity_threshold(self):
        """获取强度阈值"""
        print("\n--- 强度阈值设定 ---")
        return float(input("请输入相对强度的筛选阈值 (1-100, 默认为40): ") or "40")
    
    def clean_phase_name(self, name):
        """清理相名称，适用于文件名和内容名称"""
        if not name:
            return ""
        
        # 移除路径分隔符、扩展名等
        name = os.path.splitext(os.path.basename(name))[0]
        
        # 移除特殊字符，但保留中文、英文、数字、下划线、连字符
        name = re.sub(r'[^\w\u4e00-\u9fff\-]', '', name)
        
        # 移除多余的空白字符
        name = re.sub(r'\s+', '', name)
        
        return name if name else "UnknownPhase"
    
    def process_card_file(self):
        """处理卡片文件主程序"""
        print("========================================")
        print("   XRD PDF卡片智能数据清洗与提取工具")
        print("========================================")
        
        # 查找文件
        script_dir = os.path.dirname(os.path.abspath(__file__))
        found_files = [os.path.abspath(f) for f in os.listdir(script_dir) 
                      if f.endswith('.txt') and not f.startswith('reference_')]
        
        if not found_files:
            search_path = self.get_search_path()
            if not search_path:
                print("\n程序已退出。")
                return
            found_files = self.search_for_files(search_path)
        
        if not found_files:
            print("\n[最终结果] 未能找到任何卡片文件。程序已退出。")
            return
        
        # 选择文件和参数
        selected_filepath = self.select_file_from_list(found_files)
        if not selected_filepath:
            print("\n程序已退出。")
            return
        
        symbol = self.select_symbol()
        intensity_threshold = self.get_intensity_threshold()
        
        print(f"\n--- 开始处理 ---")
        print(f"源文件: {selected_filepath}")
        print(f"选用符号: {symbol}")
        print(f"强度阈值: >= {intensity_threshold}")
        
        # 读取和处理文件
        try:
            with open(selected_filepath, 'r', encoding='utf-8') as f:
                lines = f.readlines()
        except Exception as e:
            print(f"\n[严重错误] 读取文件时发生意外: {e}")
            return
        
        # 优先从文件名提取相名称，作为备用从文件内容提取
        base_filename = os.path.splitext(os.path.basename(selected_filepath))[0]
        # 清理文件名，移除特殊字符
        phase_name = self.clean_phase_name(base_filename)
        
        # 如果文件名清理后为空或无效，则从文件内容中提取作为备用
        if not phase_name or phase_name.lower() in ['untitled', 'unnamed', 'file']:
            phase_name = "UnknownPhase"
            for i, line in enumerate(lines):
                if "PDF#" in line and i + 1 < len(lines):
                    phase_name = self.clean_phase_name(lines[i+1].strip())
                    break
        
        print(f"使用相名称: {phase_name} (基于文件名: {base_filename})")
        
        # 提取峰值数据
        reference_peaks = []
        for line in lines:
            match = re.match(r'^\s*(\d+\.\d+)\s+[\d.]+\s+([\d.]+)', line)
            if match:
                try:
                    two_theta, intensity = float(match.group(1)), float(match.group(2))
                    if intensity >= intensity_threshold:
                        reference_peaks.append(two_theta)
                except (ValueError, IndexError):
                    continue
        
        if not reference_peaks:
            print(f"\n[警告] 未找到强度大于等于 {intensity_threshold} 的峰。")
            return
        
        # 保存处理结果 - 文件名基于原始文件名
        output_filename = f"reference_{phase_name}.txt"
        with open(output_filename, 'w', encoding='utf-8') as f:
            f.write(f"# Phase: {phase_name}\n")
            f.write(f"# Symbol: {symbol}\n")
            f.write(f"# Intensity Threshold: >= {intensity_threshold}\n")
            f.write(f"# Format: 2-Theta,PhaseName,Symbol\n")
            f.write(f"# ----------------------------------\n")
            for two_theta in reference_peaks:
                f.write(f"{two_theta},{phase_name},{symbol}\n")
        
        print("\n================= 成功 ==================")
        print(f"已从源文件中提取了 {len(reference_peaks)} 个强峰。")
        print(f"已生成可用的参考文件: '{output_filename}'")
        print("========================================")

def main():
    """主程序入口"""
    print("========================================")
    print("   XRD 数据综合分析工具 v2.0")
    print("   (支持配置文件自定义参数)")
    print("========================================")
    
    # 加载配置
    config = ConfigManager()
    
    print("功能选择:")
    print("  [1] 绘制XRD图谱并进行相识别标注")
    print("  [2] 处理PDF卡片文件生成参考数据")
    print("  [3] 查看当前配置")
    print("  [4] 退出程序")
    
    while True:
        try:
            choice = input("\n请选择功能 (1-4): ").strip()
            if choice == '1':
                analyzer = XRDAnalyzer(config)
                analyzer.plot_xrd_with_annotations()
                break
            elif choice == '2':
                processor = XRDCardProcessor()
                processor.process_card_file()
                break
            elif choice == '3':
                print("\n当前配置参数:")
                print(f"  角度容差: ±{config.get_float('峰值检测参数', 'angle_tolerance', 0.5)}°")
                print(f"  最小强度比例: {config.get_float('峰值检测参数', 'min_intensity_ratio', 0.05)*100:.1f}%")
                print(f"  峰间距: {config.get_int('峰值检测参数', 'peak_detection_distance', 10)} 点")
                print(f"  标注字体大小: {config.get_int('标注样式', 'annotation_fontsize', 8)}")
                print(f"  图形尺寸: {config.get_int('图形设置', 'figure_width', 12)} x {config.get_int('图形设置', 'figure_height', 7)} 英寸")
                print(f"  是否保存图片: {'是' if config.get_bool('图形设置', 'save_figure', True) else '否'}")
                print("\n提示: 可以编辑 config.ini 文件来修改这些参数")
            elif choice == '4':
                print("程序已退出。")
                break
            else:
                print("无效选择，请输入 1、2、3 或 4。")
        except KeyboardInterrupt:
            print("\n\n程序已退出。")
            break
        except Exception as e:
            print(f"发生错误: {e}")

if __name__ == "__main__":
    main()
