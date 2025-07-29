"""
XRD峰匹配分析程序 - 图形化界面版
提供完整的可视化界面，支持参数调整和实时预览
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib as mpl
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.backends._backend_tk import NavigationToolbar2Tk
from scipy.signal import find_peaks
import os
import numpy as np
import warnings
import logging
import threading
import json
from datetime import datetime
from typing import Optional, List, Dict, Any
from config_manager_gui import ConfigManager

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)
warnings.filterwarnings('ignore', category=FutureWarning)

# 设置中文字体支持
def setup_fonts():
    """设置字体支持中文和符号"""
    try:
        mpl.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei', 'SimSun']
        mpl.rcParams['axes.unicode_minus'] = False
        logger.info("中文字体设置成功")
    except Exception as e:
        logger.warning(f"字体设置警告: {e}")

setup_fonts()

class XRDAnalyzerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("XRD峰匹配分析程序 v3.0")
        self.root.geometry("1400x900")
        self.root.minsize(1200, 800)
        
        # 初始化配置管理器
        self.config_manager = ConfigManager()
        
        # 数据存储 - 添加类型注解
        self.exp_data: Optional[pd.DataFrame] = None
        self.pdf_data: List[pd.DataFrame] = []
        self.found_peaks: Optional[pd.DataFrame] = None
        self.matched_peaks: Optional[pd.DataFrame] = None
        self.exp_file_path: Optional[str] = None
        self.pdf_file_paths: List[str] = []
        
        # 从配置文件加载配置参数
        self.init_config_from_file()
        
        self.create_widgets()
        self.setup_layout()
        
        # 设置窗口关闭时的回调
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
    def init_config_from_file(self):
        """从配置文件初始化配置参数"""
        # 加载配置文件中的数值
        config_data = self.config_manager.load_config()
        
        # 配置参数 - 使用配置文件中的值
        self.config = {
            # 峰检测参数
            'peak_height': tk.DoubleVar(value=config_data.get('peak_height', 100)),
            'peak_distance': tk.IntVar(value=config_data.get('peak_distance', 15)),
            'peak_prominence': tk.DoubleVar(value=config_data.get('peak_prominence', 50)),
            'peak_width': tk.DoubleVar(value=config_data.get('peak_width', 2)),
            'match_tolerance': tk.DoubleVar(value=config_data.get('match_tolerance', 0.2)),
            
            # 显示参数
            'figure_width': tk.DoubleVar(value=config_data.get('figure_width', 16)),
            'figure_height': tk.DoubleVar(value=config_data.get('figure_height', 8)),
            'line_width': tk.DoubleVar(value=config_data.get('line_width', 1.2)),
            'marker_size': tk.DoubleVar(value=config_data.get('marker_size', 10)),
            'font_size': tk.IntVar(value=config_data.get('font_size', 12)),
            'title_size': tk.IntVar(value=config_data.get('title_size', 18)),
            
            # 颜色设置
            'exp_data_color': tk.StringVar(value=config_data.get('exp_data_color', 'black')),
            'unmatched_color': tk.StringVar(value=config_data.get('unmatched_color', 'red')),
            'grid_alpha': tk.DoubleVar(value=config_data.get('grid_alpha', 0.4)),
            'legend_alpha': tk.DoubleVar(value=config_data.get('legend_alpha', 0.9)),
            
            # 数据处理参数
            'intensity_threshold': tk.DoubleVar(value=config_data.get('intensity_threshold', 0)),
            'angle_min': tk.DoubleVar(value=config_data.get('angle_min', 10)),
            'angle_max': tk.DoubleVar(value=config_data.get('angle_max', 70)),
            'smooth_window': tk.IntVar(value=config_data.get('smooth_window', 1)),
            
            # 输出设置
            'save_dpi': tk.IntVar(value=config_data.get('save_dpi', 300)),
            'auto_save': tk.BooleanVar(value=config_data.get('auto_save', True)),
            'show_statistics': tk.BooleanVar(value=config_data.get('show_statistics', True)),
            'show_unmatched': tk.BooleanVar(value=config_data.get('show_unmatched', True))
        }
        
    def create_widgets(self):
        """创建界面组件"""
        # 创建主框架
        self.main_frame = ttk.Frame(self.root)
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 创建左侧控制面板
        self.create_control_panel()
        
        # 创建右侧显示区域
        self.create_display_area()
        
    def create_control_panel(self):
        """创建左侧控制面板"""
        self.control_frame = ttk.Frame(self.main_frame, width=400)
        self.control_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 5))
        self.control_frame.pack_propagate(False)
        
        # 文件选择区域
        self.create_file_section()
        
        # 参数设置区域
        self.create_parameter_section()
        
        # 控制按钮区域
        self.create_control_buttons()
        
        # 日志显示区域
        self.create_log_section()
        
    def create_file_section(self):
        """创建文件选择区域"""
        file_frame = ttk.LabelFrame(self.control_frame, text="文件选择", padding=10)
        file_frame.pack(fill=tk.X, pady=(0, 10))
        
        # 实验数据文件
        ttk.Label(file_frame, text="实验数据文件:").pack(anchor=tk.W)
        exp_frame = ttk.Frame(file_frame)
        exp_frame.pack(fill=tk.X, pady=(5, 10))
        
        self.exp_file_var = tk.StringVar(value="未选择文件")
        ttk.Label(exp_frame, textvariable=self.exp_file_var, 
                 width=40, relief=tk.SUNKEN).pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Button(exp_frame, text="浏览", command=self.select_exp_file, 
                  width=8).pack(side=tk.RIGHT, padx=(5, 0))
        
        # PDF卡片文件
        ttk.Label(file_frame, text="PDF卡片文件:").pack(anchor=tk.W)
        pdf_frame = ttk.Frame(file_frame)
        pdf_frame.pack(fill=tk.X, pady=(5, 0))
        
        self.pdf_listbox = tk.Listbox(pdf_frame, height=4)
        pdf_scroll = ttk.Scrollbar(pdf_frame, orient=tk.VERTICAL, command=self.pdf_listbox.yview)
        self.pdf_listbox.configure(yscrollcommand=pdf_scroll.set)
        self.pdf_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        pdf_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        pdf_btn_frame = ttk.Frame(file_frame)
        pdf_btn_frame.pack(fill=tk.X, pady=(5, 0))
        ttk.Button(pdf_btn_frame, text="添加PDF", command=self.add_pdf_files).pack(side=tk.LEFT)
        ttk.Button(pdf_btn_frame, text="清除", command=self.clear_pdf_files).pack(side=tk.LEFT, padx=(5, 0))
        
    def create_parameter_section(self):
        """创建参数设置区域"""
        # 创建选项卡
        self.notebook = ttk.Notebook(self.control_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # 峰检测参数选项卡
        self.create_peak_detection_tab()
        
        # 显示设置选项卡
        self.create_display_tab()
        
        # 数据处理选项卡
        self.create_data_processing_tab()
        
        # 输出设置选项卡
        self.create_output_tab()
        
    def create_peak_detection_tab(self):
        """创建峰检测参数选项卡"""
        peak_frame = ttk.Frame(self.notebook)
        self.notebook.add(peak_frame, text="峰检测")
        
        # 添加滚动条
        canvas = tk.Canvas(peak_frame)
        scrollbar = ttk.Scrollbar(peak_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # 参数设置
        params = [
            ("峰高阈值:", self.config['peak_height'], 1, 1000, "检测峰的最小高度"),
            ("峰间距离:", self.config['peak_distance'], 1, 100, "相邻峰之间的最小距离"),
            ("峰突出度:", self.config['peak_prominence'], 1, 500, "峰相对于基线的突出程度"),
            ("峰宽度:", self.config['peak_width'], 1, 50, "峰的最小宽度"),
            ("匹配容差(°):", self.config['match_tolerance'], 0.01, 2.0, "实验峰与理论峰的匹配容差")
        ]
        
        for i, (label, var, min_val, max_val, tooltip) in enumerate(params):
            frame = ttk.Frame(scrollable_frame)
            frame.pack(fill=tk.X, pady=5, padx=10)
            
            ttk.Label(frame, text=label).pack(anchor=tk.W)
            
            scale_frame = ttk.Frame(frame)
            scale_frame.pack(fill=tk.X, pady=(2, 0))
            
            scale = ttk.Scale(scale_frame, from_=min_val, to=max_val, 
                            orient=tk.HORIZONTAL, variable=var)
            scale.pack(side=tk.LEFT, fill=tk.X, expand=True)
            
            entry = ttk.Entry(scale_frame, textvariable=var, width=8)
            entry.pack(side=tk.RIGHT, padx=(5, 0))
            
            # 添加工具提示
            self.create_tooltip(frame, tooltip)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
    def create_display_tab(self):
        """创建显示设置选项卡"""
        display_frame = ttk.Frame(self.notebook)
        self.notebook.add(display_frame, text="显示")
        
        canvas = tk.Canvas(display_frame)
        scrollbar = ttk.Scrollbar(display_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # 图形尺寸
        size_frame = ttk.LabelFrame(scrollable_frame, text="图形尺寸", padding=10)
        size_frame.pack(fill=tk.X, pady=5, padx=10)
        
        ttk.Label(size_frame, text="宽度:").grid(row=0, column=0, sticky=tk.W)
        ttk.Scale(size_frame, from_=8, to=24, orient=tk.HORIZONTAL, 
                 variable=self.config['figure_width']).grid(row=0, column=1, sticky=tk.EW, padx=5)
        ttk.Entry(size_frame, textvariable=self.config['figure_width'], width=8).grid(row=0, column=2)
        
        ttk.Label(size_frame, text="高度:").grid(row=1, column=0, sticky=tk.W)
        ttk.Scale(size_frame, from_=4, to=16, orient=tk.HORIZONTAL, 
                 variable=self.config['figure_height']).grid(row=1, column=1, sticky=tk.EW, padx=5)
        ttk.Entry(size_frame, textvariable=self.config['figure_height'], width=8).grid(row=1, column=2)
        
        size_frame.columnconfigure(1, weight=1)
        
        # 线条和标记
        style_frame = ttk.LabelFrame(scrollable_frame, text="样式设置", padding=10)
        style_frame.pack(fill=tk.X, pady=5, padx=10)
        
        ttk.Label(style_frame, text="线条宽度:").grid(row=0, column=0, sticky=tk.W)
        ttk.Scale(style_frame, from_=0.5, to=3.0, orient=tk.HORIZONTAL, 
                 variable=self.config['line_width']).grid(row=0, column=1, sticky=tk.EW, padx=5)
        ttk.Entry(style_frame, textvariable=self.config['line_width'], width=8).grid(row=0, column=2)
        
        ttk.Label(style_frame, text="标记大小:").grid(row=1, column=0, sticky=tk.W)
        ttk.Scale(style_frame, from_=4, to=20, orient=tk.HORIZONTAL, 
                 variable=self.config['marker_size']).grid(row=1, column=1, sticky=tk.EW, padx=5)
        ttk.Entry(style_frame, textvariable=self.config['marker_size'], width=8).grid(row=1, column=2)
        
        style_frame.columnconfigure(1, weight=1)
        
        # 字体设置
        font_frame = ttk.LabelFrame(scrollable_frame, text="字体设置", padding=10)
        font_frame.pack(fill=tk.X, pady=5, padx=10)
        
        ttk.Label(font_frame, text="字体大小:").grid(row=0, column=0, sticky=tk.W)
        ttk.Scale(font_frame, from_=8, to=20, orient=tk.HORIZONTAL, 
                 variable=self.config['font_size']).grid(row=0, column=1, sticky=tk.EW, padx=5)
        ttk.Entry(font_frame, textvariable=self.config['font_size'], width=8).grid(row=0, column=2)
        
        ttk.Label(font_frame, text="标题大小:").grid(row=1, column=0, sticky=tk.W)
        ttk.Scale(font_frame, from_=12, to=24, orient=tk.HORIZONTAL, 
                 variable=self.config['title_size']).grid(row=1, column=1, sticky=tk.EW, padx=5)
        ttk.Entry(font_frame, textvariable=self.config['title_size'], width=8).grid(row=1, column=2)
        
        font_frame.columnconfigure(1, weight=1)
        
        # 颜色设置
        color_frame = ttk.LabelFrame(scrollable_frame, text="颜色设置", padding=10)
        color_frame.pack(fill=tk.X, pady=5, padx=10)
        
        colors = [
            ("实验数据:", self.config['exp_data_color'], ['black', 'blue', 'red', 'green']),
            ("未匹配峰:", self.config['unmatched_color'], ['red', 'orange', 'purple', 'brown'])
        ]
        
        for i, (label, var, options) in enumerate(colors):
            ttk.Label(color_frame, text=label).grid(row=i, column=0, sticky=tk.W)
            ttk.Combobox(color_frame, textvariable=var, values=options, 
                        state="readonly", width=10).grid(row=i, column=1, padx=5, sticky=tk.W)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
    def create_data_processing_tab(self):
        """创建数据处理选项卡"""
        data_frame = ttk.Frame(self.notebook)
        self.notebook.add(data_frame, text="数据处理")
        
        canvas = tk.Canvas(data_frame)
        scrollbar = ttk.Scrollbar(data_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # 数据范围
        range_frame = ttk.LabelFrame(scrollable_frame, text="数据范围", padding=10)
        range_frame.pack(fill=tk.X, pady=5, padx=10)
        
        ttk.Label(range_frame, text="最小角度(°):").grid(row=0, column=0, sticky=tk.W)
        ttk.Scale(range_frame, from_=0, to=50, orient=tk.HORIZONTAL, 
                 variable=self.config['angle_min']).grid(row=0, column=1, sticky=tk.EW, padx=5)
        ttk.Entry(range_frame, textvariable=self.config['angle_min'], width=8).grid(row=0, column=2)
        
        ttk.Label(range_frame, text="最大角度(°):").grid(row=1, column=0, sticky=tk.W)
        ttk.Scale(range_frame, from_=50, to=180, orient=tk.HORIZONTAL, 
                 variable=self.config['angle_max']).grid(row=1, column=1, sticky=tk.EW, padx=5)
        ttk.Entry(range_frame, textvariable=self.config['angle_max'], width=8).grid(row=1, column=2)
        
        range_frame.columnconfigure(1, weight=1)
        
        # 数据过滤
        filter_frame = ttk.LabelFrame(scrollable_frame, text="数据过滤", padding=10)
        filter_frame.pack(fill=tk.X, pady=5, padx=10)
        
        ttk.Label(filter_frame, text="强度阈值:").grid(row=0, column=0, sticky=tk.W)
        ttk.Scale(filter_frame, from_=0, to=1000, orient=tk.HORIZONTAL, 
                 variable=self.config['intensity_threshold']).grid(row=0, column=1, sticky=tk.EW, padx=5)
        ttk.Entry(filter_frame, textvariable=self.config['intensity_threshold'], width=8).grid(row=0, column=2)
        
        ttk.Label(filter_frame, text="平滑窗口:").grid(row=1, column=0, sticky=tk.W)
        ttk.Scale(filter_frame, from_=1, to=20, orient=tk.HORIZONTAL, 
                 variable=self.config['smooth_window']).grid(row=1, column=1, sticky=tk.EW, padx=5)
        ttk.Entry(filter_frame, textvariable=self.config['smooth_window'], width=8).grid(row=1, column=2)
        
        filter_frame.columnconfigure(1, weight=1)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
    def create_output_tab(self):
        """创建输出设置选项卡"""
        output_frame = ttk.Frame(self.notebook)
        self.notebook.add(output_frame, text="输出")
        
        # 保存设置
        save_frame = ttk.LabelFrame(output_frame, text="保存设置", padding=10)
        save_frame.pack(fill=tk.X, pady=5, padx=10)
        
        ttk.Label(save_frame, text="保存DPI:").grid(row=0, column=0, sticky=tk.W)
        ttk.Combobox(save_frame, textvariable=self.config['save_dpi'], 
                    values=["150", "300", "600", "1200"], state="readonly", width=10).grid(row=0, column=1, padx=5)
        
        ttk.Checkbutton(save_frame, text="自动保存", 
                       variable=self.config['auto_save']).grid(row=1, column=0, columnspan=2, sticky=tk.W, pady=5)
        
        # 显示选项
        display_frame = ttk.LabelFrame(output_frame, text="显示选项", padding=10)
        display_frame.pack(fill=tk.X, pady=5, padx=10)
        
        ttk.Checkbutton(display_frame, text="显示统计信息", 
                       variable=self.config['show_statistics']).pack(anchor=tk.W, pady=2)
        ttk.Checkbutton(display_frame, text="显示未匹配峰", 
                       variable=self.config['show_unmatched']).pack(anchor=tk.W, pady=2)
        
    def create_control_buttons(self):
        """创建控制按钮"""
        btn_frame = ttk.Frame(self.control_frame)
        btn_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Button(btn_frame, text="开始分析", command=self.start_analysis, 
                  style="Accent.TButton").pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(btn_frame, text="清除数据", command=self.clear_data).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="导出报告", command=self.export_match_report).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="保存配置", command=self.save_config).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="加载配置", command=self.load_config).pack(side=tk.LEFT, padx=5)
        
    def create_log_section(self):
        """创建日志显示区域"""
        log_frame = ttk.LabelFrame(self.control_frame, text="运行日志", padding=5)
        log_frame.pack(fill=tk.BOTH, expand=True)
        
        self.log_text = scrolledtext.ScrolledText(log_frame, height=8, width=50)
        self.log_text.pack(fill=tk.BOTH, expand=True)
        
        # 重定向日志到文本框
        self.setup_logging()
        
    def create_display_area(self):
        """创建右侧显示区域"""
        self.display_frame = ttk.Frame(self.main_frame)
        self.display_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        # 创建matplotlib图形
        self.fig, self.ax = plt.subplots(figsize=(12, 8))
        self.canvas = FigureCanvasTkAgg(self.fig, self.display_frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        # 添加工具栏
        toolbar = NavigationToolbar2Tk(self.canvas, self.display_frame)
        toolbar.update()
        
        # 初始化空图表
        self.ax.text(0.5, 0.5, '请选择数据文件并开始分析', 
                    ha='center', va='center', transform=self.ax.transAxes, fontsize=16)
        self.ax.set_title('XRD峰匹配分析程序', fontsize=18)
        self.canvas.draw()
        
    def setup_layout(self):
        """设置布局"""
        # 设置样式
        style = ttk.Style()
        style.theme_use('clam')
        
        # 自定义样式
        style.configure("Accent.TButton", foreground="white", background="#0078d4")
        
    def create_tooltip(self, widget, text):
        """创建工具提示"""
        def on_enter(event):
            tooltip = tk.Toplevel()
            tooltip.wm_overrideredirect(True)
            tooltip.wm_geometry(f"+{event.x_root+10}+{event.y_root+10}")
            label = tk.Label(tooltip, text=text, background="lightyellow", 
                           relief="solid", borderwidth=1, font=("Arial", 9))
            label.pack()
            widget.tooltip = tooltip
            
        def on_leave(event):
            if hasattr(widget, 'tooltip'):
                widget.tooltip.destroy()
                del widget.tooltip
                
        widget.bind("<Enter>", on_enter)
        widget.bind("<Leave>", on_leave)
        
    def setup_logging(self):
        """设置日志重定向"""
        class TextHandler(logging.Handler):
            def __init__(self, text_widget):
                super().__init__()
                self.text_widget = text_widget
                
            def emit(self, record):
                msg = self.format(record)
                self.text_widget.insert(tk.END, msg + '\n')
                self.text_widget.see(tk.END)
                
        handler = TextHandler(self.log_text)
        handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
        logger.addHandler(handler)
        
    def log_message(self, message, level="INFO"):
        """添加日志消息"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.insert(tk.END, f"[{timestamp}] {level}: {message}\n")
        self.log_text.see(tk.END)
        
    def select_exp_file(self):
        """选择实验数据文件"""
        file_path = filedialog.askopenfilename(
            title="选择实验数据文件",
            filetypes=[("文本文件", "*.txt"), ("CSV文件", "*.csv"), ("所有文件", "*.*")]
        )
        if file_path:
            self.exp_file_path = file_path
            self.exp_file_var.set(os.path.basename(file_path))
            self.log_message(f"已选择实验文件: {os.path.basename(file_path)}")
            
    def add_pdf_files(self):
        """添加PDF卡片文件"""
        file_paths = filedialog.askopenfilenames(
            title="选择PDF卡片文件",
            filetypes=[("文本文件", "*.txt"), ("CSV文件", "*.csv"), ("所有文件", "*.*")]
        )
        for file_path in file_paths:
            if file_path not in self.pdf_file_paths:
                self.pdf_file_paths.append(file_path)
                self.pdf_listbox.insert(tk.END, os.path.basename(file_path))
                
        self.log_message(f"已添加 {len(file_paths)} 个PDF卡片文件")
        
    def clear_pdf_files(self):
        """清除PDF文件列表"""
        self.pdf_file_paths.clear()
        self.pdf_listbox.delete(0, tk.END)
        self.log_message("已清除PDF文件列表")
        
    def clear_data(self):
        """清除所有数据"""
        self.exp_data = None
        self.pdf_data = []
        self.found_peaks = None
        self.matched_peaks = None
        self.exp_file_path = None
        self.pdf_file_paths = []
        self.exp_file_var.set("未选择文件")
        self.pdf_listbox.delete(0, tk.END)
        
        # 清除图表
        self.ax.clear()
        self.ax.text(0.5, 0.5, '请选择数据文件并开始分析', 
                    ha='center', va='center', transform=self.ax.transAxes, fontsize=16)
        self.ax.set_title('XRD峰匹配分析程序', fontsize=18)
        self.canvas.draw()
        
        self.log_message("已清除所有数据")
        
    def start_analysis(self):
        """开始分析"""
        if not self.exp_file_path:
            messagebox.showerror("错误", "请先选择实验数据文件")
            return
            
        if not self.pdf_file_paths:
            messagebox.showerror("错误", "请先选择PDF卡片文件")
            return
            
        # 在新线程中运行分析
        threading.Thread(target=self.run_analysis, daemon=True).start()
        
    def run_analysis(self):
        """运行分析（在后台线程中）"""
        try:
            self.log_message("开始XRD峰匹配分析...")
            
            # 加载实验数据
            self.load_experimental_data()
            
            # 加载PDF数据
            self.load_pdf_data()
            
            # 峰检测
            self.detect_peaks()
            
            # 峰匹配
            self.match_peaks()
            
            # 更新图表
            self.root.after(0, self.update_plot)
            
            self.log_message("分析完成!")
            
        except Exception as e:
            self.log_message(f"分析过程中出现错误: {str(e)}", "ERROR")
            messagebox.showerror("错误", f"分析失败: {str(e)}")
            
    def load_experimental_data(self):
        """加载实验数据"""
        self.log_message("正在加载实验数据...")
        
        if not self.exp_file_path:
            raise Exception("实验文件路径未设置")
        
        try:
            # 尝试多种读取方式
            read_attempts = [
                {'delim_whitespace': True, 'header': None, 'usecols': [0, 1]},
                {'sep': ',', 'header': None, 'usecols': [0, 1]},
                {'sep': '\t', 'header': None, 'usecols': [0, 1]},
            ]
            
            for i, params in enumerate(read_attempts):
                try:
                    exp_data = pd.read_csv(
                        self.exp_file_path,
                        names=['2theta', 'intensity'],
                        comment='#',
                        **params
                    )
                    
                    # 数据验证和清理
                    exp_data = exp_data.dropna()
                    exp_data = exp_data[
                        (exp_data['2theta'] > 0) & 
                        (exp_data['2theta'] < 180) & 
                        (exp_data['intensity'] >= 0)
                    ]
                    
                    if len(exp_data) > 100:
                        self.exp_data = exp_data.sort_values('2theta').reset_index(drop=True)
                        if self.exp_data is not None:
                            self.log_message(f"成功加载实验数据，数据点数: {len(self.exp_data)}")
                        return
                        
                except Exception as e:
                    continue
                    
            raise ValueError("无法加载有效的实验数据")
            
        except Exception as e:
            raise Exception(f"实验数据加载失败: {str(e)}")
            
    def load_pdf_data(self):
        """加载PDF数据"""
        self.log_message("正在加载PDF卡片数据...")
        self.pdf_data = []
        symbols = ['①', '②', '③', '④', '⑤', '⑥', '⑦', '⑧', '⑨', '⑩', '⑪', '⑫', '⑬', '⑭', '⑮']
        
        for i, pdf_path in enumerate(self.pdf_file_paths):
            if i >= len(symbols):
                break
            
            phase_name = ""  # 初始化变量
            try:
                phase_name = os.path.basename(pdf_path).split('.')[0]
                symbol = symbols[i]
                
                # 自动检测PDF格式
                skiprows, usecols = self.detect_pdf_format(pdf_path)
                
                # 尝试读取数据
                read_attempts = [
                    {'delim_whitespace': True, 'skiprows': skiprows, 'usecols': usecols},
                    {'sep': ',', 'skiprows': skiprows, 'usecols': usecols},
                    {'sep': '\t', 'skiprows': skiprows, 'usecols': usecols},
                ]
                
                for params in read_attempts:
                    try:
                        card_data = pd.read_csv(
                            pdf_path,
                            header=None,
                            names=['2theta', 'intensity'],
                            comment='#',
                            **params
                        )
                        
                        # 数据清理
                        card_data = card_data.dropna()
                        card_data = card_data[
                            (card_data['2theta'] > 0) & 
                            (card_data['2theta'] < 180) & 
                            (card_data['intensity'] >= 0)
                        ]
                        
                        if len(card_data) > 0:
                            card_data['phase'] = phase_name
                            card_data['symbol'] = symbol
                            self.pdf_data.append(card_data)
                            self.log_message(f"成功加载PDF卡片: {phase_name}")
                            break
                            
                    except Exception:
                        continue
                        
            except Exception as e:
                self.log_message(f"PDF卡片 {phase_name} 加载失败: {str(e)}", "WARNING")
                
        if not self.pdf_data:
            raise Exception("没有成功加载任何PDF卡片")
            
    def detect_pdf_format(self, file_path):
        """检测PDF文件格式"""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                lines = [f.readline().strip() for _ in range(30)]
            
            for i, line in enumerate(lines):
                if line and not line.startswith(('#', 'PDF', 'Ref:', 'CELL:', 'Strong', 'Radiation')):
                    parts = line.split()
                    if len(parts) >= 3:
                        try:
                            float(parts[0])
                            float(parts[2])
                            return i, [0, 2]
                        except ValueError:
                            continue
            return 20, [0, 2]
        except Exception:
            return 20, [0, 2]
            
    def detect_peaks(self):
        """峰检测"""
        self.log_message("正在进行峰检测...")
        
        if self.exp_data is None:
            raise Exception("实验数据未加载")
        
        # 获取参数
        params = {
            'height': self.config['peak_height'].get(),
            'distance': int(self.config['peak_distance'].get()),
            'prominence': self.config['peak_prominence'].get(),
            'width': self.config['peak_width'].get()
        }
        
        # 数据范围过滤
        angle_min = self.config['angle_min'].get()
        angle_max = self.config['angle_max'].get()
        intensity_threshold = self.config['intensity_threshold'].get()
        
        filtered_data = self.exp_data[
            (self.exp_data['2theta'] >= angle_min) & 
            (self.exp_data['2theta'] <= angle_max) &
            (self.exp_data['intensity'] >= intensity_threshold)
        ].copy()
        
        # 平滑处理
        smooth_window = int(self.config['smooth_window'].get())
        if smooth_window > 1:
            filtered_data['intensity'] = filtered_data['intensity'].rolling(
                window=smooth_window, center=True, min_periods=1).mean()
        
        # 执行峰检测
        peak_indices, _ = find_peaks(filtered_data['intensity'], **params)
        self.found_peaks = filtered_data.iloc[peak_indices].copy()
        
        if self.found_peaks is not None:
            self.log_message(f"检测到 {len(self.found_peaks)} 个峰")
        else:
            self.log_message("峰检测失败")
        
    def match_peaks(self):
        """峰匹配"""
        self.log_message("正在进行峰匹配...")
        
        if not self.pdf_data:
            raise Exception("没有PDF数据可用于匹配")
            
        if self.found_peaks is None:
            raise Exception("没有检测到的峰数据")
            
        # 合并所有PDF数据
        master_pdf_df = pd.concat(self.pdf_data, ignore_index=True)
        
        # 获取匹配容差
        tolerance = self.config['match_tolerance'].get()
        
        matched_info = []
        for idx, exp_peak in self.found_peaks.iterrows():
            exp_2theta = exp_peak['2theta']
            
            # 计算距离
            master_pdf_df['delta'] = abs(master_pdf_df['2theta'] - exp_2theta)
            
            # 找到匹配的峰
            potential_matches = master_pdf_df[master_pdf_df['delta'] <= tolerance]
            
            if not potential_matches.empty:
                best_match = potential_matches.sort_values(['delta', 'intensity'], 
                                                         ascending=[True, False]).iloc[0].copy()
                best_match['match_quality'] = 1.0 - (best_match['delta'] / tolerance)
                matched_info.append(best_match)
            else:
                matched_info.append(None)
                
        # 添加匹配结果
        self.found_peaks['match'] = matched_info
        self.matched_peaks = self.found_peaks.dropna(subset=['match'])
        
        self.log_message(f"成功匹配 {len(self.matched_peaks)} 个峰")
        
        # 输出统计信息
        if len(self.matched_peaks) > 0:
            phase_stats = self.matched_peaks['match'].apply(lambda x: x['phase']).value_counts()
            self.log_message("各物相匹配统计:")
            for phase, count in phase_stats.items():
                percentage = count / len(self.matched_peaks) * 100
                self.log_message(f"  {phase}: {count} 个峰 ({percentage:.1f}%)")
            
            # 生成详细匹配报告
            self.generate_match_report()
                
    def generate_match_report(self):
        """生成详细的匹配结果报告"""
        try:
            if self.matched_peaks is None or len(self.matched_peaks) == 0:
                self.log_message("没有匹配数据可导出", "WARNING")
                return
            
            # 确定输出文件路径
            if self.exp_file_path:
                output_dir = os.path.dirname(self.exp_file_path)
                base_name = os.path.splitext(os.path.basename(self.exp_file_path))[0]
            else:
                output_dir = os.getcwd()
                base_name = "xrd_analysis"
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            report_path = os.path.join(output_dir, f"{base_name}_匹配报告_{timestamp}.txt")
            
            self.save_detailed_report(report_path)
            self.log_message(f"匹配报告已保存到: {report_path}")
            
        except Exception as e:
            self.log_message(f"生成匹配报告失败: {str(e)}", "ERROR")
                
    def export_match_report(self):
        """手动导出匹配报告按钮回调"""
        if self.matched_peaks is None or len(self.matched_peaks) == 0:
            messagebox.showwarning("警告", "没有匹配数据可导出，请先进行分析。")
            return
        
        # 询问用户保存位置
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        if self.exp_file_path:
            base_name = os.path.splitext(os.path.basename(self.exp_file_path))[0]
            default_name = f"{base_name}_匹配报告_{timestamp}.txt"
            initial_dir = os.path.dirname(self.exp_file_path)
        else:
            default_name = f"xrd_analysis_匹配报告_{timestamp}.txt"
            initial_dir = os.getcwd()
        
        file_path = filedialog.asksaveasfilename(
            title="保存匹配报告",
            defaultextension=".txt",
            filetypes=[("文本文件", "*.txt"), ("所有文件", "*.*")],
            initialfile=default_name,
            initialdir=initial_dir
        )
        
        if file_path:
            try:
                self.save_detailed_report(file_path)
                self.log_message(f"匹配报告已保存到: {file_path}")
                messagebox.showinfo("成功", f"匹配报告已保存到:\n{file_path}")
            except Exception as e:
                error_msg = f"保存报告失败: {str(e)}"
                self.log_message(error_msg, "ERROR")
                messagebox.showerror("错误", error_msg)
                
    def save_detailed_report(self, file_path: str):
        """保存详细匹配报告到指定文件"""
        if self.matched_peaks is None or len(self.matched_peaks) == 0:
            raise ValueError("没有匹配数据可导出")
            
        with open(file_path, 'w', encoding='utf-8') as f:
            # 写入报告头部
            f.write("=" * 80 + "\n")
            f.write("XRD峰匹配分析详细报告\n")
            f.write("=" * 80 + "\n")
            f.write(f"生成时间: {datetime.now().strftime('%Y年%m月%d日 %H:%M:%S')}\n")
            if self.exp_file_path:
                f.write(f"实验数据文件: {os.path.basename(self.exp_file_path)}\n")
            f.write(f"匹配容差: ±{self.config['match_tolerance'].get():.3f}°\n")
            f.write(f"总检测峰数: {len(self.found_peaks) if self.found_peaks is not None else 0}\n")
            f.write(f"成功匹配峰数: {len(self.matched_peaks)}\n")
            if self.found_peaks is not None and len(self.found_peaks) > 0:
                success_rate = len(self.matched_peaks)/len(self.found_peaks)*100
                f.write(f"匹配成功率: {success_rate:.1f}%\n")
            else:
                f.write(f"匹配成功率: 无法计算\n")
            f.write("\n")
            
            # 按物相分组统计
            phase_stats = self.matched_peaks['match'].apply(lambda x: x['phase']).value_counts()
            f.write("各物相匹配统计:\n")
            f.write("-" * 40 + "\n")
            for phase, count in phase_stats.items():
                percentage = count / len(self.matched_peaks) * 100
                f.write(f"{phase}: {count} 个峰 ({percentage:.1f}%)\n")
            f.write("\n")
            
            # 详细匹配结果表格
            f.write("详细匹配结果对照表:\n")
            f.write("=" * 120 + "\n")
            f.write(f"{'序号':<4} {'物相名称':<15} {'符号':<4} {'实验峰位(°)':<12} {'PDF峰位(°)':<12} {'误差(°)':<10} {'实验强度':<12} {'PDF强度':<10} {'匹配度':<8}\n")
            f.write("-" * 120 + "\n")
            
            # 按物相和峰位置排序
            sorted_matches = self.matched_peaks.sort_values('2theta')
            
            for i, (idx, peak) in enumerate(sorted_matches.iterrows(), 1):
                match_info = peak['match']
                exp_2theta = peak['2theta']
                pdf_2theta = match_info['2theta']
                error = abs(exp_2theta - pdf_2theta)
                exp_intensity = peak['intensity']
                pdf_intensity = match_info['intensity']
                match_quality = match_info['match_quality']
                phase = match_info['phase']
                symbol = match_info['symbol']
                
                f.write(f"{i:<4} {phase:<15} {symbol:<4} {exp_2theta:<12.3f} {pdf_2theta:<12.3f} "
                       f"{error:<10.3f} {exp_intensity:<12.0f} {pdf_intensity:<10.0f} {match_quality:<8.3f}\n")
            
            f.write("-" * 120 + "\n")
            f.write("\n")
            
            # 按物相分组的详细信息
            f.write("按物相分组的详细信息:\n")
            f.write("=" * 80 + "\n")
            
            for phase in phase_stats.index:
                phase_peaks = sorted_matches[sorted_matches['match'].apply(lambda x: x['phase']) == phase]
                symbol = phase_peaks.iloc[0]['match']['symbol']
                
                f.write(f"\n{symbol} {phase} ({len(phase_peaks)} 个峰):\n")
                f.write("-" * 60 + "\n")
                f.write(f"{'峰序号':<6} {'实验峰位(°)':<12} {'PDF峰位(°)':<12} {'误差(°)':<10} {'匹配度':<8}\n")
                f.write("-" * 60 + "\n")
                
                for j, (idx, peak) in enumerate(phase_peaks.iterrows(), 1):
                    match_info = peak['match']
                    exp_2theta = peak['2theta']
                    pdf_2theta = match_info['2theta']
                    error = abs(exp_2theta - pdf_2theta)
                    match_quality = match_info['match_quality']
                    
                    f.write(f"{j:<6} {exp_2theta:<12.3f} {pdf_2theta:<12.3f} {error:<10.3f} {match_quality:<8.3f}\n")
            
            # 统计摘要
            f.write(f"\n\n统计摘要:\n")
            f.write("=" * 40 + "\n")
            errors = [abs(peak['2theta'] - peak['match']['2theta']) for _, peak in sorted_matches.iterrows()]
            qualities = [peak['match']['match_quality'] for _, peak in sorted_matches.iterrows()]
            
            f.write(f"平均误差: {np.mean(errors):.4f}°\n")
            f.write(f"最大误差: {np.max(errors):.4f}°\n")
            f.write(f"最小误差: {np.min(errors):.4f}°\n")
            f.write(f"误差标准差: {np.std(errors):.4f}°\n")
            f.write(f"平均匹配度: {np.mean(qualities):.4f}\n")
            f.write(f"最高匹配度: {np.max(qualities):.4f}\n")
            f.write(f"最低匹配度: {np.min(qualities):.4f}\n")
            
            f.write(f"\n生成完成时间: {datetime.now().strftime('%Y年%m月%d日 %H:%M:%S')}\n")
            f.write("=" * 80 + "\n")
                
    def update_plot(self):
        """更新图表显示"""
        self.ax.clear()
        
        # 检查必要的数据
        if self.exp_data is None:
            self.ax.text(0.5, 0.5, '请加载实验数据', 
                        ha='center', va='center', transform=self.ax.transAxes, fontsize=16)
            self.canvas.draw()
            return
        
        # 获取显示参数
        fig_width = self.config['figure_width'].get()
        fig_height = self.config['figure_height'].get()
        line_width = self.config['line_width'].get()
        marker_size = self.config['marker_size'].get()
        font_size = int(self.config['font_size'].get())
        title_size = int(self.config['title_size'].get())
        exp_color = self.config['exp_data_color'].get()
        unmatched_color = self.config['unmatched_color'].get()
        
        # 重设图形尺寸
        self.fig.set_size_inches(fig_width, fig_height)
        
        # 绘制实验数据
        self.ax.plot(self.exp_data['2theta'], self.exp_data['intensity'], 
                    label='实验数据', color=exp_color, alpha=0.8, linewidth=line_width)
        
        # 绘制未匹配的峰
        if (self.config['show_unmatched'].get() and 
            self.found_peaks is not None and len(self.found_peaks) > 0):
            unmatched_peaks = self.found_peaks[self.found_peaks['match'].isna()]
            if len(unmatched_peaks) > 0:
                self.ax.plot(unmatched_peaks['2theta'], unmatched_peaks['intensity'], 
                            'o', markersize=marker_size*0.6, color=unmatched_color, 
                            alpha=0.7, label='未匹配峰')
        
        # 绘制匹配的峰
        colors = ['red', 'blue', 'green', 'orange', 'purple', 'brown', 'pink', 'gray', 'cyan', 'magenta']
        color_map = {}
        
        if self.matched_peaks is not None and len(self.matched_peaks) > 0:
            # 按物相分组
            phase_groups = {}
            for idx, row in self.matched_peaks.iterrows():
                match_info = row['match']
                phase = match_info['phase']
                if phase not in phase_groups:
                    phase_groups[phase] = []
                phase_groups[phase].append(row)
            
            # 为每个物相绘制峰和标注
            for i, (phase, peaks) in enumerate(phase_groups.items()):
                if phase not in color_map:
                    color_map[phase] = colors[i % len(colors)]
                
                symbol = peaks[0]['match']['symbol']
                color = color_map[phase]
                
                # 提取坐标数据
                peak_2theta = [peak['2theta'] for peak in peaks]
                peak_intensity = [peak['intensity'] for peak in peaks]
                
                # 绘制匹配的峰
                self.ax.plot(peak_2theta, peak_intensity, 
                            'x', markersize=marker_size, mew=3, color=color, 
                            label=f"{symbol} {phase}", alpha=0.9)
                
                # 添加标注
                for peak in peaks:
                    match_info = peak['match']
                    annotation_height = peak['intensity'] + max(self.exp_data['intensity']) * 0.03
                    self.ax.text(peak['2theta'], annotation_height, 
                                f"{match_info['symbol']}", 
                                ha='center', va='bottom', fontsize=font_size, 
                                color=color, weight='bold',
                                bbox=dict(boxstyle="round,pad=0.2", facecolor='white', 
                                         edgecolor=color, alpha=0.8))
        
        # 设置图表样式
        self.ax.set_title('XRD多物相识别分析', fontsize=title_size, pad=20, weight='bold')
        self.ax.set_xlabel('2θ (度)', fontsize=font_size+2, weight='bold')
        self.ax.set_ylabel('强度 (计数)', fontsize=font_size+2, weight='bold')
        
        # 图例
        legend = self.ax.legend(title="识别物相", fontsize=font_size-1, loc='upper right', 
                               title_fontsize=font_size, framealpha=self.config['legend_alpha'].get())
        legend.get_frame().set_edgecolor('gray')
        
        # 网格
        self.ax.grid(True, linestyle='--', alpha=self.config['grid_alpha'].get(), color='gray')
        self.ax.set_ylim(bottom=0)
        
        # 数据范围
        angle_min = self.config['angle_min'].get()
        angle_max = self.config['angle_max'].get()
        self.ax.set_xlim(angle_min, angle_max)
        
        # 统计信息
        if (self.config['show_statistics'].get() and 
            self.found_peaks is not None and self.matched_peaks is not None):
            stats_text = (f"总峰数: {len(self.found_peaks)}  |  "
                         f"匹配峰数: {len(self.matched_peaks)}  |  "
                         f"匹配率: {len(self.matched_peaks)/len(self.found_peaks)*100:.1f}%")
            self.ax.text(0.02, 0.98, stats_text, transform=self.ax.transAxes, 
                        fontsize=font_size-2, verticalalignment='top', 
                        bbox=dict(boxstyle="round,pad=0.3", facecolor='lightblue', alpha=0.8))
        
        # 刷新画布
        self.canvas.draw()
        
        # 自动保存
        if self.config['auto_save'].get() and self.exp_file_path:
            self.save_result()
            
    def save_result(self):
        """保存结果"""
        try:
            if self.exp_file_path:
                output_dir = os.path.dirname(self.exp_file_path) or os.getcwd()
            else:
                output_dir = os.getcwd()
                
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = os.path.join(output_dir, f'xrd_analysis_{timestamp}.png')
            
            dpi = int(self.config['save_dpi'].get())
            self.fig.savefig(output_path, dpi=dpi, bbox_inches='tight', facecolor='white')
            self.log_message(f"结果已保存到: {output_path}")
            
        except Exception as e:
            self.log_message(f"保存失败: {str(e)}", "ERROR")
            
    def save_config(self):
        """保存配置"""
        try:
            config_data = {}
            for key, var in self.config.items():
                config_data[key] = var.get()
                
            file_path = filedialog.asksaveasfilename(
                title="保存配置文件",
                defaultextension=".json",
                filetypes=[("JSON文件", "*.json"), ("所有文件", "*.*")],
                initialfile="xrd_config.json"
            )
            
            if file_path:
                # 使用ConfigManager保存配置
                if self.config_manager.save_config(config_data):
                    # 同时保存到用户指定的位置
                    with open(file_path, 'w', encoding='utf-8') as f:
                        json.dump(config_data, f, indent=2, ensure_ascii=False)
                    self.log_message(f"配置已保存到: {file_path}")
                else:
                    self.log_message("保存到默认配置文件失败", "WARNING")
                
        except Exception as e:
            messagebox.showerror("错误", f"保存配置失败: {str(e)}")
            
    def auto_save_config(self):
        """自动保存配置到默认文件"""
        try:
            config_data = {}
            for key, var in self.config.items():
                config_data[key] = var.get()
            
            if self.config_manager.save_config(config_data):
                self.log_message("配置已自动保存")
            else:
                self.log_message("自动保存配置失败", "WARNING")
                
        except Exception as e:
            self.log_message(f"自动保存配置失败: {str(e)}", "ERROR")
            
    def on_closing(self):
        """窗口关闭时的回调函数"""
        try:
            # 自动保存配置
            self.auto_save_config()
        except Exception as e:
            print(f"关闭时保存配置失败: {e}")
        finally:
            # 关闭窗口
            self.root.destroy()
            
    def load_config(self):
        """加载配置"""
        try:
            file_path = filedialog.askopenfilename(
                title="加载配置文件",
                filetypes=[("JSON文件", "*.json"), ("所有文件", "*.*")]
            )
            
            if file_path:
                with open(file_path, 'r', encoding='utf-8') as f:
                    config_data = json.load(f)
                    
                for key, value in config_data.items():
                    if key in self.config:
                        self.config[key].set(value)
                        
                self.log_message(f"配置已从 {file_path} 加载")
                
        except Exception as e:
            messagebox.showerror("错误", f"加载配置失败: {str(e)}")

def main():
    """主函数"""
    root = tk.Tk()
    app = XRDAnalyzerGUI(root)
    
    # 设置窗口图标（如果有的话）
    try:
        root.iconbitmap("icon.ico")
    except:
        pass
        
    root.mainloop()

if __name__ == "__main__":
    main()
