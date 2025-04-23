from flask import render_template, request, send_file
from app import app
from app.utils import generate_solar_quote, allowed_file, get_radio_value
import os
from werkzeug.utils import secure_filename
from io import BytesIO
import matplotlib.pyplot as plt
from matplotlib import rcParams
import numpy as np
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/generate', methods=['POST'])
def generate_pdf():
    try:
        # 获取表单数据
        customer_data = {
            'project_id': request.form['project_id'],
            'first_name': request.form['first_name'],
            'last_name': request.form['last_name'],
            'name': f"{request.form['first_name']} {request.form['last_name']}",
            'address': request.form['address'],
            'roof_material': get_radio_value(request.form, 'roof_material', 'Others', 'roof_others_detail'),
            'meter_box': get_radio_value(request.form, 'meter_box', None, None),
            'storey': get_radio_value(request.form, 'storey', 'Other', 'storey_other_detail')
        }
        
        system_details = {
            'system_size': request.form['system_size'],
            'panel_module': request.form['panel_module'],
            'panel_warranty': request.form['panel_warranty'],
            'panel_qty': request.form['panel_qty'],
            'panel_performance_warranty': request.form['panel_performance_warranty'],
            'inverter_module': request.form['inverter_module'],
            'inverter_warranty': request.form['inverter_warranty'],
            'inverter_qty': request.form['inverter_qty'],
            'inverter_performance_warranty': request.form['inverter_performance_warranty'],
            'daily_generation': request.form['daily_generation']
        }
        
        pricing = {
            'stc_rebate': request.form['stc_rebate'],
            'price_before_rebate': request.form['price_before_rebate'],
            'system_price': request.form['system_price'],
            'total_cost': request.form['total_cost']
        }
        
        # 处理图片上传
        roof_design_image_path = None
        if 'roof_design_image' in request.files:
            file = request.files['roof_design_image']
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                roof_design_image_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(roof_design_image_path)

        # 生成图表数据
        chart_buffer = None
        if all(key in request.form for key in ['before_total', 'after_total', 'before_costs', 'after_costs']):
            try:
                # 确保数据格式正确
                before_costs = [float(x) for x in request.form['before_costs'].split(',') if x.strip()]
                after_costs = [float(x) for x in request.form['after_costs'].split(',') if x.strip()]
                
                if len(before_costs) == 10 and len(after_costs) == 10:
                    # 生成图表图片
                    chart_buffer = BytesIO()
                    
                    # 设置中文字体
                    plt.rcParams['font.sans-serif'] = ['Microsoft YaHei']
                    plt.rcParams['axes.unicode_minus'] = False

                    # 数据准备（与generate_chart完全一致）
                    years = [str(y) for y in range(2025, 2035)]
                    cost_data = {
                        f'安装太阳能前电费(10年): ${float(request.form["before_total"]):,}': before_costs,
                        f'安装太阳能后电费(10年): ${float(request.form["after_total"]):,}': after_costs
                    }

                    # 创建画布（保持12x8英寸大小）
                    fig = plt.figure(figsize=(12, 8))
                    ax1 = fig.add_subplot(1, 1, 1)
                    
                    # 柱状图设置（完全一致）
                    bar_width = 0.35
                    x = np.arange(len(years))
                    colors = ['#ffbda4', '#f94501']
                    
                    # 绘制柱状图（保持原有颜色和样式）
                    bars_before = ax1.bar(x - bar_width/2, before_costs, width=bar_width, 
                                        label=list(cost_data.keys())[0], color=colors[0])
                    bars_after = ax1.bar(x + bar_width/2, after_costs, width=bar_width,
                                       label=list(cost_data.keys())[1], color=colors[1])

                    # 添加数值标签（完全一致）
                    for rect in bars_before:
                        height = rect.get_height()
                        ax1.text(rect.get_x() + rect.get_width()/2, height + 50,
                                f'${height:,}', ha='center', va='bottom', fontsize=12)

                    for i, rect in enumerate(bars_after):
                        height = rect.get_height()
                        if height < 0:
                            ax1.text(rect.get_x() + rect.get_width()/2, height - 60,
                                    f'-${abs(height):,}', ha='center', va='top', fontsize=12)
                        elif height > 0:
                            ax1.text(rect.get_x() + rect.get_width()/2, height + 50,
                                    f'${height:,}', ha='center', va='bottom', fontsize=12)

                    # 图表装饰（完全保持原样）
                    ax1.set_xticks(x)
                    ax1.set_xticklabels(years)
                    max_value = max(max(before_costs), max(abs(v) for v in after_costs))
                    ax1.set_ylim(-max_value*0.2, max_value*1.3)
                    ax1.set_title('太阳能系统电费对比 (2025-2034)', pad=20, fontsize=14)
                    ax1.set_ylabel('金额（$）', fontsize=12)
                    ax1.set_xlabel('年份', fontsize=12)
                    ax1.axhline(0, color='black', linewidth=0.8)
                    ax1.grid(True, axis='y', linestyle='--', alpha=0.7)
                    ax1.legend(loc='upper left', fontsize=13)

                    # 保存图像（保持300dpi高质量）
                    plt.savefig(chart_buffer, format='png', dpi=300, bbox_inches='tight')
                    plt.close()
                    chart_buffer.seek(0)
                    
            except Exception as e:
                print(f"图表生成错误: {str(e)}")
                chart_buffer = None

        # 生成PDF（确保传递chart_buffer）
        buffer = BytesIO()
        generate_solar_quote(buffer, customer_data, system_details, pricing, 
                           roof_design_image_path, chart_buffer)
        buffer.seek(0)
        
        return send_file(
            buffer,
            as_attachment=True,
            download_name=f"Solar_Quote_{customer_data['project_id']}.pdf",
            mimetype='application/pdf'
        )
        
    except Exception as e:
        print(f"PDF生成错误: {str(e)}")
        return "生成PDF时出错，请检查数据格式", 500

@app.route('/generate_chart', methods=['POST'])
def generate_chart():
    # 获取表单数据
    data = request.json
    
    # 设置中文字体
    rcParams['font.sans-serif'] = ['Microsoft YaHei']
    rcParams['axes.unicode_minus'] = False

    # 数据准备（确保与前端计算完全一致）
    years = [str(y) for y in range(2025, 2035)]
    cost_data = {
        f'安装太阳能前电费(10年): ${data["before_total"]:,}': data["before_costs"],
        f'安装太阳能后电费(10年): ${data["after_total"]:,}': data["after_costs"]
    }

    # 创建画布
    fig = plt.figure(figsize=(12, 8))
    ax1 = fig.add_subplot(1, 1, 1)
    
    # 柱状图设置
    bar_width = 0.35
    x = np.arange(len(years))
    colors = ['#ffbda4', '#f94501']
    
    # 修改点1：直接使用负值绘制，不需要分离正负值
    after_values = data["after_costs"]

    # 绘制柱状图（保持原有颜色）
    bars_before = ax1.bar(x - bar_width/2, data["before_costs"], width=bar_width, 
                         label=list(cost_data.keys())[0], color=colors[0])
    
    # 修改点2：直接绘制包含负值的柱状图
    bars_after = ax1.bar(x + bar_width/2, after_values, width=bar_width,
                        label=list(cost_data.keys())[1], color=colors[1])

    # 修改点3：调整负值标签位置
    for rect in bars_before:
        height = rect.get_height()
        ax1.text(rect.get_x() + rect.get_width()/2, height + 50,
                f'${height:,}', ha='center', va='bottom', fontsize=12)

    for i, rect in enumerate(bars_after):
        height = rect.get_height()
        # 负值标签显示在柱子下方
        if height < 0:
            ax1.text(rect.get_x() + rect.get_width()/2, height - 60,
                    f'-${abs(height):,}', ha='center', va='top', fontsize=12)
        elif height > 0:  # 正值标签显示在柱子上方
            ax1.text(rect.get_x() + rect.get_width()/2, height + 50,
                    f'${height:,}', ha='center', va='bottom', fontsize=12)

    # 图表装饰（完全保持原样）
    ax1.set_xticks(x)
    ax1.set_xticklabels(years)
    max_value = max(max(data["before_costs"]), max(abs(v) for v in after_values))
    ax1.set_ylim(-max_value*0.2, max_value*1.3)  # 稍微增加负轴空间
    ax1.set_title('太阳能系统电费对比 (2025-2034)', pad=20, fontsize=14)
    ax1.set_ylabel('金额（$）', fontsize=12)
    ax1.set_xlabel('年份', fontsize=12)
    ax1.axhline(0, color='black', linewidth=0.8)  # 加强基准线
    ax1.grid(True, axis='y', linestyle='--', alpha=0.7)
    ax1.legend(loc='upper left', fontsize=13)

    # 保存图像（保持原样）
    buffer = BytesIO()
    plt.savefig(buffer, format='png', dpi=300, bbox_inches='tight')
    plt.close()
    buffer.seek(0)
    
    return send_file(buffer, mimetype='image/png')