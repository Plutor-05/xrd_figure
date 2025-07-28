"""
XRD数据综合分析工具 - 主程序
模块化设计，支持XRD图谱绘制标注和PDF卡片数据处理
"""

from config_manager import ConfigManager
from xrd_plotter import XRDPlotter
from pdf_card_processor import PDFCardProcessor


class XRDAnalysisApp:
    """XRD数据分析应用程序主控制器"""
    
    def __init__(self):
        self.config = ConfigManager()
        print("程序初始化完成。")
    
    def show_main_menu(self):
        """显示主菜单"""
        print("\n" + "="*50)
        print("   XRD 数据综合分析工具 v2.0")
        print("   (优化版 - 使用兼容性最佳配置)")
        print("="*50)
        print("功能选择:")
        print("  [1] 绘制XRD图谱并进行相识别标注")
        print("  [2] 处理PDF卡片文件生成参考数据")
        print("  [3] 退出程序")
        print("-"*50)
    
    def get_user_choice(self):
        """获取用户选择"""
        while True:
            try:
                choice = input("请选择功能 (1-3): ").strip()
                if choice in ['1', '2', '3']:
                    return choice
                else:
                    print("无效选择，请输入 1、2 或 3。")
            except EOFError:
                print("\n检测到输入结束，退出程序。")
                return '3'
            except KeyboardInterrupt:
                print("\n用户中断，退出程序。")
                return '3'
    
    def run_xrd_plotter(self):
        """运行XRD图谱绘制模块"""
        print("\n正在启动XRD图谱绘制模块...")
        try:
            plotter = XRDPlotter(self.config)
            plotter.run()
            print("\nXRD图谱绘制完成。")
        except Exception as e:
            print(f"\nXRD图谱绘制过程中出现错误: {e}")
        
        # 询问是否继续
        self.ask_continue()
    
    def run_pdf_processor(self):
        """运行PDF卡片处理模块"""
        print("\n正在启动PDF卡片处理模块...")
        try:
            processor = PDFCardProcessor()
            success = processor.run()
            if success:
                print("\nPDF卡片处理完成。")
            else:
                print("\nPDF卡片处理未完成。")
        except Exception as e:
            print(f"\nPDF卡片处理过程中出现错误: {e}")
        
        # 询问是否继续
        self.ask_continue()
    
    def ask_continue(self):
        """询问用户是否继续使用程序"""
        print("\n" + "-"*50)
        while True:
            try:
                choice = input("是否继续使用程序？(y/n): ").strip().lower()
                if choice in ['y', 'yes', '是', '']:
                    return True
                elif choice in ['n', 'no', '否']:
                    print("感谢使用，程序即将退出。")
                    return False
                else:
                    print("请输入 y(是) 或 n(否)。")
            except (EOFError, KeyboardInterrupt):
                print("\n程序即将退出。")
                return False
    
    def run(self):
        """主程序运行循环"""
        print("="*50)
        print("欢迎使用 XRD 数据综合分析工具!")
        print("="*50)
        
        while True:
            try:
                # 显示主菜单
                self.show_main_menu()
                
                # 获取用户选择
                choice = self.get_user_choice()
                
                # 根据选择执行相应功能
                if choice == '1':
                    self.run_xrd_plotter()
                elif choice == '2':
                    self.run_pdf_processor()
                elif choice == '3':
                    print("感谢使用XRD数据综合分析工具，再见！")
                    break
                
                # 每个功能执行完后会自动回到主菜单
                
            except KeyboardInterrupt:
                print("\n\n程序被用户中断，正在退出...")
                break
            except Exception as e:
                print(f"\n程序运行过程中出现意外错误: {e}")
                print("程序将返回主菜单，您可以尝试其他功能。")


def main():
    """程序入口点"""
    app = XRDAnalysisApp()
    app.run()


if __name__ == "__main__":
    main()
