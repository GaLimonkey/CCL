from flask import render_template, request, send_file
from app import app
from app.utils import generate_solar_quote, allowed_file, get_radio_value
import os
from werkzeug.utils import secure_filename
from io import BytesIO

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/generate', methods=['POST'])
def generate_pdf():
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

    # 生成PDF到内存
    buffer = BytesIO()
    generate_solar_quote(buffer, customer_data, system_details, pricing, roof_design_image_path)
    buffer.seek(0)
    
    # 返回PDF文件
    return send_file(
        buffer,
        as_attachment=True,
        download_name=f"Solar_Quote_{customer_data['project_id']}.pdf",
        mimetype='application/pdf'
    )