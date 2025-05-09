import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties

def plot_table_data(file_path, chart_type='bar', output_name='chart.png', 
                   title='数据图表', xlabel='X轴', ylabel='Y轴', 
                   figsize=(12,7), color='#2c7fb8'):
    """
    表格数据可视化函数
    
    参数说明：
    - file_path:  文件路径（支持.xlsx/.xls/.csv）
    - chart_type: 图表类型（bar/line/pie/scatter）
    - output_name: 输出图片文件名
    - title: 图表标题
    - xlabel/yabel: 坐标轴标签
    - figsize: 图表尺寸(宽,高)
    - color: 主色（HEX格式）
    """
    
    # 解决中文乱码问题（参考网页3[3](@ref)）
    plt.rcParams['font.sans-serif'] = ['SimHei', 'Arial Unicode MS']
    plt.rcParams['axes.unicode_minus'] = False

    try:
        # 读取数据（兼容Excel和CSV格式，参考网页1[1](@ref)）
        if file_path.endswith(('.xlsx', '.xls')):
            df = pd.read_excel(file_path)
        else:
            df = pd.read_csv(file_path)
            
        # 自动检测数据列（参考网页5[5](@ref)）
        if len(df.columns) < 2:
            raise ValueError("表格需要至少两列数据")
            
        x_col = df.columns[0]
        y_col = df.columns[1]

        # 创建画布（参考网页7[7](@ref)）
        plt.figure(figsize=figsize)
        
        # 绘制图表（支持多种类型）
        if chart_type == 'bar':
            plt.bar(df[x_col], df[y_col], color=color, alpha=0.8)
        elif chart_type == 'line':
            plt.plot(df[x_col], df[y_col], marker='o', color=color, linewidth=2)
        elif chart_type == 'pie':
            plt.pie(df[y_col], labels=df[x_col], autopct='%1.1f%%', 
                   colors=[color, '#7fc97f', '#beaed4'])
        elif chart_type == 'scatter':
            plt.scatter(df[x_col], df[y_col], color=color, s=100, alpha=0.6)
        else:
            raise ValueError("不支持的图表类型")

        # 添加标注（参考网页5[5](@ref)）
        plt.title(title, fontsize=16, pad=20)
        plt.xlabel(xlabel)
        plt.ylabel(ylabel)
        plt.grid(axis='y', linestyle='--', alpha=0.5)
        
        # 自动旋转x轴标签（参考网页3[3](@ref)）
        plt.xticks(rotation=45, ha='right')
        
        # 保存高清图片（参考网页5[5](@ref)）
        plt.tight_layout()
        plt.savefig(output_name, dpi=300, bbox_inches='tight')
        plt.close()
        
        print(f"图表已保存至: {output_name}")
        
    except Exception as e:
        print(f"生成失败: {str(e)}")

# 使用示例（生成柱状图）
plot_table_data(
    file_path='销售数据.xlsx',
    chart_type='bar',
    output_name='月度销售柱状图.png',
    title='2023年度销售趋势',
    xlabel='月份',
    ylabel='销售额（万元）',
    color='#2ca25f'
)