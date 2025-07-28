"""
XRD图谱绘制和相识别标注模块
负责加载实验数据、峰值检测、相识别和图谱标注
"""

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib as mpl
from pathlib import Path
import numpy as np
import re
from scipy.signal import find_peaks
from typing import List, Tuple, Dict, Optional


def move_figure_to_center(fig):
    """将Matplotlib窗口移动到屏幕中央"""
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
            screen_geometry = window.screen().geometry()
            geom = window.frameGeometry()
            geom.moveCenter(screen_geometry.center())
            window.move(geom.topLeft())

        elif 'wx' in backend:
            window.Center()

    except Exception:
        pass


class XRDPlotter:
    """XRD图谱绘制和相识别标注器"""
    
    def __init__(self, config_manager):
        self.config = config_manager
        self.script_dir = Path(__file__).resolve().parent
        
        # 设置中文字体
        self._setup_fonts()
        
        # 从配置加载参数
        self._load_parameters()
        
    def _setup_fonts(self):
        """设置字体支持中文和符号"""
        try:
            # 使用兼容性最好的字体配置
            current_font = self.config.get_current_font()
            mpl.rcParams['font.sans-serif'] = [current_font, 'Microsoft YaHei', 'SimHei', 'SimSun']
            mpl.rcParams['axes.unicode_minus'] = False
            
            print(f"使用字体: {current_font}")
            
        except Exception as e:
            print(f"字体设置警告: {e}")
            mpl.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei']
            mpl.rcParams['axes.unicode_minus'] = False
    
    def _load_parameters(self):
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
        
        # 图例和坐标轴
        self.show_legend = self.config.get_bool('图例', 'show_legend', True)
        self.legend_location = self.config.get_string('图例', 'legend_location', 'upper right')
        self.legend_fontsize = self.config.get_int('图例', 'legend_fontsize', 10)
        
        self.tick_fontsize = self.config.get_int('坐标轴', 'tick_fontsize', 12)
        self.axis_label_fontsize = self.config.get_int('坐标轴', 'axis_label_fontsize', 14)
        
        # 固定样式参数
        self._setup_fixed_style()
    
    def _setup_fixed_style(self):
        """设置固定的样式参数"""
        self.title_text = 'XRD Test Results with Phase Identification'
        self.title_fontsize = 18
        self.title_fontweight = 'bold'
        self.title_color = 'black'
        self.title_pad = 20
        
        self.xlabel_text = '2θ (degrees)'
        self.ylabel_text = 'Intensity (a.u.)'
        
        self.figure_facecolor = "#eef3fa"
        self.plot_facecolor = "#FFFFFF"
        
    def search_reference_files(self) -> List[Path]:
        """搜索参考文件"""
        reference_files = sorted(self.script_dir.glob('reference_*.txt'))
        return reference_files
    
    def load_reference_data(self, reference_files: List[Path]) -> Dict:
        """加载参考数据"""
        reference_data = {}
        
        for ref_file in reference_files:
            try:
                data = []
                phase_name = ""
                symbol = ""
                
                # 优先从文件名中提取相名称
                file_stem = ref_file.stem
                if file_stem.startswith('reference_'):
                    phase_name = file_stem[10:]  # 去掉'reference_'前缀
                
                with open(ref_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        if line.startswith('# Phase:') and not phase_name:
                            phase_name = line.split(':', 1)[1].strip()
                        elif line.startswith('# Symbol:'):
                            symbol = line.split(':', 1)[1].strip()
                        elif line and not line.startswith('#'):
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
    
    def get_data_files(self) -> List[Path]:
        """获取实验数据文件"""
        data_files = sorted([f for f in self.script_dir.glob('*.txt') 
                           if not f.name.startswith('reference_')])
        return data_files
    
    def select_files_to_plot(self, data_files: List[Path]) -> List[Path]:
        """让用户选择要绘制的文件"""
        if not data_files:
            print("错误：未找到任何实验数据文件。")
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
    
    def load_xrd_data(self, file_path: Path) -> Tuple[Optional[np.ndarray], Optional[np.ndarray]]:
        """加载XRD实验数据"""
        try:
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
    
    def find_peaks_in_data(self, two_theta: np.ndarray, intensity: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """在实验数据中找到峰值"""
        max_intensity = np.max(intensity)
        height = max_intensity * self.min_intensity_ratio
        prominence = max_intensity * 0.02
        
        peaks, _ = find_peaks(intensity, 
                             height=height,
                             distance=self.peak_detection_distance,
                             prominence=prominence)
        
        peak_angles = two_theta[peaks]
        peak_intensities = intensity[peaks]
        
        return peak_angles, peak_intensities
    
    def match_peaks_to_references(self, peak_angles: np.ndarray, peak_intensities: np.ndarray, 
                                reference_data: Dict) -> Dict:
        """将实验峰值与参考数据匹配"""
        matches = {}
        
        # 按强度排序的峰值信息
        peak_info = [(peak_angles[i], peak_intensities[i], i) for i in range(len(peak_angles))]
        peak_info.sort(key=lambda x: x[1], reverse=True)
        
        used_peak_indices = set()
        
        for phase_name, ref_data in reference_data.items():
            phase_matches = []
            
            for ref_angle in ref_data['two_theta']:
                best_match = None
                best_intensity = 0
                
                for angle, intensity, idx in peak_info:
                    if idx in used_peak_indices:
                        continue
                        
                    angle_diff = abs(angle - ref_angle)
                    if angle_diff <= self.angle_tolerance:
                        if intensity > best_intensity:
                            best_match = {
                                'exp_angle': angle,
                                'ref_angle': ref_angle,
                                'intensity': intensity,
                                'diff': angle_diff,
                                'peak_idx': idx
                            }
                            best_intensity = intensity
                
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
    
    def add_peak_annotations(self, ax, matches: Dict):
        """在图上添加峰值标注"""
        # 获取当前配置的符号组和备用符号
        current_symbols = self.config.get_current_symbols()
        fallback_symbol = self.config.get_fallback_symbol()
        
        for i, (phase_name, match_data) in enumerate(matches.items()):
            color = self.annotation_colors[i % len(self.annotation_colors)]
            symbol = match_data['symbol']
            
            # 使用配置的符号组进行显示，如果不在当前符号组中则使用备用符号
            display_symbol = symbol if symbol in current_symbols else fallback_symbol
            
            for match in match_data['matches']:
                x = match['exp_angle']
                y = match['intensity']
                annotation_y = y + self.annotation_offset_y + (i * 20)
                
                annotation_text = f"{display_symbol} {phase_name}\n{x:.2f}°"
                
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
                
                # 使用配置的符号组进行显示
                display_symbol = symbol if symbol in current_symbols else fallback_symbol
                
                from matplotlib.lines import Line2D
                legend_elements.append(Line2D([0], [0], marker='o', color='w', 
                                            markerfacecolor=color, markersize=8,
                                            label=f"{display_symbol} {phase_name} ({count} peaks)"))
            
            legend2 = ax.legend(handles=legend_elements, 
                              loc='upper left',
                              fontsize=self.annotation_fontsize,
                              title="Phase Identification",
                              title_fontsize=self.annotation_fontsize + 1)
            
            ax.add_artist(legend2)
    
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
            
            matches = sorted(match_data['matches'], key=lambda x: x['intensity'], reverse=True)
            main_peaks = [f"{m['exp_angle']:.2f}" for m in matches[:3]]
            main_peaks_str = ", ".join(main_peaks)
            
            print(f"{phase_name:<20} {symbol:<5} {count:<8} {main_peaks_str}")
        
        print(f"{'='*50}")
        
        # 符号说明
        print("\n符号说明:")
        unique_symbols = set(match_data['symbol'] for match_data in all_matches.values())
        for symbol in unique_symbols:
            print(f"  {symbol} - 扑克牌符号")
        print()
        
        # 详细标注信息
        print("标注信息:")
        for phase_name, match_data in all_matches.items():
            print(f"  相 {phase_name} ({match_data['symbol']}):")
            for i, match in enumerate(match_data['matches'][:5]):
                print(f"    {match['exp_angle']:.2f}° (理论值: {match['ref_angle']:.2f}°, 偏差: {match['diff']:.3f}°)")
            if len(match_data['matches']) > 5:
                print(f"    ... 还有 {len(match_data['matches']) - 5} 个匹配峰")
        print()
    
    def setup_plot_appearance(self, ax, all_two_theta):
        """设置图形外观"""
        ax.set_title(self.title_text,
                    fontsize=self.title_fontsize,
                    fontweight=self.title_fontweight,
                    color=self.title_color,
                    pad=self.title_pad)
        
        ax.set_xlabel(self.xlabel_text, fontsize=self.axis_label_fontsize)
        ax.set_ylabel(self.ylabel_text, fontsize=self.axis_label_fontsize)
        
        if self.show_legend:
            legend = ax.legend(fontsize=self.legend_fontsize, loc=self.legend_location)
            legend.get_frame().set_alpha(0.9)
        
        if all_two_theta:
            ax.set_xlim(min(all_two_theta), max(all_two_theta))
        ax.set_ylim(bottom=0)
        
        ax.tick_params(axis='both', which='major', labelsize=self.tick_fontsize)
        
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
    
    def run(self):
        """运行XRD图谱绘制和标注"""
        print("\n开始XRD数据分析...")
        print(f"当前配置:")
        print(f"  - 角度容差: ±{self.angle_tolerance}°")
        print(f"  - 最小强度比例: {self.min_intensity_ratio*100:.1f}%")
        print(f"  - 峰间距: {self.peak_detection_distance} 点")
        print(f"  - 字体: {self.config.get_current_font()}")
        print(f"  - 符号组: {' '.join(self.config.get_current_symbols())}")
        
        # 获取要绘制的文件
        data_files = self.get_data_files()
        files_to_plot = self.select_files_to_plot(data_files)
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
        
        # 绘制数据并进行峰值匹配
        for i, file_path in enumerate(files_to_plot):
            two_theta, intensity = self.load_xrd_data(file_path)
            if two_theta is None or intensity is None:
                continue
                
            all_two_theta.extend(two_theta)
            
            # 绘制XRD曲线
            color = self.line_colors[i % len(self.line_colors)]
            ax.plot(two_theta, intensity,
                   label=file_path.name,
                   color=color,
                   linewidth=self.line_width,
                   alpha=self.line_alpha)
            
            # 峰值匹配
            if reference_data:
                peak_angles, peak_intensities = self.find_peaks_in_data(two_theta, intensity)
                matches = self.match_peaks_to_references(peak_angles, peak_intensities, reference_data)
                
                if matches:
                    print(f"\n文件 {file_path.name} 的相识别结果:")
                    for phase, match_data in matches.items():
                        print(f"  {match_data['symbol']} {phase}: {match_data['count']} 个匹配峰")
                    
                    # 合并匹配结果
                    for phase, match_data in matches.items():
                        if phase not in all_matches:
                            all_matches[phase] = match_data
                        else:
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
            self.add_peak_annotations(ax, all_matches)
            self.print_analysis_summary(all_matches)
        
        # 设置图形外观
        self.setup_plot_appearance(ax, all_two_theta)
        
        # 显示和保存图形
        plt.tight_layout(pad=1.5)
        fig.canvas.draw()
        plt.pause(0.1)
        move_figure_to_center(fig)
        
        if self.save_figure:
            save_path = self.script_dir / self.save_filename
            plt.savefig(save_path, format=self.save_format, dpi=self.save_dpi,
                       bbox_inches='tight', facecolor=self.figure_facecolor)
            print(f"\n图片已保存为: {save_path}")
        
        plt.show()
