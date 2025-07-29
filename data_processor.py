"""
数据处理模块 - 用于XRD数据的加载、处理和分析
"""

import pandas as pd
import numpy as np
from scipy.signal import find_peaks, savgol_filter
import os
import logging

logger = logging.getLogger(__name__)

class XRDDataProcessor:
    """XRD数据处理器"""
    
    def __init__(self):
        self.symbols = ['①', '②', '③', '④', '⑤', '⑥', '⑦', '⑧', '⑨', '⑩', 
                       '⑪', '⑫', '⑬', '⑭', '⑮', '⑯', '⑰', '⑱', '⑲', '⑳']
    
    def detect_file_format(self, file_path):
        """
        自动检测文件格式
        返回: (skiprows, usecols, separator, encoding)
        """
        encodings = ['utf-8', 'gbk', 'latin1', 'ascii']
        
        for encoding in encodings:
            try:
                with open(file_path, 'r', encoding=encoding, errors='ignore') as f:
                    lines = [f.readline().strip() for _ in range(50)]
                
                # 查找数据开始的行
                data_start = 0
                separator = None
                
                for i, line in enumerate(lines):
                    if not line or line.startswith(('#', 'PDF', 'Ref:', 'CELL:', 'Strong', 'Radiation', '%')):
                        continue
                    
                    # 检测分隔符
                    if '\t' in line:
                        separator = '\t'
                        parts = line.split('\t')
                    elif ',' in line:
                        separator = ','
                        parts = line.split(',')
                    else:
                        separator = None  # 空白分隔
                        parts = line.split()
                    
                    # 检查是否包含数字数据
                    if len(parts) >= 2:
                        try:
                            # 尝试解析前两列作为2theta和intensity
                            float(parts[0])
                            float(parts[1])
                            data_start = i
                            return data_start, [0, 1], separator, encoding
                        except ValueError:
                            # 尝试解析第1和第3列（有些格式中间有其他列）
                            if len(parts) >= 3:
                                try:
                                    float(parts[0])
                                    float(parts[2])
                                    data_start = i
                                    return data_start, [0, 2], separator, encoding
                                except ValueError:
                                    continue
                
                # 如果没有找到明确的数据开始行，使用默认值
                return 20, [0, 1], None, encoding
                
            except Exception:
                continue
        
        # 如果所有编码都失败，使用默认值
        return 20, [0, 1], None, 'utf-8'
    
    def load_experimental_data(self, file_path, config=None):
        """
        加载实验数据文件
        """
        try:
            logger.info(f"正在加载实验数据: {file_path}")
            
            # 检测文件格式
            skiprows, usecols, separator, encoding = self.detect_file_format(file_path)
            
            # 准备读取参数
            read_params = {
                'header': None,
                'names': ['2theta', 'intensity'],
                'comment': '#',
                'encoding': encoding,
                'usecols': usecols,
                'skiprows': skiprows
            }
            
            if separator:
                read_params['sep'] = separator
            else:
                read_params['delim_whitespace'] = True
            
            # 尝试读取数据
            try:
                exp_data = pd.read_csv(file_path, **read_params)
            except Exception as e:
                # 如果失败，尝试其他方法
                logger.warning(f"首次读取失败，尝试备用方法: {e}")
                
                # 备用方法：更宽松的参数
                backup_params = [
                    {'delim_whitespace': True, 'header': None, 'usecols': [0, 1], 'encoding': encoding},
                    {'sep': ',', 'header': None, 'usecols': [0, 1], 'encoding': encoding},
                    {'sep': '\t', 'header': None, 'usecols': [0, 1], 'encoding': encoding},
                    {'sep': None, 'header': None, 'usecols': [0, 1], 'encoding': encoding, 'engine': 'python'}
                ]
                
                for params in backup_params:
                    try:
                        exp_data = pd.read_csv(file_path, names=['2theta', 'intensity'], 
                                             comment='#', **params)
                        break
                    except Exception:
                        continue
                else:
                    raise ValueError("所有读取方法都失败")
            
            # 数据验证和清理
            exp_data = self.clean_experimental_data(exp_data, config)
            
            logger.info(f"成功加载实验数据，数据点数: {len(exp_data)}")
            logger.info(f"2θ范围: {exp_data['2theta'].min():.2f}° - {exp_data['2theta'].max():.2f}°")
            logger.info(f"强度范围: {exp_data['intensity'].min():.0f} - {exp_data['intensity'].max():.0f}")
            
            return exp_data
            
        except Exception as e:
            logger.error(f"加载实验数据失败: {e}")
            raise Exception(f"实验数据加载失败: {str(e)}")
    
    def clean_experimental_data(self, data, config=None):
        """清理实验数据"""
        # 删除缺失值
        data = data.dropna()
        
        # 基本数据验证
        data = data[
            (data['2theta'] > 0) & 
            (data['2theta'] < 180) & 
            (data['intensity'] >= 0)
        ]
        
        if len(data) < 100:
            raise ValueError("有效数据点过少（少于100个）")
        
        # 应用用户配置的过滤器
        if config:
            # 角度范围过滤
            angle_min = config.get('angle_min', 0)
            angle_max = config.get('angle_max', 180)
            data = data[(data['2theta'] >= angle_min) & (data['2theta'] <= angle_max)]
            
            # 强度阈值过滤
            intensity_threshold = config.get('intensity_threshold', 0)
            data = data[data['intensity'] >= intensity_threshold]
            
            # 数据平滑
            smooth_window = config.get('smooth_window', 1)
            if smooth_window > 1 and len(data) > smooth_window:
                try:
                    # 使用Savitzky-Golay滤波器进行平滑
                    if smooth_window % 2 == 0:
                        smooth_window += 1  # 确保窗口大小为奇数
                    
                    if len(data) > smooth_window:
                        data['intensity'] = savgol_filter(data['intensity'], 
                                                         window_length=smooth_window, 
                                                         polyorder=min(3, smooth_window-1))
                except Exception as e:
                    logger.warning(f"数据平滑失败，使用原始数据: {e}")
        
        # 排序和重置索引
        data = data.sort_values('2theta').drop_duplicates().reset_index(drop=True)
        
        return data
    
    def load_pdf_cards(self, file_paths):
        """
        加载PDF卡片数据
        """
        pdf_data = []
        successful_files = []
        
        for i, pdf_path in enumerate(file_paths):
            if i >= len(self.symbols):
                logger.warning(f"符号不足，文件 '{os.path.basename(pdf_path)}' 将被忽略")
                break
            
            try:
                phase_name = os.path.basename(pdf_path).split('.')[0]
                symbol = self.symbols[i]
                
                card_data = self.parse_pdf_card(pdf_path, phase_name, symbol)
                
                if card_data is not None and len(card_data) > 0:
                    pdf_data.append(card_data)
                    successful_files.append(phase_name)
                    logger.info(f"成功加载PDF卡片: {phase_name}")
                else:
                    logger.warning(f"PDF卡片无效或为空: {phase_name}")
                    
            except Exception as e:
                logger.error(f"加载PDF卡片 '{os.path.basename(pdf_path)}' 时发生错误: {e}")
        
        if not pdf_data:
            raise Exception("没有成功加载任何PDF卡片")
        
        # 合并所有PDF数据
        master_pdf_df = pd.concat(pdf_data, ignore_index=True)
        logger.info(f"PDF卡片数据库已建立，包含 {len(master_pdf_df)} 个理论峰")
        logger.info(f"成功加载的物相: {successful_files}")
        
        return master_pdf_df, successful_files
    
    def parse_pdf_card(self, file_path, phase_name, symbol):
        """
        解析单个PDF卡片文件
        """
        try:
            # 检测文件格式
            skiprows, usecols, separator, encoding = self.detect_file_format(file_path)
            
            # 准备读取参数
            read_params = {
                'header': None,
                'names': ['2theta', 'intensity'],
                'comment': '#',
                'encoding': encoding,
                'usecols': usecols,
                'skiprows': skiprows
            }
            
            if separator:
                read_params['sep'] = separator
            else:
                read_params['delim_whitespace'] = True
            
            # 尝试多种读取方式
            read_attempts = [
                read_params,
                {'delim_whitespace': True, 'skiprows': skiprows, 'usecols': usecols, 'header': None, 'names': ['2theta', 'intensity']},
                {'sep': ',', 'skiprows': skiprows, 'usecols': usecols, 'header': None, 'names': ['2theta', 'intensity']},
                {'sep': '\t', 'skiprows': skiprows, 'usecols': usecols, 'header': None, 'names': ['2theta', 'intensity']},
                {'delim_whitespace': True, 'skiprows': max(0, skiprows-10), 'usecols': usecols, 'header': None, 'names': ['2theta', 'intensity']}
            ]
            
            card_data = None
            for i, params in enumerate(read_attempts):
                try:
                    card_data = pd.read_csv(file_path, comment='#', **params)
                    
                    # 验证和清理数据
                    if self.validate_pdf_data(card_data):
                        card_data = self.clean_pdf_data(card_data, phase_name, symbol)
                        if len(card_data) > 0:
                            logger.debug(f"PDF卡片 {phase_name} 使用方法 {i+1} 成功解析")
                            break
                            
                except Exception as e:
                    logger.debug(f"PDF解析方法 {i+1} 失败: {e}")
                    continue
            
            if card_data is None or len(card_data) == 0:
                logger.error(f"所有PDF解析方法都失败: {file_path}")
                return None
            
            return card_data
            
        except Exception as e:
            logger.error(f"解析PDF卡片 '{file_path}' 时发生意外错误: {e}")
            return None
    
    def validate_pdf_data(self, data):
        """验证PDF数据格式"""
        if data is None or data.empty:
            return False
        
        required_columns = ['2theta', 'intensity']
        for col in required_columns:
            if col not in data.columns:
                return False
            if not pd.api.types.is_numeric_dtype(data[col]):
                return False
        
        return True
    
    def clean_pdf_data(self, data, phase_name, symbol):
        """清理PDF数据"""
        # 删除缺失值
        data = data.dropna()
        
        # 数据范围验证
        data = data[
            (data['2theta'] > 0) & 
            (data['2theta'] < 180) & 
            (data['intensity'] >= 0)
        ]
        
        # 添加物相信息
        data['phase'] = phase_name
        data['symbol'] = symbol
        
        # 排序
        data = data.sort_values('2theta').reset_index(drop=True)
        
        return data
    
    def detect_peaks(self, intensity_data, config):
        """
        自适应峰检测
        """
        # 获取峰检测参数
        params = {
            'height': config.get('peak_height', 100),
            'distance': int(config.get('peak_distance', 15)),
            'prominence': config.get('peak_prominence', 50),
            'width': config.get('peak_width', 2)
        }
        
        # 数据统计分析用于自适应调整
        mean_intensity = np.mean(intensity_data)
        std_intensity = np.std(intensity_data)
        max_intensity = np.max(intensity_data)
        
        # 自适应调整参数
        if max_intensity > 0:
            # 调整高度阈值
            adaptive_height = max(mean_intensity + 2 * std_intensity, max_intensity * 0.05)
            params['height'] = min(params['height'], adaptive_height)
            
            # 调整突出度
            adaptive_prominence = max(std_intensity, max_intensity * 0.02)
            params['prominence'] = min(params['prominence'], adaptive_prominence)
        
        logger.info(f"峰检测参数: {params}")
        
        # 执行峰检测
        peak_indices, properties = find_peaks(intensity_data, **params)
        
        logger.info(f"检测到 {len(peak_indices)} 个峰")
        
        return peak_indices, properties
    
    def match_peaks(self, found_peaks, master_pdf_df, tolerance):
        """
        优化的峰匹配算法
        """
        matched_info = []
        unmatched_count = 0
        
        logger.info("开始峰匹配...")
        
        for idx, exp_peak in found_peaks.iterrows():
            exp_2theta = exp_peak['2theta']
            exp_intensity = exp_peak['intensity']
            
            # 计算距离
            master_pdf_df_copy = master_pdf_df.copy()
            master_pdf_df_copy['delta'] = abs(master_pdf_df_copy['2theta'] - exp_2theta)
            
            # 筛选潜在匹配
            potential_matches = master_pdf_df_copy[master_pdf_df_copy['delta'] <= tolerance]
            
            if not potential_matches.empty:
                # 按距离和强度排序
                potential_matches = potential_matches.sort_values(
                    by=['delta', 'intensity'], 
                    ascending=[True, False]
                )
                best_match = potential_matches.iloc[0].copy()
                
                # 添加匹配质量信息
                best_match['match_quality'] = 1.0 - (best_match['delta'] / tolerance)
                best_match['exp_intensity'] = exp_intensity
                
                matched_info.append(best_match)
            else:
                matched_info.append(None)
                unmatched_count += 1
        
        match_count = len(found_peaks) - unmatched_count
        logger.info(f"匹配完成：{match_count}/{len(found_peaks)} 个峰成功匹配")
        
        return matched_info
    
    def generate_statistics(self, found_peaks, matched_peaks):
        """
        生成统计信息
        """
        stats = {
            'total_peaks': len(found_peaks),
            'matched_peaks': len(matched_peaks),
            'match_rate': len(matched_peaks) / len(found_peaks) * 100 if len(found_peaks) > 0 else 0,
            'phase_stats': {}
        }
        
        if len(matched_peaks) > 0:
            phase_counts = matched_peaks['match'].apply(lambda x: x['phase'] if x is not None else None).value_counts()
            for phase, count in phase_counts.items():
                percentage = count / len(matched_peaks) * 100
                stats['phase_stats'][phase] = {
                    'count': count,
                    'percentage': percentage
                }
        
        return stats
