"""
PDF卡片数据处理模块
负责从PDF卡片文件中提取峰值数据并生成标准化参考文件
"""

import os
import re
from pathlib import Path


class PDFCardProcessor:
    """PDF卡片数据处理器"""
    
    def __init__(self):
        # 扩展符号选项，包含扑克符号和几何符号
        self.symbols = {
            '1': '♠', '2': '♥', '3': '♦', '4': '♣',       # 扑克符号
            '5': '●', '6': '■', '7': '▲', '8': '◆'        # 几何符号
        }
        self.script_dir = Path(__file__).resolve().parent
    
    def search_for_files(self, search_path='.'):
        """在指定路径下递归搜索所有的.txt文件"""
        found_files = []
        search_path = Path(search_path)
        print(f"\n正在路径 '{search_path}' 及其所有子文件夹中搜索 .txt 文件...")
        
        # 定义要排除的目录
        excluded_dirs = {'.venv', 'venv', '__pycache__', '.git', 'node_modules', 
                        'site-packages', '.pytest_cache', '.mypy_cache'}
        
        # 使用Path.rglob递归搜索
        for file_path in search_path.rglob('*.txt'):
            # 检查路径中是否包含排除的目录
            if any(part in excluded_dirs for part in file_path.parts):
                continue
            if not file_path.name.startswith('reference_'):
                found_files.append(file_path)
        
        # 按修改时间排序，最新的文件在前
        found_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
        return [str(f.resolve()) for f in found_files]
    
    def get_local_card_files(self):
        """获取当前目录及子目录下的卡片文件"""
        found_files = []
        
        # 定义要排除的目录
        excluded_dirs = {'.venv', 'venv', '__pycache__', '.git', 'node_modules', 
                        'site-packages', '.pytest_cache', '.mypy_cache'}
        
        # 递归搜索所有txt文件，排除reference_开头的文件和排除目录
        for file_path in self.script_dir.rglob('*.txt'):
            # 检查路径中是否包含排除的目录
            if any(part in excluded_dirs for part in file_path.parts):
                continue
            if not file_path.name.startswith('reference_'):
                found_files.append(file_path)
        
        # 按修改时间排序，最新的文件在前
        found_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
        return [str(f.resolve()) for f in found_files]
    
    def select_file_from_list(self, file_list):
        """提供文件列表让用户选择，或者允许直接输入文件路径"""
        if not file_list:
            return self.get_direct_file_path()
        
        print("\n--- 文件选择 ---")
        print("请从以下找到的文件中选择一个进行处理 (按修改时间排序，最新在前):")
        
        for i, filepath in enumerate(file_list, 1):
            relative_path = os.path.relpath(filepath, self.script_dir)
            # 获取文件修改时间
            file_path_obj = Path(filepath)
            mtime = file_path_obj.stat().st_mtime
            import datetime
            mod_time = datetime.datetime.fromtimestamp(mtime).strftime('%Y-%m-%d %H:%M:%S')
            print(f"  [{i}] {os.path.basename(filepath)}  (位置: {relative_path})  [修改: {mod_time}]")
        
        print(f"  [0] 手动输入文件路径")
        
        while True:
            try:
                choice = input(f"请输入您的选择 (0-{len(file_list)}): ")
                
                if choice == '0':
                    return self.get_direct_file_path()
                
                choice_num = int(choice)
                if 1 <= choice_num <= len(file_list):
                    return file_list[choice_num - 1]
                else:
                    print(f"[提示] 无效选择，请输入0到{len(file_list)}之间的数字。")
            except ValueError:
                print("[错误] 请输入一个有效的数字。")
    
    def get_direct_file_path(self):
        """允许用户直接输入文件路径"""
        print("\n--- 手动输入文件路径 ---")
        print("您可以输入完整的文件路径，或者相对于当前目录的路径")
        
        while True:
            file_path = input("请输入文件路径 (直接回车返回文件列表): ").strip()
            
            if not file_path:
                return None
            
            # 尝试解析路径
            path_obj = Path(file_path)
            
            # 如果是相对路径，相对于脚本目录
            if not path_obj.is_absolute():
                path_obj = self.script_dir / path_obj
            
            # 检查文件是否存在
            if path_obj.exists() and path_obj.is_file():
                if path_obj.suffix.lower() == '.txt':
                    if not path_obj.name.startswith('reference_'):
                        print(f"[成功] 找到文件: {path_obj}")
                        return str(path_obj.resolve())
                    else:
                        print("[错误] 不能选择reference_开头的参考文件。")
                else:
                    print("[错误] 请选择.txt格式的文件。")
            else:
                print(f"[错误] 文件不存在: {file_path}")
                print("请检查路径是否正确。")
    
    def get_search_path(self):
        """引导用户提供搜索路径或直接输入文件路径"""
        print("\n[提示] 未在当前目录及子目录找到卡片文件。")
        print("您可以:")
        print("  1. 提供一个文件夹路径进行深度搜索")
        print("  2. 直接输入具体的文件路径")
        
        while True:
            path_input = input("请输入文件夹路径或文件路径 (直接回车则退出程序): ").strip()
            if not path_input:
                return None
            
            path_obj = Path(path_input)
            
            # 如果是相对路径，相对于脚本目录
            if not path_obj.is_absolute():
                path_obj = self.script_dir / path_obj
            
            if path_obj.is_dir():
                print(f"[信息] 将在目录 '{path_obj}' 中搜索文件...")
                return str(path_obj)
            elif path_obj.is_file():
                if path_obj.suffix.lower() == '.txt' and not path_obj.name.startswith('reference_'):
                    print(f"[成功] 直接使用文件: {path_obj}")
                    return str(path_obj)  # 返回文件路径，run方法中需要特殊处理
                else:
                    print("[错误] 请选择.txt格式的非reference_文件。")
            else:
                print("[错误] 您输入的路径无效，请检查后重试。")
    
    def select_symbol(self):
        """选择标注符号"""
        print("\n--- 符号选择 ---")
        print("扑克符号:")
        print("  [1] ♠ (黑桃)")
        print("  [2] ♥ (红心)")
        print("  [3] ♦ (方块)")
        print("  [4] ♣ (梅花)")
        print("几何符号:")
        print("  [5] ● (圆形)")
        print("  [6] ■ (方形)")
        print("  [7] ▲ (三角)")
        print("  [8] ◆ (菱形)")
        
        while True:
            choice = input("请输入您的选择 (1-8): ").strip()
            if choice in self.symbols:
                return self.symbols[choice]
            else:
                print("无效选择，请输入 1-8 之间的数字。")
    
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
    
    def extract_phase_name_from_file(self, selected_filepath):
        """从文件名和内容中提取相名称"""
        # 优先从文件名提取相名称
        base_filename = os.path.splitext(os.path.basename(selected_filepath))[0]
        phase_name = self.clean_phase_name(base_filename)
        
        # 如果文件名清理后为空或无效，则从文件内容中提取作为备用
        if not phase_name or phase_name.lower() in ['untitled', 'unnamed', 'file']:
            phase_name = "UnknownPhase"
            try:
                with open(selected_filepath, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                
                for i, line in enumerate(lines):
                    if "PDF#" in line and i + 1 < len(lines):
                        phase_name = self.clean_phase_name(lines[i+1].strip())
                        break
            except Exception as e:
                print(f"从文件内容提取相名称时出错: {e}")
        
        return phase_name, base_filename
    
    def extract_peaks_from_file(self, filepath, intensity_threshold):
        """从文件中提取峰值数据"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                lines = f.readlines()
        except Exception as e:
            print(f"\n[严重错误] 读取文件时发生意外: {e}")
            return None
        
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
        
        return reference_peaks
    
    def save_reference_file(self, phase_name, symbol, intensity_threshold, reference_peaks):
        """保存处理结果到参考文件"""
        output_filename = f"reference_{phase_name}.txt"
        try:
            with open(output_filename, 'w', encoding='utf-8') as f:
                f.write(f"# Phase: {phase_name}\n")
                f.write(f"# Symbol: {symbol}\n")
                f.write(f"# Intensity Threshold: >= {intensity_threshold}\n")
                f.write(f"# Format: 2-Theta,PhaseName,Symbol\n")
                f.write(f"# ----------------------------------\n")
                for two_theta in reference_peaks:
                    f.write(f"{two_theta},{phase_name},{symbol}\n")
            return output_filename
        except Exception as e:
            print(f"保存文件时出错: {e}")
            return None
    
    def process_single_file(self, selected_filepath, symbol, intensity_threshold):
        """处理单个卡片文件"""
        print(f"\n--- 开始处理 ---")
        print(f"源文件: {selected_filepath}")
        print(f"选用符号: {symbol}")
        print(f"强度阈值: >= {intensity_threshold}")
        
        # 提取相名称
        phase_name, base_filename = self.extract_phase_name_from_file(selected_filepath)
        print(f"使用相名称: {phase_name} (基于文件名: {base_filename})")
        
        # 提取峰值数据
        reference_peaks = self.extract_peaks_from_file(selected_filepath, intensity_threshold)
        if reference_peaks is None:
            return False
        
        if not reference_peaks:
            print(f"\n[警告] 未找到强度大于等于 {intensity_threshold} 的峰。")
            return False
        
        # 保存处理结果
        output_filename = self.save_reference_file(phase_name, symbol, intensity_threshold, reference_peaks)
        if output_filename:
            print("\n================= 成功 ==================")
            print(f"已从源文件中提取了 {len(reference_peaks)} 个强峰。")
            print(f"已生成可用的参考文件: '{output_filename}'")
            print("========================================")
            return True
        else:
            print("\n[错误] 保存参考文件失败。")
            return False
    
    def run(self):
        """运行PDF卡片数据处理"""
        print("========================================")
        print("   XRD PDF卡片智能数据清洗与提取工具")
        print("========================================")
        
        # 首先在当前目录及子目录查找文件
        found_files = self.get_local_card_files()
        selected_filepath = None
        
        if found_files:
            print(f"\n[信息] 在当前目录及子目录中找到 {len(found_files)} 个卡片文件")
            selected_filepath = self.select_file_from_list(found_files)
        else:
            # 如果没有找到文件，让用户输入搜索路径或直接文件路径
            search_input = self.get_search_path()
            if not search_input:
                print("\n程序已退出。")
                return False
            
            # 检查输入是文件还是目录
            path_obj = Path(search_input)
            if path_obj.is_file():
                # 直接使用该文件
                selected_filepath = search_input
            else:
                # 在指定目录搜索文件
                found_files = self.search_for_files(search_input)
                if not found_files:
                    print("\n[最终结果] 未能找到任何卡片文件。程序已退出。")
                    return False
                selected_filepath = self.select_file_from_list(found_files)
        
        if not selected_filepath:
            print("\n程序已退出。")
            return False
        
        # 选择参数
        symbol = self.select_symbol()
        intensity_threshold = self.get_intensity_threshold()
        
        # 处理文件
        success = self.process_single_file(selected_filepath, symbol, intensity_threshold)
        return success
