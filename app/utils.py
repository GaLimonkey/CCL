from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.lib.utils import ImageReader
from werkzeug.utils import secure_filename
import os

def allowed_file(filename):
    """检查上传的文件是否是允许的类型"""
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_radio_value(form_data, main_key, other_key=None, detail_key=None):
    """获取单选按钮的值"""
    main_value = form_data.get(main_key, '').strip()
    if other_key and main_value == other_key:
        detail = form_data.get(detail_key, '').strip()
        if detail:
            return f"{main_value}: {detail}"
        else:
            return main_value
    return main_value

def generate_solar_quote(buffer, customer_data, system_details, pricing, roof_design_image_path=None, chart_buffer=None):
    """生成太阳能报价PDF文档"""
    c = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter
    
    # 标准边距和行距设置
    left_margin = 72  # 1英寸边距
    line_height = 24  # 标准行距
    current_y = height - 72  # 从顶部1英寸开始
    
    # ========== 第一页：封面页 ==========
    # 标题
    c.setFont("Helvetica-Bold", 16)
    c.drawCentredString(width/2, current_y, f"Solar Quotation: {customer_data['project_id']}")
    current_y -= line_height * 1.5
    
    # 客户信息
    c.setFont("Helvetica", 12)
    c.drawString(left_margin, current_y, f"Customer: {customer_data['first_name']} {customer_data['last_name']}")
    current_y -= line_height
    
    # 地址处理
    address_lines = [f"Property Address: {customer_data['address']}"]
    for line in address_lines:
        c.drawString(left_margin, current_y, line)
        current_y -= line_height
    
    # 公司信息
    current_y -= line_height * 0.5  # 额外空半行
    c.setFont("Helvetica-Bold", 12)
    c.drawString(left_margin, current_y, "CCL Energy Group Pty Ltd")
    current_y -= line_height
    
    c.setFont("Helvetica", 10)
    company_info = [
        "BNE: U4/1645 Ipswich Rd, Rocklea QLD 4106",
        "SYD: 8 Melissa Street, Auburn NSW 2144",
        "Phone: 1300 755 765",
        "Visit: www.cclenergy.com.au"
    ]
    
    for info in company_info:
        c.drawString(left_margin, current_y, info)
        current_y -= line_height
    
    # 问候语
    current_y -= line_height * 0.5  # 额外空半行
    c.setFont("Helvetica", 12)
    greeting = f"Dear {customer_data['name']},"
    c.drawString(left_margin, current_y, greeting)
    current_y -= line_height * 1.5
    
    # 正文内容
    text_content = [
        "Thank you for choosing CCL Energy Group to provide you with a",
        "customized solar system solution. If you have any questions,",
        "please feel free to contact me directly during business hours.",
        "",
        f"Please note your project ID is {customer_data['project_id']}.",
        "Reference this ID for all future inquiries."
    ]
    
    for line in text_content:
        if line:  # 非空行
            c.drawString(left_margin, current_y, line)
        current_y -= line_height
    
    # 联系信息
    current_y -= line_height  # 额外空一行
    c.setFont("Helvetica-Bold", 12)
    c.drawString(left_margin, current_y, "Thank you,")
    current_y -= line_height
    c.drawString(left_margin, current_y, "Marco Lin")
    current_y -= line_height
    
    c.setFont("Helvetica", 10)
    c.drawString(left_margin, current_y, "+61 0405 411 777")
    current_y -= line_height
    c.drawString(left_margin, current_y, "Marco@cclenergy.com.au")
    
    # 页脚
    footer_y = 72  # 底部1英寸边距
    c.setFont("Helvetica", 8)
    footer_lines = [
        "CCL Energy Group is an Australian-owned solar retailer dedicated to",
        "providing excellent residential and commercial solar solutions.",
        "We are proud to help Australian households reduce electricity bills",
        "and carbon footprints."
    ]
    
    for line in footer_lines:
        c.drawString(left_margin, footer_y, line)
        footer_y += line_height / 2  # 页脚行距更小
    
    c.showPage()
    
    # ========== 第二页：系统设计和房产详情 ==========
    current_y = height - 72  # 重置Y坐标
    
    # 标题
    c.setFont("Helvetica-Bold", 16)
    c.drawCentredString(width/2, current_y, "Solar System Roof Design")
    current_y -= line_height * 1.5
    
    # 房产详情标题
    c.setFont("Helvetica-Bold", 12)
    c.drawString(left_margin, current_y, "1. Property Details")
    current_y -= line_height
    
    # 属性详情表
    property_data = [
        ["Roof Material", customer_data['roof_material']],
        ["Meter Box", customer_data['meter_box']],
        ["Floor", customer_data['storey']]
    ]
    
    for label, value in property_data:
        c.drawString(left_margin, current_y, label)
        c.drawString(left_margin + 200, current_y, value)
        c.line(left_margin, current_y-5, left_margin + 400, current_y-5)  # 水平线
        current_y -= line_height
    
    # 嵌入上传的图片（如果提供）
    if roof_design_image_path:
        try:
            img = ImageReader(roof_design_image_path)
            img_width, img_height = img.getSize()
            aspect_ratio = img_height / img_width
            pdf_width = 200
            pdf_height = pdf_width * aspect_ratio
            c.drawImage(img, left_margin, current_y - pdf_height - 20, 
                       width=pdf_width, height=pdf_height)
        except Exception as e:
            print(f"Error embedding image: {e}")
    
    c.showPage()
    
    # ========== 第三页：系统详情和定价 ==========
    current_y = height - 72  # 重置Y坐标
    line_height = 24  # 标准行距
    section_gap = 36  # 节间距

    # 标题
    c.setFont("Helvetica-Bold", 16)
    c.drawCentredString(width/2, current_y, "2. Solar System Details")
    current_y -= section_gap

    # 系统大小
    c.setFont("Helvetica-Bold", 12)
    c.drawString(left_margin, current_y, f"System Size: {system_details['system_size']}")
    current_y -= line_height * 1.5  # 多空半行

    # 面板详情
    c.setFont("Helvetica-Bold", 12)
    c.drawString(left_margin, current_y, "Solar Panels:")
    current_y -= line_height

    panel_data = [
        ["Model:", system_details['panel_module']],
        ["Quantity:", system_details['panel_qty']],
        ["Product Warranty:", system_details['panel_warranty']],
        ["Performance Warranty:", system_details['panel_performance_warranty']]
    ]

    # 使用表格形式展示面板数据
    for label, value in panel_data:
        c.setFont("Helvetica", 10)
        c.drawString(left_margin + 20, current_y, label)
        c.drawString(left_margin + 150, current_y, value)
        current_y -= line_height

    # 逆变器详情（增加间距防止重叠）
    current_y -= line_height * 0.5  # 额外空半行
    c.setFont("Helvetica-Bold", 12)
    c.drawString(left_margin, current_y, "Inverter:")
    current_y -= line_height

    inverter_data = [
        ["Model:", system_details['inverter_module']],
        ["Quantity:", system_details['inverter_qty']],
        ["Product Warranty:", system_details['inverter_warranty']],
        ["Performance Warranty:", system_details['inverter_performance_warranty']]
    ]

    # 使用表格形式展示逆变器数据
    for label, value in inverter_data:
        c.setFont("Helvetica", 10)
        c.drawString(left_margin + 20, current_y, label)
        c.drawString(left_margin + 150, current_y, value)
        current_y -= line_height

    # 每日发电量（增加间距）
    current_y -= line_height * 0.5
    c.setFont("Helvetica-Bold", 10)
    c.drawString(left_margin, current_y, "Daily Power Generation:")
    c.setFont("Helvetica", 10)
    c.drawString(left_margin + 120, current_y, system_details['daily_generation'])
    current_y -= section_gap
    
    # 定价部分
    c.setFont("Helvetica-Bold", 16)
    c.drawCentredString(width/2, current_y, "3. System Price")
    current_y -= line_height * 1.5
    
    price_data = [
        ["Federal Rebate (STC)", f"${pricing['stc_rebate']}"],
        ["Price Before Rebate", f"${pricing['price_before_rebate']}"],
        ["System Price:", f"${pricing['system_price']}"],
        ["", ""],
        ["Total Cost", f"${pricing['total_cost']}"]
    ]
    
    for label, value in price_data[:-1]:
        if label:  # 跳过空行
            c.drawString(left_margin, current_y, label)
            c.drawString(left_margin + 200, current_y, value)
            current_y -= line_height
        else:
            current_y -= line_height * 0.5  # 空行间距
    
    # 突出显示总成本
    c.setFont("Helvetica-Bold", 14)
    c.drawString(left_margin, current_y, price_data[-1][0])
    c.drawString(left_margin + 200, current_y, price_data[-1][1])
    

    # ========== 第四页：电费对比图表 ==========
    c.showPage()  # 开始新页面
    current_y = height - 72  # 从顶部1英寸开始
    
    # 1. 添加标题
    c.setFont("Helvetica-Bold", 16)
    c.drawCentredString(width/2, current_y, "4. Electricity Cost Comparison")
    current_y -= 30  # 下移
    
    # 2. 嵌入图表（如果有）
    if chart_buffer:
        try:
            # 重置缓冲区指针
            chart_buffer.seek(0)
            
            # 创建ImageReader
            img = ImageReader(chart_buffer)
            
            # 计算图表显示尺寸（保持宽高比）
            display_width = width - 144  # 两边各留1英寸边距
            display_height = display_width * 0.6  # 固定比例
            
            # 计算绘制位置（居中）
            x_pos = (width - display_width) / 2
            y_pos = current_y - display_height - 20  # 留出标题空间
            
            # 绘制图表
            c.drawImage(img, x_pos, y_pos, 
                       width=display_width, 
                       height=display_height,
                       preserveAspectRatio=True)
            
            # 添加图表说明
            c.setFont("Helvetica", 10)
            c.drawCentredString(width/2, y_pos - 20, 
                               "Comparison of estimated electricity costs with/without solar system")
        except Exception as e:
            print(f"图表嵌入错误: {str(e)}")
            c.setFont("Helvetica", 12)
            c.drawString(72, current_y - 50, "Chart could not be displayed")
    
    # 添加页脚
    c.setFont("Helvetica", 8)
    c.drawString(72, 72, "CCL Energy Group Pty Ltd")
    c.drawString(72, 84, "ABN: 61 160 504 763")
    
    c.save()