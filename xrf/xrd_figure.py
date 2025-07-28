import pandas as pd
import matplotlib.pyplot as plt
import matplotlib as mpl
from pathlib import Path 

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
            screen_geometry = window.screen().geometry() # type: ignore
            geom = window.frameGeometry()
            geom.moveCenter(screen_geometry.center())
            window.move(geom.topLeft())

        elif 'wx' in backend:
            window.Center()

    except Exception:
        pass

# ==================== 可自定义参数区域 ====================
# 字体设置
mpl.rcParams['font.sans-serif'] = ['SimHei', 'Arial Unicode MS', 'DejaVu Sans']  # 设置中文字体优先级
mpl.rcParams['axes.unicode_minus'] = False  # 解决负号显示问题

# ==================== 数据文件配置 ====================
script_dir = Path(__file__).resolve().parent  # 获取脚本所在目录
file_path = script_dir / 'test.txt'  # 数据文件路径（相对于脚本目录）

# ==================== 图形窗口设置 ====================
figure_width = 12          # 图形宽度（英寸）
figure_height = 7          # 图形高度（英寸）
display_dpi = 100          # 显示分辨率（屏幕显示时的DPI）

# ==================== 数据线条样式 ====================
line_color = "#4F63E5"     # 线条颜色（十六进制颜色代码或颜色名称）
line_width = 1.0           # 线条宽度（数值越大线条越粗）
line_style = '-'           # 线条样式：'-'实线, '--'虚线, ':'点线, '-.'点划线
line_alpha = 1.0           # 线条透明度（0-1，0完全透明，1完全不透明）

# ==================== 数据点标记设置 ====================
marker_style = None        # 数据点标记样式：None无标记, 'o'圆点, 's'方形, '^'三角等
marker_size = 4            # 标记大小
marker_edge_color = 'black'    # 标记边缘颜色
marker_face_color = line_color # 标记填充颜色（默认与线条颜色相同）

# ==================== 图形标题设置 ====================
title_text = 'XRD 测试结果'    # 图形标题文本
title_fontsize = 18            # 标题字体大小
title_fontweight = 'bold'      # 标题字体粗细：'normal'正常, 'bold'粗体
title_color = 'black'          # 标题颜色
title_pad = 20                 # 标题与图形的间距

# ==================== 坐标轴标签设置 ====================
xlabel_text = '2θ (degrees)'   # X轴标签文本
ylabel_text = 'Intensity (a.u.)'  # Y轴标签文本
axis_label_fontsize = 14        # 坐标轴标签字体大小
axis_label_color = 'black'      # 坐标轴标签颜色
axis_label_fontweight = 'normal' # 坐标轴标签字体粗细

# ==================== 坐标轴刻度设置 ====================
show_x_ticks = False        # 是否显示X轴刻度线和标签（True显示，False隐藏）
show_y_ticks = False       # 是否显示Y轴刻度线和标签（True显示，False隐藏）
tick_fontsize = 12         # 刻度标签字体大小
tick_color = 'black'       # 刻度标签颜色
tick_direction = 'in'      # 刻度方向：'in'向内, 'out'向外, 'inout'双向
tick_length = 6            # 刻度线长度
tick_width = 1.0           # 刻度线宽度

# ==================== 图例设置 ====================
legend_text = 'XRD实验数据'    # 图例显示的文本
legend_fontsize = 12           # 图例字体大小
legend_location = 'upper right'  # 图例位置：'upper right', 'upper left', 'lower right', 'lower left', 'center'等
show_legend = True             # 是否显示图例（True显示，False隐藏）
legend_frameon = True          # 是否显示图例边框
legend_fancybox = True         # 是否使用圆角边框
legend_shadow = False          # 是否显示图例阴影
legend_alpha = 0.9             # 图例透明度（0-1）

# ==================== 网格设置 ====================
show_grid = False          # 是否显示主网格线（True显示，False隐藏）
grid_linestyle = '--'      # 网格线样式：'-'实线, '--'虚线, ':'点线
grid_alpha = 0.5           # 网格线透明度（0-1）
grid_color = 'gray'        # 网格线颜色
grid_linewidth = 0.5       # 网格线宽度
show_minor_grid = False    # 是否显示次网格线

# ==================== 坐标轴范围设置 ====================
x_range = None             # X轴显示范围：None自动调整，或使用元组如(10, 80)
y_range = None             # Y轴显示范围：None自动调整，或使用元组如(0, 1000)
y_min = 0                  # Y轴最小值（当y_range为None时生效）

# ==================== 图形背景和边框设置 ====================
figure_facecolor = "#eef3fa"   # 图形窗口背景色
plot_facecolor = "#FFFFFF"     # 绘图区域背景色
spine_color = 'black'          # 图形边框颜色
spine_linewidth = 1.0          # 图形边框宽度
hide_top_spine = True          # 是否隐藏顶部边框
hide_right_spine = True        # 是否隐藏右侧边框

# ==================== 图形保存设置 ====================
save_figure = False            # 是否保存图形（True保存，False不保存）
save_filename = 'xrd_pattern.png'  # 保存的文件名
save_format = 'png'            # 保存格式：'png', 'pdf', 'svg', 'eps', 'jpg'等
save_dpi = 300                 # 保存时的分辨率（DPI，用于矢量格式时无效）
save_bbox_inches = 'tight'     # 保存时的边界：'tight'紧凑边界，None标准边界

# ==================== 绘图样式设置 ====================
plot_style = 'default'        # Matplotlib样式：'default', 'seaborn', 'ggplot', 'bmh'等

# ==================== 绘图主逻辑 ====================

if plot_style != 'default':
    plt.style.use(plot_style)

try:
    # 使用 sep='\s+' 替代已弃用的 delim_whitespace=True
    data = pd.read_csv(file_path, sep=r'\s+', header=None, engine='python')
    two_theta = data[0]
    intensity = data[1]

    fig, ax = plt.subplots(figsize=(figure_width, figure_height),
                           facecolor=figure_facecolor,
                           dpi=display_dpi,
                           subplot_kw={'facecolor': plot_facecolor})

    ax.plot(two_theta, intensity,
            label=legend_text,
            color=line_color,
            linewidth=line_width,
            linestyle=line_style,
            alpha=line_alpha,
            marker=marker_style,
            markersize=marker_size,
            markeredgecolor=marker_edge_color,
            markerfacecolor=marker_face_color)

    ax.set_title(title_text,
                fontsize=title_fontsize,
                fontweight=title_fontweight,
                color=title_color,
                pad=title_pad)
    ax.set_xlabel(xlabel_text,
                 fontsize=axis_label_fontsize,
                 color=axis_label_color,
                 fontweight=axis_label_fontweight)
    ax.set_ylabel(ylabel_text,
                 fontsize=axis_label_fontsize,
                 color=axis_label_color,
                 fontweight=axis_label_fontweight)

    if show_legend:
        legend = ax.legend(fontsize=legend_fontsize,
                           loc=legend_location,
                           frameon=legend_frameon,
                           fancybox=legend_fancybox,
                           shadow=legend_shadow)
        legend.get_frame().set_alpha(legend_alpha)

    if show_grid:
        ax.grid(True, which='major', linestyle=grid_linestyle, alpha=grid_alpha,
                color=grid_color, linewidth=grid_linewidth)
        if show_minor_grid:
            ax.minorticks_on()
            ax.grid(True, which='minor', linestyle=':', alpha=grid_alpha * 0.5)

    if x_range is not None:
        ax.set_xlim(x_range)
    else:
        ax.set_xlim(min(two_theta), max(two_theta))

    if y_range is not None:
        ax.set_ylim(y_range)
    else:
        ax.set_ylim(bottom=y_min)

    ax.tick_params(axis='both', which='major', labelsize=tick_fontsize,
                   colors=tick_color, direction=tick_direction,
                   length=tick_length, width=tick_width)

    # 控制坐标轴刻度显示
    if not show_x_ticks:
        ax.tick_params(axis='x', which='both', bottom=False, top=False, labelbottom=False)
    if not show_y_ticks:
        ax.tick_params(axis='y', which='both', left=False, right=False, labelleft=False)

    for spine in ax.spines.values():
        spine.set_color(spine_color)
        spine.set_linewidth(spine_linewidth)

    if hide_top_spine:
        ax.spines['top'].set_visible(False)
    if hide_right_spine:
        ax.spines['right'].set_visible(False)

    plt.tight_layout(pad=1.5)

    fig.canvas.draw()
    plt.pause(0.1)
    move_figure_to_center(fig)

    if save_figure:
        # 如果要保存，也使用动态路径
        save_path = script_dir / save_filename
        plt.savefig(save_path, format=save_format, dpi=save_dpi,
                    bbox_inches=save_bbox_inches, facecolor=figure_facecolor)
        print(f"图片已保存为: {save_path}")

    plt.show()

except FileNotFoundError:
    # 现在的错误提示会显示完整的、预期的文件路径
    print(f"错误：文件 '{file_path}' 未找到。")
    print("请确保 'test.txt' 文件与您的Python脚本在同一个目录下。")
except Exception as e:
    print(f"读取或绘图时发生错误: {e}")
    print(f"请检查 '{file_path}' 文件的格式。它应该至少包含两列由空格或制表符分隔的数字。")
