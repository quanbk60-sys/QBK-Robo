import sys, os
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib import colors
from reportlab.platypus import (BaseDocTemplate, PageTemplate, Frame, Paragraph, Spacer, Table, TableStyle,
                                KeepTogether, Image, PageBreak, ListFlowable, ListItem, CondPageBreak)

OUT = sys.argv[1]; IMG = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'img')
pdfmetrics.registerFont(TTFont('DV', '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'))
pdfmetrics.registerFont(TTFont('DVB', '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'))
INK = colors.HexColor('#1f2430'); BODY = colors.HexColor('#2a2f36'); MUTED = colors.HexColor('#5d6670')
ACC = colors.HexColor('#b8621f'); LINE = colors.HexColor('#d6dbe3'); HEAD = colors.HexColor('#f3f1ec'); ALT = colors.HexColor('#f8f9fc')
WARN = colors.HexColor('#b4541f')
W = 515

TITLE = ParagraphStyle('t', fontName='DVB', fontSize=26, leading=32, textColor=INK)
SUB = ParagraphStyle('s', fontName='DVB', fontSize=14, leading=19, textColor=ACC, spaceAfter=8)
H1 = ParagraphStyle('h1', fontName='DVB', fontSize=19, leading=24, textColor=INK, spaceBefore=4, spaceAfter=6)
H2 = ParagraphStyle('h2', fontName='DVB', fontSize=12.5, leading=16, textColor=ACC, spaceBefore=10, spaceAfter=4)
H3 = ParagraphStyle('h3', fontName='DVB', fontSize=11, leading=14, textColor=INK, spaceBefore=9, spaceAfter=2)
P = ParagraphStyle('p', fontName='DV', fontSize=9.2, leading=13, textColor=BODY, spaceAfter=4)
SM = ParagraphStyle('sm', parent=P, fontSize=8, leading=11, textColor=MUTED)
CAPT = ParagraphStyle('cap', parent=SM, alignment=1)
CELL = ParagraphStyle('c', fontName='DV', fontSize=8.4, leading=11, textColor=BODY)
CELLB = ParagraphStyle('cb', parent=CELL, fontName='DVB')
TH = ParagraphStyle('th', parent=CELL, fontName='DVB', fontSize=8, textColor=INK)
NOTE = ParagraphStyle('n', parent=P, fontSize=8.6, leading=12)
LBL = ParagraphStyle('l', parent=P, fontName='DVB', fontSize=8.6, textColor=INK, spaceBefore=2, spaceAfter=1)

def tbl(head, rows, widths, bold_first=False):
    data = [[Paragraph(h, TH) for h in head]] if head else []
    for r in rows:
        data.append([Paragraph(str(c), CELLB if (bold_first and i == 0) else CELL) for i, c in enumerate(r)])
    t = Table(data, colWidths=widths, repeatRows=1 if head else 0)
    st = [('GRID', (0, 0), (-1, -1), 0.5, LINE), ('VALIGN', (0, 0), (-1, -1), 'TOP'),
          ('TOPPADDING', (0, 0), (-1, -1), 3), ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
          ('LEFTPADDING', (0, 0), (-1, -1), 4), ('RIGHTPADDING', (0, 0), (-1, -1), 4)]
    if head: st.append(('BACKGROUND', (0, 0), (-1, 0), HEAD))
    for i in range(2 if head else 1, len(data), 2): st.append(('BACKGROUND', (0, i), (-1, i), ALT))
    t.setStyle(TableStyle(st)); return t

def note(title, text, color=ACC):
    t = Table([[Paragraph(f'<font name="DVB" color="{color.hexval()}">{title}.</font> {text}', NOTE)]], colWidths=[W])
    t.setStyle(TableStyle([('LINEBEFORE', (0, 0), (0, 0), 2.5, color), ('BACKGROUND', (0, 0), (-1, -1), ALT),
                           ('LEFTPADDING', (0, 0), (-1, -1), 8), ('TOPPADDING', (0, 0), (-1, -1), 5), ('BOTTOMPADDING', (0, 0), (-1, -1), 5)]))
    return t

def bullets(items):
    return ListFlowable([ListItem(Paragraph(x, P), leftIndent=12, value='•') for x in items], bulletType='bullet', start='•', leftIndent=12, bulletFontName='DV', bulletFontSize=8)

def numbered(items):
    return ListFlowable([ListItem(Paragraph(x, P), leftIndent=14) for x in items], bulletType='1', leftIndent=14, bulletFontName='DVB', bulletFontSize=8.6, bulletColor=ACC, bulletFormat='%s.')

B = '□'
def checks_simple(items):
    return [Paragraph('Kiểm tra', LBL)] + [Paragraph(f'{B} {x}', P) for x in items]

def step(code, title, intro=None, need=None, do=(), check=(), tip=None):
    f = [Paragraph(f'<font color="{ACC.hexval()}">{code}</font> {title}', H3)]
    if intro: f.append(Paragraph(intro, P))
    if need: f.append(Paragraph(f'<font name="DVB">Cần:</font> {need}', P))
    if do: f.append(numbered(list(do)))
    if check: f += checks_simple(list(check))
    out = [KeepTogether(f[:4]), *f[4:]]
    if tip: out += [Spacer(1, 3), note(*tip)]
    return out

def img(name, width, caption=None):
    from PIL import Image as PI
    w, h = PI.open(os.path.join(IMG, name)).size
    out = [Image(os.path.join(IMG, name), width=width, height=width * h / w)]
    if caption: out += [Spacer(1, 3), Paragraph(caption, CAPT)]
    return out

S = []
# ---------------- TRANG BÌA ----------------
S += [Paragraph('QBK-Robo', TITLE), Paragraph('Robot bánh xích khung đồng · trợ lý AI có camera', SUB)]
S += img('i-000.png', W, 'Mô hình 3D: khung đồng Ø1,6, 2 bánh xích N20, màn TFT làm mắt, ESP32-S3 trên nóc.')
S.append(Spacer(1, 12))
S.append(tbl(['Nội dung', 'Trang'], [['1. Dự án', os.environ.get('P1','?')], ['2. Chức năng', os.environ.get('P2','?')], ['3. Danh sách vật tư', os.environ.get('P3','?')],
    ['4. Sơ đồ nối dây và bảng chân', os.environ.get('P4','?')], ['5. Hướng dẫn lắp (khung đồng, thử module, lắp ráp)', os.environ.get('P5','?')],
    ['6. Kiểm tra cuối và an toàn', os.environ.get('P6','?')], ['7. Checklist tổng', os.environ.get('P7','?')], ['8. Firmware', os.environ.get('P8','?')]], [455, 60]))
S.append(Spacer(1, 8))
S.append(Paragraph('Bản đầy đủ ngày 24/11/2026. Lập theo đồ anh đã đặt trên Shopee. Thiết kế: khung đồng, 2 bánh xích N20, 1 màn TFT 1.8" (không dùng OLED 0.91", không làm vỏ Wall-E, không có trạm sạc: robot sạc bằng cáp USB-C cắm ở cửa sau). Chân GPIO là bản tạm theo board ESP32-S3 N16R8 có camera; khi có sơ đồ board của shop cần đối chiếu lại.', SM))
S.append(PageBreak())

# ---------------- 1. DỰ ÁN ----------------
S.append(Paragraph('1. Dự án', H1))
S.append(Paragraph('QBK-Robo là robot nhỏ chạy bánh xích, thân là khung đồng thau Ø1,6 mm hàn tay (dài 100 mm, rộng 64 mm, cao 74 mm phía trước, thấp dần về sau còn 54 mm). Bộ não là ESP32-S3 N16R8 có camera OV3660, kèm mic, ampli và loa để nói chuyện với AI qua WiFi. Màn TFT 1.8" ở mặt trước làm đôi mắt và hiện sóng âm khi robot nói.', P))
S.append(tbl(['Hạng mục', 'Thông số'], [
    ['Khung', '3 thanh đồng Ø1,6 × 1 m, uốn và hàn thiếc. Khung lộ ra ngoài, mọi linh kiện nằm bên trong.'],
    ['Di chuyển', '2 motor giảm tốc N20, driver MX1508, bộ bánh xích N20 trục dài (có bánh chủ động riêng). Quay tại chỗ bằng cách chạy 2 bên ngược chiều.'],
    ['Điều khiển', 'ESP32-S3 N16R8 (16MB flash, 8MB PSRAM), WiFi + Bluetooth, camera OV3660.'],
    ['Nguồn', '2 pin 18650 Beston 3300mAh mắc song song (≈ 6600mAh), mạch sạc USB-C tăng áp 5V, công tắc gạt.'],
    ['Kích thước thân', 'Dài 100 · rộng 64 (tâm 2 vòng hông) · cao 74 trước / 54 sau (mm), chưa tính xích.'],
    ['Sạc', 'Cắm cáp USB-C ở cửa sau. Không làm trạm sạc tự động.'],
], [110, 405], bold_first=True))
S.append(Paragraph('2. Chức năng', H1))
S.append(tbl(['Chức năng', 'Linh kiện', 'Mô tả'], [
    ['Nói chuyện AI', 'Mic INMP441, ampli MAX98357A, loa 3W', 'Nghe giọng anh, gửi lên AI qua WiFi, trả lời bằng giọng nói. Mic và ampli dùng chung xung nhịp I2S.'],
    ['Mắt và biểu cảm', 'TFT 1.8" ST7735', 'Hai mắt chớp, nhìn theo; mép dưới màn hiện sóng âm khi robot nói.'],
    ['Nhìn bằng camera', 'OV3660 trên board', 'Xem hình trực tiếp trên điện thoại, nhận diện vật hoặc người, chụp ảnh gửi AI hỏi.'],
    ['Di chuyển', '2 N20 + MX1508 + xích', 'Tiến, lùi, quay trái phải, điều khiển qua điện thoại hoặc bằng lời nói.'],
    ['Tránh vật cản', 'TOF050C (VL6180X)', 'Đo khoảng cách phía trước (khoảng 5–20 cm), tự dừng hoặc rẽ khi gặp vật.'],
    ['Nhiệt độ, độ ẩm', 'SHT31', 'Đọc nhiệt độ và độ ẩm phòng, báo khi được hỏi, dùng để tự bật điều hòa.'],
    ['Điều khiển điều hòa', 'Bộ IR thu + IR phát', 'Học lệnh từ remote máy lạnh, phát lại theo lời nói hoặc theo nhiệt độ.'],
    ['Vuốt đầu', 'Nút chạm TTP223', 'Chạm vào nóc: robot phản ứng, đánh thức hoặc tắt tiếng.'],
    ['Báo pin', 'Cầu chia 100k/100k → GPIO1', 'Đọc áp pin, báo khi pin yếu dưới khoảng 3,5 V.'],
    ['Đèn trang trí', '2 đèn LED Edison', 'Sáng ở đuôi nóc mỗi khi bật công tắc.'],
    ['Đèn thêm (chờ)', '2 đèn LED mua thêm', 'Chưa có trong sơ đồ. Khi hàng về biết loại đèn sẽ bổ sung cách nối (xem mục 7.2).'],
], [95, 130, 290], bold_first=True))
S.append(PageBreak())

# ---------------- 3. VẬT TƯ ----------------
S.append(Paragraph('3. Danh sách vật tư', H1))
S.append(Paragraph('3.1 Đồ đã đặt mua (giá đã trừ giảm giá)', H2))
buy = [['1', 'Combo phụ kiện chế tạo xe robot AI mini (ESP32 OV3660, màn màu 1.8")', 'AI Maker Shop', '1', '882.000đ'],
 ['2', 'Thanh đồng Benytro Ø1,6 mm × 100 cm', 'Benytro Official Store', '3', '159.585đ'],
 ['3', 'Bộ bánh xích cho xe robot AI – N20 trục dài', 'maybayrc', '1', '60.000đ'],
 ['4', 'Pin sạc Beston 18650 3300mAh ×2 + sạc đôi M7001', 'BESTON', '1 bộ', '233.200đ'],
 ['5', 'Đế pin 18650 2 pin song song', 'Bán Buôn Linh Kiện', '1', '17.916đ'],
 ['6', 'Cảm biến nhiệt độ, độ ẩm SHT31-D (mạch tím)', 'SAMIORE.vn', '1', '53.674đ'],
 ['7', 'Mô-đun IR thu + IR phát (bộ)', 'roarkit.vn', '1 bộ', '10.845đ'],
 ['8', 'Điện trở 100kΩ 1/4W', 'linhkien1993.com', '10 con', '9.000đ'],
 ['9', 'Tụ hóa 470µF 16V 6×12 mm', 'Linh Kiện Điện Tử Của Tôi 24H', '5 con', '15.399đ'],
 ['10', 'PCB đục lỗ 5×7 cm 2 mặt', 'Cơ Điện Tử ViNa', '2 tấm', '20.693đ'],
 ['11', 'Ống co nhiệt cắt sẵn', 'TOOLIX HARDWARE VN', '127 ống', '17.030đ'],
 ['12', 'Mỏ hàn chỉnh nhiệt 60–80W (bộ, màu đen)', 'Thế Giới Đồ Chơi', '1', '134.000đ'],
 ['13', 'Combo máy bắn keo nến 20W + 50 keo nến', 'Huy Tưởng Trading', '1', '90.070đ'],
 ['', '<b>Tổng cộng</b>', '', '', '<b>1.703.412đ</b>']]
S.append(tbl(['#', 'Món', 'Shop', 'SL', 'Thành tiền'], buy, [20, 235, 130, 50, 80]))
S.append(Paragraph('2 đèn LED mua thêm chưa có trong bảng vì chưa rõ loại và giá; bổ sung khi hàng về.', SM))
S.append(Paragraph('3.2 Trong combo robot AI (14 hạng mục)', H2))
S.append(tbl(['Nhóm', 'Linh kiện', 'Dùng trong robot'], [
    ['Điều khiển, hiển thị', 'ESP32-S3 N16R8 + camera OV3660; màn TFT 1.8" ST7735', 'Có'],
    ['Âm thanh', 'Mic INMP441; ampli MAX98357A; loa mini 3W 4Ω', 'Có'],
    ['Cảm biến', 'TOF050C (VL6180X); cảm biến chạm TTP223', 'Có'],
    ['Truyền động', '2 motor N20-1218; mạch điều khiển động cơ DC (MX1508)', 'Có'],
    ['Truyền động', '2 bánh răng kim loại 64T', 'Không: bộ xích N20 có bánh chủ động riêng. Giữ lại phòng khi bánh của bộ xích không vừa trục N20'],
    ['Truyền động', 'Bánh xe bi đa hướng', 'Không (đã có bánh xích)'],
    ['Nguồn, phụ kiện', 'Mạch sạc USB-C; 2 đèn LED Edison dạng ống; bộ dây kết nối', 'Có'],
], [100, 230, 185], bold_first=True))
S.append(Paragraph('3.3 Không cần mua thêm', H2))
S.append(Paragraph('Đồ đã đủ. Những thứ dưới đây dùng đồ có sẵn:', P))
S.append(bullets(['Công tắc gạt: anh có sẵn.',
 'Dây nối: bộ dây kết nối trong combo. Dây Dupont cái cắm thẳng vào chân ESP32, không cần header.',
 'Đế ESP32 và thanh nguồn: 2 tấm PCB 5×7 đã mua. Đế nóc cắt 70 × 30 mm, thanh nguồn 22 × 14 mm, phần dư gắn mic, IR, nút chạm.',
 'Điện trở 100k: cần 2 con cho cầu chia đo pin (mua 10). Tụ 470µF: cần 2 con cho MX1508 và ampli (mua 5).',
 'Hàn: bộ mỏ hàn 80W kèm thiếc. Keo nến để gắn module, ống co nhiệt bọc mối nối.',
 'Đồ trong nhà: kìm, thước, băng keo giấy, một lọ hoặc ống tròn Ø27 làm khuôn uốn.']))
S.append(PageBreak())

# ---------------- 4. SƠ ĐỒ ----------------
S.append(Paragraph('4. Sơ đồ nối dây', H1))
S.append(Paragraph('4.1 Sơ đồ nối dây (xoay ngang trang để xem)', H2))
S += img('i-001.png', 515 * 0.93)
S.append(PageBreak())
S.append(Paragraph('4.2 Vị trí các module trong khung (3D)', H2))
S += img('i-002.png', W, 'Sơ đồ nối dây 3D: nhìn chéo trước-trái và sau-phải. SHT31 đặt cạnh TOF050C ở mặt trước dưới.')
S.append(Spacer(1, 8))
t = Table([[Image(os.path.join(IMG, 'i-003.png'), width=300, height=187.5)], ], colWidths=[W]); t.setStyle(TableStyle([('ALIGN', (0, 0), (-1, -1), 'CENTER')])); S.append(t)
t = Table([[Image(os.path.join(IMG, 'i-004.png'), width=252, height=157.5), Image(os.path.join(IMG, 'i-005.png'), width=252, height=157.5)]], colWidths=[257.5, 257.5]); S.append(t)
S += [Spacer(1, 3), Paragraph('Mô hình mạch thật: trên là chéo trước; dưới trái là nhìn từ trên xuống, dưới phải là chéo sau.', CAPT)]
S.append(PageBreak())
S.append(Paragraph('4.3 Bảng chân', H2))
pins = [['ESP32-S3', '5V / GND', '5V / GND thanh nguồn', 'Đỏ / Đen'], ['ESP32-S3', 'GPIO1', 'Điểm giữa cầu chia 100k/100k', 'Trắng'],
 ['TFT 1.8" ST7735', 'SCK', 'GPIO21', 'Tím'], ['TFT 1.8" ST7735', 'MOSI (SDA)', 'GPIO47', 'Tím'], ['TFT 1.8" ST7735', 'DC (A0)', 'GPIO14', 'Tím'],
 ['TFT 1.8" ST7735', 'RST', 'EN (reset của board)', 'Trắng'], ['TFT 1.8" ST7735', 'CS', 'GND', 'Đen'], ['TFT 1.8" ST7735', 'VCC, BL', '3V3', 'Cam'], ['TFT 1.8" ST7735', 'GND', 'GND', 'Đen'],
 ['Mic INMP441', 'SCK', 'GPIO2', 'Xanh dương'], ['Mic INMP441', 'WS', 'GPIO42', 'Xanh dương'], ['Mic INMP441', 'SD', 'GPIO41', 'Xanh dương'],
 ['Mic INMP441', 'L/R', 'GND (kênh trái)', 'Đen'], ['Mic INMP441', 'VDD / GND', '3V3 / GND', 'Cam / Đen'],
 ['Ampli MAX98357A', 'BCLK', 'GPIO2 (chung mic)', 'Xanh dương'], ['Ampli MAX98357A', 'LRC', 'GPIO42 (chung mic)', 'Xanh dương'], ['Ampli MAX98357A', 'DIN', 'GPIO40', 'Xanh dương'],
 ['Ampli MAX98357A', 'VIN / GND', '5V / GND (tụ 470µF sát chân)', 'Đỏ / Đen'], ['Ampli MAX98357A', 'GAIN, SD', 'Để trống', ''], ['Ampli MAX98357A', '+/−', 'Loa 4Ω 3W (dây xoắn đôi)', 'Xám'],
 ['TOF050C', 'SDA / SCL', 'GPIO38 / GPIO39', 'Vàng / Xanh lá'], ['TOF050C', 'VIN / GND', '3V3 / GND', 'Cam / Đen'],
 ['SHT31', 'SDA / SCL', 'GPIO38 / GPIO39 (chung TOF)', 'Vàng / Xanh lá'], ['SHT31', 'VIN / GND', '3V3 / GND', 'Cam / Đen'],
 ['Nút chạm TTP223', 'I/O', 'GPIO3', 'Trắng'], ['Nút chạm TTP223', 'VCC / GND', '3V3 / GND', 'Cam / Đen'],
 ['IR thu', 'OUT', 'GPIO0', 'Trắng'], ['IR thu', 'VCC / GND', '3V3 / GND', 'Cam / Đen'], ['IR phát', 'SIG', 'GPIO20', 'Trắng'], ['IR phát', 'VCC / GND', '5V / GND', 'Đỏ / Đen'],
 ['MX1508', 'IN1 / IN2', 'GPIO45 / GPIO46 (motor trái)', 'Nâu'], ['MX1508', 'IN3 / IN4', 'GPIO19 / GPIO48 (motor phải)', 'Nâu'],
 ['MX1508', 'VCC / GND', '5V / GND (tụ 470µF sát chân)', 'Đỏ / Đen'], ['MX1508', 'MOTOR-A / MOTOR-B', 'N20 trái / N20 phải', 'Xám'],
 ['Đèn Edison ×2', '+/−', '3V3 hoặc 5V theo điện áp ghi trên đèn / GND', 'Đỏ / Đen'], ['Camera OV3660', 'cáp FPC', 'Đầu cắm camera trên board', '']]
S.append(tbl(['Module', 'Chân module', 'Nối tới', 'Màu dây'], pins, [115, 105, 205, 90]))
S.append(Spacer(1, 5))
S.append(note('Địa chỉ I2C', 'TOF050C 0x29, SHT31 0x44, không trùng nhau.'))
S.append(Spacer(1, 4))
S.append(note('Chân đặc biệt', 'GPIO19 (motor IN3) và GPIO20 (IR phát) là chân USB gốc nên luôn nạp code qua cổng USB-C “COM”. GPIO20 bị kéo lên mức cao lúc bật nguồn nên dành cho IR phát (đèn IR sáng thoáng qua, vô hại), không dùng cho motor. GPIO48 có đèn RGB trên board, đèn có thể nháy khi motor phải chạy. GPIO0, 45, 46 là chân khởi động: IR thu giữ mức cao lúc nghỉ; GPIO45 phải ở mức thấp lúc bật nguồn, MX1508 thường có trở kéo xuống. Kiểm ở bước B8: cắm MX1508 mà board không chạy thì hàn trở 10k từ GPIO45 xuống GND. Camera chiếm GPIO4–13, 15–18. TOF050C và SHT31 dùng cổng I2C 0, camera tự dùng cổng I2C 1. Board đã hết chân trống (GPIO43/44 là TX/RX của cổng nạp).', WARN))
S.append(Spacer(1, 4))
S.append(note('Nhiều dây chung 1 chân', 'Mỗi chân ESP32 chỉ cắm được 1 đầu Dupont. Các dây cùng nối 1 chân (3V3, GND, GPIO2, GPIO42) hàn nối chung thành 1 dây trước (nối chữ Y cách đầu cắm khoảng 3 cm), bọc co nhiệt, rồi mới cắm.'))
S.append(Paragraph('Mã màu dây', H3))
S.append(tbl(None, [['Đỏ · 5V sau công tắc, pin +', 'Tím · SPI màn TFT'], ['Cam · 3V3 từ ESP32', 'Xanh dương · I2S mic + ampli'], ['Đen · GND', 'Nâu · Điều khiển motor'],
    ['Vàng · I2C SDA', 'Trắng · Tín hiệu lẻ: nút, IR, đo pin'], ['Xanh lá · I2C SCL', 'Xám · Dây ra motor, ra loa']], [257.5, 257.5]))
S.append(PageBreak())

# ---------------- 5. HƯỚNG DẪN ----------------
S.append(Paragraph('5. Hướng dẫn lắp', H1))
S.append(Paragraph('Thứ tự cả quá trình: làm khung trước (phần A). Thử từng module bằng dây Dupont (phần B). Module nào chạy rồi mới hàn và lắp vào khung, từ dưới lên, từ trong ra ngoài (phần C). Mọi chiều cao tính từ tâm thanh đáy, khoảng cách dọc tính từ mặt trước.', P))
S.append(Paragraph('5.0 Dụng cụ', H2))
S.append(bullets(['Bộ mỏ hàn 80W đã mua (kèm thiếc), đặt 380–420°C khi hàn đồng. Thanh đồng hút nhiệt nhanh, để mỏ nóng hẳn rồi mới hàn.',
 'Súng keo nến, ống co nhiệt đã mua.', 'Đồ trong nhà: kìm cắt, kìm mỏ nhọn, thước, bút lông, băng keo giấy, một lọ hoặc ống tròn Ø27 làm khuôn uốn (bán kính tâm thanh ≈ 14 mm).',
 'Vài sợi đồng mảnh tước từ lõi dây điện mềm để quấn mối nối, buộc dây.', 'Đồng hồ vạn năng (nếu có) để đo áp và thông mạch.']))
S.append(Paragraph('5.1 Bảng cắt đồng Ø1,6 (3 thanh × 1 m)', H2))
S.append(tbl(['Thanh', 'Đoạn', 'Số', 'Dài (mm)', 'Ghi chú'], [
 ['1', 'Vòng hông', '2', '305', '304,3 + 0,7 giũa mối nối'], ['1', 'Ray nóc', '2', '70', 'chìa ra sau 8 mm để kẹp đèn'], ['1', 'Thanh giữa hông', '2', '98,4', 'lọt giữa mặt trước và mặt sau'],
 ['2', 'Thanh ngang', '8', '62,4', '2 đáy, 2 trước, 2 sau, 2 nóc'], ['2', 'Thanh khay đáy', '3', '80', 'đỡ đế pin'], ['2', 'Cột đứng', '6', '32,4', '4 cột kẹp motor, 2 cột bánh căng'],
 ['3', 'Viền TFT', '1', '200', 'chữ nhật 62×39, bo R3'], ['3', 'Thanh đứng cửa sau', '2', '23,4', 'giữ mạch sạc và công tắc'], ['3', 'Mắt trục', '6', '20', '1 vòng quanh đinh Ø3 + 2 chân'],
 ['3', 'Kẹp module, kẹp đèn', '1', '200', 'cắt dần khi cần'], ['3', 'Dự phòng', '–', '≈ 430', 'đủ làm lại 1 viền TFT hoặc vài đoạn hỏng'],
 ['', '<b>Tổng dùng</b>', '', '≈ 2.450', 'trên 3.000 mm, dư ≈ 550 mm (thanh 1 và 2 mỗi thanh dư khoảng 60 mm)']], [40, 120, 30, 60, 265]))
bend = tbl(['Từ', 'Đến', 'Đoạn'], [['0', '35,7', 'Thẳng · đáy, nửa trước'], ['35,7', '58,2', 'Cong · góc trước-dưới, góc trong 90°'], ['58,2', '100,4', 'Thẳng · mặt trước'],
 ['100,4', '125,7', 'Cong · góc trước-trên, góc trong 79°'], ['125,7', '198,5', 'Thẳng · nóc dốc'], ['198,5', '218,2', 'Cong · góc sau-trên, góc trong 101°'],
 ['218,2', '246,1', 'Thẳng · mặt sau'], ['246,1', '268,6', 'Cong · góc sau-dưới, góc trong 90°'], ['268,6', '304,3', 'Thẳng · đáy, nửa sau → mối nối']], [38, 38, 174])
coord = tbl(['Thanh', 'Vị trí'], [['Ngang đáy', 'cách mặt trước 16 · cách mặt sau 16'], ['Ngang trước', 'cao 16 · cao 55'], ['Ngang sau', 'cao 16 · cao 41'],
 ['Ngang nóc', 'cách mặt trước 19,6 · cách mặt sau 19,6'], ['Ray nóc', 'cách tâm ±15 · chìa ra sau 8'], ['Giữa hông', 'cao 34'], ['Khay đáy', 'tâm · ±22'],
 ['Cột kẹp motor', 'cách mặt trước 21 và 35'], ['Cột bánh căng', 'cách mặt trước 86'], ['Viền TFT', 'cạnh dưới cao 34'], ['Cửa sau', 'cách tâm ±20'], ['Tâm trục motor', 'cao ≈ 29 · cách mặt trước 28']], [75, 175])
two = Table([[[Paragraph('Vạch uốn vòng hông (đo từ 1 đầu đoạn 305)', H3), bend], [Paragraph('Tọa độ các thanh (mm)', H3), coord]]], colWidths=[257.5, 257.5])
two.setStyle(TableStyle([('VALIGN', (0, 0), (-1, -1), 'TOP'), ('LEFTPADDING', (0, 0), (-1, -1), 0), ('RIGHTPADDING', (0, 0), (-1, -1), 7)]))
S.append(two)
S.append(Spacer(1, 4))
S.append(Paragraph('Bản uốn khung tỉ lệ 1:1 để đặt vòng hông lên so: file <b>design/ban-uon-khung-1-1.pdf</b> (in đúng 100%, không co giãn).', SM))
S.append(CondPageBreak(200))

S.append(Paragraph('Phần A · Khung đồng', H2))
S += step('A1', 'Nắn thẳng và cắt đồng', 'Cắt 3 thanh 1 m thành các đoạn theo bảng 5.1.', None,
 ['Nắn thẳng: kẹp một đầu, kéo căng đầu kia, rồi lăn thanh dưới tấm gỗ phẳng vài lượt.', 'Lau sạch thanh. Chỗ nào xỉn thì chà bằng miếng rửa chén cứng, vì đồng xỉn rất khó ăn thiếc.',
  'Thanh 1: 2 vòng hông 305, 2 ray nóc 70, 2 thanh giữa hông 98,4 (tổng 947 mm).', 'Thanh 2: 8 thanh ngang 62,4, 3 thanh khay 80, 6 cột 32,4 (tổng 934 mm).',
  'Thanh 3: viền TFT 200, 2 thanh cửa sau 23,4. Phần còn lại (khoảng 750 mm) giữ nguyên, sau này cắt mắt trục (6 × 20) và kẹp (200), còn dư khoảng 430 mm.', 'Giũa phẳng hai đầu mỗi đoạn, dán băng keo ghi tên.'],
 ['8 thanh ngang dài bằng nhau: xếp sát nhau, chênh dưới 0,3 mm.', 'Mỗi đoạn có nhãn tên.'], ('Mẹo', 'Cắt thanh ngang dư khoảng 0,5 mm rồi giũa dần đến khi lọt khít giữa 2 vòng hông. Cắt thiếu thì phải bỏ.'))
S += step('A2', 'Uốn 2 vòng hông', 'Hai vòng hông là xương sống của khung: mặt trước 74 mm, mặt sau 54 mm, dài 100 mm.', '2 đoạn 305 mm; lọ tròn Ø27; bản in 1:1',
 ['Đánh dấu các vạch theo bảng vạch uốn: 35,7 · 58,2 · 100,4 · 125,7 · 198,5 · 218,2 · 246,1 · 268,6 mm.', 'Góc 1 (trước-dưới, vuông): ôm đoạn 35,7–58,2 quanh lọ tròn Ø27, ấn đều tay, không bẻ gập tại một điểm.',
  'Đặt lên bản in, chỉnh trùng nét rồi uốn góc 2 (trước-trên, góc trong 79°).', 'Uốn góc 3 (sau-trên, góc trong 101°) và góc 4 (sau-dưới, vuông).',
  'Hai đầu gặp nhau giữa đáy: giũa cho áp khít, quấn 5–6 vòng dây đồng mảnh, hàn kín.', 'Làm vòng thứ hai giống hệt, đặt chồng lên vòng đầu để so.'],
 ['Đặt lên bản in: lệch nét không quá 1 mm.', 'Hai vòng chồng lên nhau trùng khít, nằm phẳng không vênh.'], ('Mẹo', 'Uốn hơi quá một chút vì đồng bật lại. Mối nối giữa đáy sẽ bị khay pin che.'))
S += step('A3', 'Dựng 2 vòng song song, hàn 2 thanh ngang đáy', 'Hai thanh đáy giữ 2 vòng cách nhau 64 mm (tâm đến tâm).', '2 thanh ngang 62,4; 2 khối gá cao đúng 62,4 mm; băng keo giấy, ê-ke',
 ['Dựng 2 vòng song song, kê 2 khối gá ở giữa, dán băng keo giữ chặt.', 'Thanh đáy thứ nhất cách mũi trước 16 mm, thanh thứ hai cách đuôi 16 mm.', 'Hàn chấm cả 4 mối (ít thiếc), đo 2 đường chéo đáy, chỉnh cho bằng nhau rồi mới hàn đầy.'],
 ['Hai đường chéo chênh không quá 1 mm.', 'Khung đặt trên bàn không cập kênh.'], ('Cách hàn một mối', 'Áp mỏ 2–3 giây cho đồng nóng, đưa thiếc vào chỗ tiếp giáp (không vào mũi hàn). Thiếc tự chảy ôm quanh mối là đạt. Mối chữ T thì áp mỏ vào thanh vòng vì nó hút nhiệt nhiều hơn.'))
S += step('A4', 'Hàn 4 thanh ngang trước và sau', None, '4 thanh ngang 62,4',
 ['Mặt trước: thanh dưới cao 16 mm, thanh trên cao 55 mm.', 'Mặt sau: thanh dưới cao 16 mm, thanh trên cao 41 mm.', 'Hàn chấm cả 8 mối, kiểm tra vuông góc rồi hàn đầy.'],
 ['Nhìn thẳng từ trước: 2 vòng hông song song, trên và dưới đều cách 64 mm.'])
S += step('A5', 'Hàn 2 thanh ngang nóc và 2 ray nóc', 'Hai ray nóc đỡ đế cắm ESP32 và kẹp 2 đèn Edison.', '2 thanh ngang 62,4; 2 ray 70',
 ['Thanh ngang nóc trước trên cạnh dốc, cách mặt trước 19,6 mm (đo ngang); thanh nóc sau cách mặt sau 19,6 mm.', 'Đặt 2 ray lên 2 thanh ngang nóc, song song cạnh dốc, cách tâm 15 mm mỗi bên.', 'Đầu trước ray bằng thanh ngang trước, đầu sau chìa ra 8 mm. Hàn 4 mối.'],
 ['Đặt thử tấm PCB 70×30 lên 2 ray: nằm vừa, không cập kênh.'])
S += step('A6', 'Thanh giữa hông, khay đáy và cột đứng', 'Motor N20 kẹp giữa các cột đứng phía trước, đế pin nằm trên khay đáy.', '2 thanh 98,4; 3 thanh 80; 6 cột 32,4; 1 motor N20 để ướm',
 ['Thanh giữa hông: mỗi bên một thanh ở cao 34 mm, nối mặt trước với mặt sau.', 'Khay đáy: 3 thanh dọc đặt lên 2 thanh ngang đáy, một ở giữa, hai thanh cách tâm 22 mm.',
  'Cột kẹp motor: mỗi bên 2 cột từ thanh đáy lên thanh giữa hông, cách mặt trước 21 và 35 mm (hộp số N20 rộng 12 mm lọt giữa).', 'Cột bánh căng: mỗi bên 1 cột, cách mặt trước 86 mm.'],
 ['Ướm N20: hộp số lọt khít giữa 2 cột, trục thò ra ngoài khung.', 'Tâm trục motor cao khoảng 29 mm.'],
 ('Kiểm khi có bộ xích', 'Tọa độ trục, cột bánh căng ở trên tính theo bánh chủ động cỡ Ø40–66. Lắp thử bánh chủ động của bộ xích lên N20 trước khi hàn cột: nếu bánh nhỏ hơn nhiều, dời cột bánh căng cho xích vừa căng.'))
S += step('A7', 'Viền màn TFT và cửa sau', 'Viền đồng ôm màn ở mặt trước. Cửa sau giữ mạch sạc, cổng USB-C và công tắc.', 'đoạn 200 mm; 2 đoạn 23,4 mm; màn TFT để ướm',
 ['Đo mạch màn thật trước khi uốn. Viền TFT: uốn chữ nhật 62 × 39 mm (theo mạch 1.8" thường gặp), bo góc R3 quanh mũi kìm, mối nối giữa cạnh dưới.', 'Hàn viền vào mặt trước: cạnh dưới cao 34 mm, 2 cạnh bên áp vào thanh đứng trước của 2 vòng hông.', 'Cửa sau: 2 thanh 23,4 mm hàn đứng giữa 2 thanh ngang sau, cách tâm 20 mm mỗi bên.'],
 ['Ướm màn sau viền: viền ôm vừa mép module, không che vùng hiển thị.'])
S += step('A8', 'Mắt trục bánh căng và bánh đỡ', 'Làm khi đã có bộ xích để chỉnh bánh căng cho xích vừa căng.', 'phần đồng còn lại; đinh Ø3 làm khuôn; bộ bánh xích N20 (kèm trục, ốc)',
 ['Uốn 6 mắt tròn: quấn đồng 1 vòng quanh đinh Ø3, chừa 2 chân 6 mm. Nếu trục của bộ xích khác Ø3 thì đổi đinh khuôn cho vừa trục.', 'Lắp tạm bánh chủ động lên trục N20, quàng xích qua bánh căng, ướm vị trí cho xích căng vừa.',
  'Hàn mắt bánh căng vào cột bánh căng, cao khoảng 15 mm, lỗ quay ra ngoài.', 'Hàn 4 mắt bánh đỡ lên thanh đáy, cách mặt trước 48 và 66 mm, mỗi bên 2 mắt.'],
 ['Ấn giữa đoạn xích trên: võng 2–3 mm.', 'Bánh đỡ chạm nhẹ mặt trong đoạn xích dưới.'])
S += step('A9', 'Làm sạch và phủ bóng khung', 'Nhựa thông sót lại làm đồng xỉn xanh sau vài tuần.', None,
 ['Chà sạch nhựa thông bằng bàn chải cũ với nước rửa chén (có cồn thì dùng cồn), lau khô.', 'Đánh bóng khung bằng kem đánh răng.', 'Muốn giữ màu lâu: xịt 1 lớp PU bóng trong (che lỗ mắt trục trước khi xịt).'],
 ['Lắc mạnh khung: không mối nào lỏng.', 'Không còn vệt nhựa thông nâu.'])

S.append(CondPageBreak(120))
S.append(Paragraph('Phần B · Thử từng module bằng dây Dupont', H2))
S.append(Paragraph('Chưa hàn gì. Cắm dây Dupont trong combo theo bảng chân 4.3. Firmware thử phần cứng <b>firmware/bin/qbk-test.bin</b> tự kiểm từng module và báo lên màn TFT và cổng Serial (115200). Mỗi lần cắm thêm module, bấm RST để firmware kiểm lại.', P))
S.append(note('Nạp code an toàn', 'Board lấy 5V từ thanh nguồn, nên khi cắm cáp máy tính, cổng USB cũng cấp điện ngược ra MX1508, ampli, IR, đèn. Khi nạp code để công tắc TẮT và không cho motor chạy (cổng USB chỉ chịu khoảng 0,5 A). Muốn chạy thử motor thì bật công tắc dùng pin.', WARN))
S += step('B1', 'Nạp firmware thử phần cứng', None, 'cáp USB-C có truyền dữ liệu; máy tính có Chrome hoặc Edge',
 ['Cắm cáp vào cổng USB-C ghi COM.', 'Mở https://espressif.github.io/esptool-js/, bấm Connect, chọn cổng COM. Không kết nối được: giữ BOOT, bấm RST, nhả BOOT rồi thử lại.', 'Bấm Erase Flash. Xong ghi địa chỉ 0x0, chọn qbk-test.bin, bấm Program. Đợi xong thì bấm RST.'],
 ['Serial hiện “===== QBK-Robo TEST =====” và dòng “I2C scan”.'])
S += step('B2', 'Camera OV3660', None, None,
 ['Lật nắp khóa đầu cắm cáp dẹt, cắm cáp đúng chiều, đẩy hết vào rồi đóng nắp.', 'Bấm RST.'],
 ['Serial hiện “Camera: OK” kèm mã cảm biến. Báo LỖI: kiểm cáp; vẫn lỗi thì chụp Serial gửi em đối chiếu chân camera.'])
S += step('B3', 'Màn TFT 1.8"', 'Chân CS nối thẳng GND vì màn là thiết bị SPI duy nhất.', None,
 ['Cắm dây theo bảng chân 4.3.', 'Bấm RST.'],
 ['Màn hiện “QBK-Robo TEST” và các dòng trạng thái.', 'Dải màu dưới cùng: đỏ – xanh lá – xanh dương từ trái sang phải.', 'Chữ lật, ngược, lệch hoặc sai màu: chụp màn gửi em đổi cấu hình.'])
S += step('B4', 'Mic INMP441', None, None,
 ['Cắm dây theo bảng chân 4.3, bấm RST.'],
 ['Nói gần mic: thanh “Mic: ||||” dài ra; im lặng thì ngắn lại.'])
S += step('B5', 'Nút chạm, TOF050C và SHT31', 'TOF050C và SHT31 cùng nằm trên 2 dây I2C GPIO38/39.', None,
 ['Cắm dây theo bảng chân 4.3, bấm RST.'],
 ['Serial dòng “I2C scan” có 0x29 và 0x44.', 'Đưa tay lại gần TOF: số mm đổi; không có vật thì hiện “khong co vat”.', 'Hà hơi vào SHT31: độ ẩm tăng.', 'Chạm nút: dòng “Cham” chuyển sang CO.'])
S += step('B6', 'Ampli MAX98357A và loa', 'Mic và ampli dùng chung xung nhịp I2S (GPIO2, GPIO42), chỉ khác dây dữ liệu.', None,
 ['Cắm dây theo bảng chân 4.3, nối loa vào cọc + và − của ampli.', 'Bấm RST: loa kêu 1 tiếng bíp ngắn.', 'Chạm nút: loa kêu 3 tiếng bíp, sau đó firmware thử motor và IR phát.'],
 ['Loa nghe rõ, không rè (rè hoặc không tiếng: kiểm GND chung, dây DIN, BCLK, LRC).'])
S += step('B7', 'IR thu và IR phát (điều hòa)', None, None,
 ['Cắm dây theo bảng chân 4.3. IR phát dùng 5V để phát xa hơn.', 'Bấm remote máy lạnh vào mắt thu.', 'Chạm nút: cuối chuỗi thử, IR phát sáng 1 giây.'],
 ['Số “IR thu” trên màn tăng mỗi lần bấm remote.', 'Soi mắt IR phát bằng camera điện thoại: thấy đèn nháy tím.'])
S += step('B8', 'Motor N20 và MX1508', None, None,
 ['Cắm MX1508 vào GPIO45, 46, 19, 48 (chưa nối motor), bấm RST: board phải khởi động bình thường. Nếu không, hàn trở 10k từ GPIO45 xuống GND.', 'Tụ 470µF cắm sát chân + và − của MX1508 (chân dài là +). Tạm lấy 5V từ chân 5V của board.', 'Nối motor, kê lên cho khỏi chạy. Chạm nút: motor trái tiến, lùi rồi motor phải tiến, lùi (màn ghi đang thử motor nào).'],
 ['Từng motor quay đúng như màn ghi; motor nào ngược thì đảo 2 dây của nó.', 'Board tự khởi động lại khi motor chạy: sang bước B9 rồi thử lại.'])
S += step('B9', 'Nguồn pin, mạch sạc và chạy tất cả', 'Hai pin 18650 song song → mạch sạc tăng áp 5V → công tắc → cả robot.', None,
 ['Sạc cả 2 pin trên sạc đôi Beston đến khi cả 2 báo đầy, rồi mới lắp vào đế song song (có đồng hồ thì đo, chênh dưới 0,05 V).', 'Nối dây đế pin vào B+ và B− của mạch sạc, ngõ ra OUT+ qua công tắc.',
  'Ráp cầu chia 100k/100k, điểm giữa vào GPIO1.', 'Rút cáp máy tính, bật công tắc chạy bằng pin, chạm nút chạy lại chuỗi thử.'],
 ['Dòng “Pin” trên màn trong khoảng 3,6–4,2 V.', 'Motor chạy mà board không tự khởi động lại.', 'Cắm USB-C vào mạch sạc: đèn sạc sáng.'],
 ('An toàn pin', 'Không hàn lên thân pin. Không để 2 dây pin chạm nhau. Hai pin lệch áp mà nối song song sẽ xả vào nhau rất mạnh.', WARN))

S.append(CondPageBreak(120))
S.append(Paragraph('Phần C · Lắp ráp vào khung', H2))
S.append(Paragraph('Từ dưới lên, từ trong ra ngoài. Hàn dây vào linh kiện trước rồi mới gắn vào khung, vì trong khung mỏ hàn rất khó với tới.', P))
S += step('C1', 'Đế pin vào khay đáy', None, None,
 ['Dùng sẵn dây đỏ (+), đen (−) của đế pin, cắt còn khoảng 60 mm.', 'Đặt đế lên khay đáy, đầu có dây quay ra sau. Buộc 2 chỗ bằng dây đồng mảnh hoặc chấm keo nến. Chưa lắp pin.'],
 ['Đế không xê dịch khi lắc khung; dây không vướng chỗ đặt motor.'])
S += step('C2', 'Mạch sạc, cổng USB-C và công tắc ở cửa sau', None, None,
 ['Gắn mạch sạc lên 2 thanh cửa sau (keo nến 4 góc hoặc buộc dây đồng), cổng USB-C hướng ra ngoài.', 'Kẹp công tắc gạt vào thanh đứng bên phải cửa sau.', 'Hàn dây đế pin vào B+ và B− của mạch sạc.'],
 ['Cắm được cáp USB-C từ phía sau; gạt công tắc dễ.'])
S += step('C3', 'Thanh nguồn chia 5V và GND', 'Mọi dây nguồn đi ra từ một điểm.', None,
 ['Cắt PCB lỗ 22 × 14 mm, hàn dải 5V (trên) và dải GND (dưới).', 'Hàn cầu chia ngay trên thanh: pin + → 100k → điểm giữa → 100k → GND; từ điểm giữa ra 1 dây trắng.',
  'Gắn thanh nguồn lên vách trái, phía sau, sát đế pin.', 'Nối: OUT+ mạch sạc → công tắc → dải 5V; OUT− → dải GND; một dây đỏ mảnh từ pin + sang đầu trên cầu chia.'],
 ['Đo thông mạch dải 5V – GND trước khi lắp pin: không chập.', 'Lắp pin tạm, bật công tắc: board sáng đèn; tắt: board tắt. Xong tháo pin ra.'],
 ('Lưu ý', 'Cầu chia nối thẳng pin + nên luôn hao khoảng 18 µA kể cả khi tắt công tắc, không đáng kể. Cất robot trên 2 tháng thì tháo pin ra.'))
S += step('C4', 'Motor N20 và MX1508', None, None,
 ['Hàn dây xám dài 70 mm vào 2 cọc mỗi motor, xoắn đôi.', 'Đặt hộp số vào giữa 2 cột kẹp, trục ra ngoài, quấn 3 vòng dây đồng mảnh qua thanh giữa hông.',
  'Dán MX1508 lên vách trái phía trên thanh nguồn, hàn tụ 470µF thẳng vào chân + và −.', 'Hàn 4 dây nâu vào IN1–IN4, dài 120 mm, luồn lên nóc. Chưa nối ESP32.'],
 ['Không chân nào chạm khung đồng.', 'Trục 2 motor thẳng hàng.'])
S += step('C5', 'Ampli và loa ở vách phải', None, None,
 ['Dán MAX98357A lên vách phải phía dưới, hàn tụ 470µF vào VIN và GND.', 'Dán loa lên vách phải phía trên, mặt loa ra ngoài.', 'Dây nguồn ampli đi vòng phía sau, trên đầu đế pin.', 'Hàn 3 dây xanh dương vào BCLK, LRC, DIN, dài 120 mm, luồn lên nóc. Dây loa xoắn đôi, ngắn.'],
 ['Loa không chạm motor phải; dây nguồn đi sát thanh đồng.'])
S += step('C6', 'Mặt trước: TFT, TOF050C và SHT31', None, None,
 ['Hàn dây dài 150 mm vào chân TFT, TOF050C và SHT31 trước khi gắn.', 'Nối song song I2C ngay tại chân TOF050C: dây vàng, xanh lá rẽ sang SHT31.',
  'Dán TOF050C dưới thanh ngang trước dưới, mắt nhìn thẳng ra trước. Dán SHT31 bên cạnh, lệch trái, lỗ cảm biến thoáng.', 'Gắn TFT vào viền: chấm keo nến 4 góc phía sau module, không để keo dính mặt kính.'],
 ['Màn không nghiêng, khe hở quanh viền đều.', 'Mắt TOF050C không bị thanh đồng che.'],
 ('Lưu ý SHT31', 'Để SHT31 xa ampli, MX1508 và mạch sạc vì các mạch này ấm lên, làm số nhiệt độ cao hơn thực tế.'))
S += step('C7', 'Đế ESP32 trên nóc', 'Board nằm trên tấm PCB lỗ, dây Dupont cái cắm thẳng vào chân board nên rút ra được khi sửa.', None,
 ['Cắt PCB lỗ 70 × 30 mm.', 'Đặt board lên PCB, chấm keo nến 4 góc hoặc buộc dây đồng mảnh qua lỗ PCB. Chân board chĩa xuống thì khoan/khoét rãnh cho chân lọt.',
  'Bắt PCB lên 2 ray nóc bằng 4 vòng dây đồng mảnh.', 'Kéo 3 dây Dupont từ thanh nguồn lên: đỏ cắm 5V, đen cắm GND, trắng (cầu chia) cắm GPIO1.', 'Cổng USB-C quay ra sau.'],
 ['Board không xê dịch; cắm được cáp USB-C khi board nằm trên nóc.'])
S += step('C8', 'Cắm các bó dây vào ESP32', 'Làm từng bó, xong bó nào soát bó đó.', None,
 ['Dây cùng nối 1 chân (3V3, GND, GPIO2, GPIO42) hàn nối chữ Y thành 1 dây trước, bọc co nhiệt, rồi mới cắm đầu Dupont.', 'Bó motor (4 nâu): đầu Dupont cái cắm vào GPIO45, 46, 19, 48.', 'Bó I2S (3 xanh dương): GPIO2, 42, 40; SCK, WS của mic nối chữ Y vào 2 dây BCLK, LRC.', 'Bó trước, nhánh TFT: 3 tím vào GPIO21, 47, 14; trắng RST vào EN; cam vào 3V3; đen vào GND.',
  'Bó trước, nhánh I2C (vàng, xanh lá, cam, đen): GPIO38, 39, 3V3, GND.', 'Mỗi bó bọc co nhiệt 5 mm cách nhau 20 mm, buộc vào thanh đồng bằng 2 vòng dây đồng mảnh.'],
 ['Soát từng dây cắm đúng chân theo bảng 4.3.', 'Nạp lại qbk-test.bin (công tắc tắt khi nạp), chạy lại như phần B: màn, TOF, SHT31, loa, motor đều OK.'])
S += step('C9', 'Module trên nóc: camera, mic, IR, nút chạm', None, None,
 ['Cắm cáp dẹt camera, dán camera ở mép trước nóc, ống kính ló ra trước.', 'Mỗi module nhỏ gắn trên một mẩu PCB lỗ, bắc từ ray nóc sang thanh hông: IR phát trước-trái (LED hướng ra trước), mic trước-phải, IR thu sau-trái, nút chạm sau-phải.', 'Dây đi sát mặt PCB, đầu Dupont cắm vào chân board.'],
 ['Camera, mic, IR thu, nút chạm đều báo OK trên qbk-test.'])
S += step('C10', 'Hai đèn Edison ở cuối nóc', None, None,
 ['Xem điện áp ghi trên đèn hoặc trang shop: đèn 3V nối + vào 3V3, đèn 5V nối + vào dải 5V. Đầu − về GND. Không rõ điện áp thì thử bằng 3V3 trước.', 'Uốn 4 kẹp chữ U nhỏ, hàn lên đầu sau 2 ray nóc, kẹp 2 ống đèn nằm ngang.'],
 ['Hai đèn sáng đều; sau 5 phút đèn không nóng tay.'],
 ('Lưu ý', 'Đèn ghi 3V mà không có mạch hạn dòng thì không nối thẳng 5V, dễ cháy. Sáng yếu ở 3V3 thì hỏi em tính trở trước khi chuyển sang 5V.', WARN))
S += step('C11', 'Lắp bánh xích', None, None,
 ['Lắp bánh chủ động của bộ xích lên trục chữ D của N20 (trục dài), nhỏ một giọt keo.', 'Xỏ trục/ốc của bộ xích qua mắt bánh căng và bánh đỡ, lắp bánh, siết 2 đai ốc chặn nhau để bánh quay trơn mà không lỏng.', 'Lắp xích, kiểm tra độ căng (võng 2–3 mm).'],
 ['Robot chạy thẳng trên sàn.', 'Quay tại chỗ không tuột xích.'])

S.append(CondPageBreak(150))
S.append(Paragraph('6. Kiểm tra cuối và an toàn', H1))
S.append(Paragraph('<a name="sec6"/>', SM))
S += step('C12', 'Lắp pin, chạy thử toàn bộ', None, None,
 ['Lắp 2 pin đã sạc đầy, đúng cực, bật công tắc.', 'Nạp firmware chính (mục 8), thử từng chức năng: nói chuyện, màn, camera, khoảng cách, nhiệt độ, học và phát lệnh máy lạnh, nhảy, nhạc.', 'Thử sạc USB-C khi công tắc tắt và khi bật.'],
 ['Mọi chức năng chạy.', 'Sau 15 phút không có gì nóng bất thường; MX1508, ampli, mạch sạc chỉ ấm.'])
S += step('C13', 'Soát lại và hoàn thiện', None, None, [],
 ['Không mối hàn trần nào chạm khung đồng; mọi mối nối dây đã bọc co nhiệt.', 'Không dây nào gần bánh răng; bó dây cách xích ít nhất 5 mm.', 'Dây thừa xếp gọn theo thanh đồng, không thắt nút.'])
S.append(Spacer(1, 4))
S.append(note('An toàn', '• Khung đồng dẫn điện: mọi mối hàn trần phải bọc co nhiệt, không để chạm khung.<br/>• Không hàn trực tiếp lên thân pin 18650. Tháo pin ra khi hàn trong khung.<br/>• Không sạc khi robot đang bị kẹt bánh hoặc có mùi khét. Không để robot sạc qua đêm khi không có người.<br/>• Mỏ hàn 80W rất nóng: luôn đặt lên giá, rút điện khi xong. Hàn ở chỗ thoáng vì khói nhựa thông.', WARN))

# ---------------- 7. CHECKLIST ----------------
S.append(PageBreak())
S.append(Paragraph('7. Checklist tổng', H1))
S.append(Paragraph('Đánh dấu □ khi xong từng mục.', P))
S.append(Paragraph('7.1 Đồ dùng trong robot', H2))
S.append(tbl(['', 'Món', 'Tình trạng'], [[B, a, b] for a, b in [
    ('ESP32-S3 N16R8 + camera OV3660', 'Có trong combo'), ('Màn TFT 1.8" ST7735 (mắt + sóng âm)', 'Có trong combo'), ('Mic INMP441, ampli MAX98357A, loa 3W 4Ω', 'Có trong combo'),
    ('TOF050C (VL6180X), nút chạm TTP223', 'Có trong combo'), ('2 motor N20, mạch MX1508', 'Có trong combo'), ('Bộ bánh xích N20 trục dài', 'Đã đặt (maybayrc)'),
    ('Mạch sạc USB-C tăng áp 5V, 2 đèn Edison, dây Dupont', 'Có trong combo'), ('2 pin Beston 18650 3300mAh + sạc đôi, đế pin song song', 'Đã đặt'),
    ('SHT31-D mạch tím (nhiệt độ, độ ẩm)', 'Đã đặt (SAMIORE)'), ('Bộ IR thu + IR phát', 'Đã đặt (roarkit)'), ('3 thanh đồng Ø1,6 × 1 m', 'Đã đặt'),
    ('Trở 100k ×10, tụ 470µF ×5, PCB lỗ 5×7 ×2, ống co nhiệt', 'Đã đặt'), ('Mỏ hàn 80W kèm thiếc, súng keo nến', 'Đã đặt'), ('Công tắc gạt', 'Anh có sẵn'),
    ('2 đèn LED mua thêm', 'Chờ hàng về để biết loại (LED thường hay WS2812)')]], [16, 300, 199]))
S.append(Spacer(1, 4))
S.append(Paragraph('<font name="DVB">Không dùng:</font> bi đa hướng, 2 bánh răng kim loại 64T (giữ lại dự phòng), OLED 0.91", các đồ của phương án vỏ Wall-E.', P))
S.append(Paragraph('7.2 Việc còn chờ', H2))
S.append(tbl(['Việc', 'Khi nào', 'Ảnh hưởng tới'], [
    ['Đối chiếu chân GPIO với sơ đồ board của shop', 'Khi có sơ đồ', 'Bảng 4.3, bước C7–C9'],
    ['Cách nối 2 đèn LED mua thêm (board đã hết chân trống: LED thường nối 5V qua trở; WS2812 cần dồn lại chân)', 'Khi hàng về', 'Bảng 4.3, bước C10'],
    ['Đo bánh chủ động bộ xích, chỉnh vị trí cột bánh căng nếu cần', 'Khi có bộ xích', 'Bước A6, A8'],
    ['Đo mạch màn TFT thật, chỉnh kích thước viền', 'Khi hàng về', 'Bước A7'],
    ['Chỉnh firmware theo board thật (hướng màn, chiều motor) nếu cần', 'Sau khi nạp thử', 'Mục 8'],
], [270, 90, 155]))
S.append(KeepTogether([Paragraph('7.3 Khi hàng về: chụp ảnh gửi em', H2), tbl(['', 'Việc', 'Ghi chú'], [[B, a, b] for a, b in [
    ('Sơ đồ nối dây của shop cho board OV3660', 'Đối chiếu bảng chân 4.3'), ('ESP32-S3 cả 2 mặt, rõ chữ in 2 hàng chân', 'Xác nhận thứ tự chân'),
    ('Mạch sạc 2 mặt, rõ chữ B+, B−, OUT', 'Xác nhận chỗ hàn dây pin và dây ra'), ('MX1508, MAX98357A, INMP441, TOF050C, TTP223, SHT31, TFT, 2 module IR', 'Xác nhận tên và thứ tự chân'),
    ('2 đèn Edison và 2 đèn LED mới (chân, chữ in)', 'Biết điện áp và loại đèn'), ('Motor N20, bộ bánh xích (bánh chủ động, bánh căng, trục)', 'Kiểm bánh chủ động vừa trục chữ D'),
    ('Đo bằng thước: màn TFT (dài × rộng mạch), bánh chủ động (đường kính)', 'Chỉnh viền TFT và vị trí trục nếu lệch')]], [16, 280, 219])]))
S.append(KeepTogether([Paragraph('7.4 Trước khi cấp điện lần đầu', H2), tbl(['', 'Việc', 'Ghi chú'], [[B, a, b] for a, b in [
    ('2 pin sạc đầy trên sạc đôi, chênh dưới 0,05 V', 'Lệch áp mà nối song song sẽ xả vào nhau'), ('Đo thông mạch dải 5V – GND (chưa lắp pin): không chập', 'Kêu bíp là có chạm, tìm ra trước'),
    ('Pin đúng cực; dây đỏ + đen − đúng B+ B− mạch sạc', ''), ('Tụ 470µF đúng cực (chân dài là +, vạch trắng là −)', 'Tụ ngược cực có thể phồng nổ'),
    ('Bật công tắc, dải 5V đo 5,0–5,2 V; tắt: 0 V', ''), ('Không mối hàn trần nào chạm khung đồng', 'Khung đồng dẫn điện'),
    ('Board khởi động bình thường khi đã cắm MX1508 (GPIO45)', 'Không chạy: trở 10k GPIO45 → GND'), ('I2C Scanner thấy 0x29 (TOF050C) và 0x44 (SHT31)', '')]], [16, 280, 219])]))
S.append(KeepTogether([Paragraph('7.5 Theo dõi tiến độ', H2), tbl(['', 'Phần', 'Các bước (xem mục 5)'], [[B] + r for r in [
    ['A · Khung đồng', 'A1 cắt · A2 vòng hông · A3 đáy · A4 trước/sau · A5 nóc · A6 hông, khay, cột · A7 viền TFT, cửa sau · A8 mắt trục · A9 làm sạch'],
    ['B · Thử module', 'B1 nạp qbk-test · B2 camera · B3 TFT · B4 mic · B5 chạm, TOF, SHT31 · B6 ampli, loa · B7 IR · B8 motor · B9 pin, chạy tất cả'],
    ['C · Lắp ráp', 'C1 đế pin · C2 sạc, công tắc · C3 thanh nguồn · C4 motor, MX1508 · C5 ampli, loa · C6 mặt trước · C7 đế ESP32 · C8 bó dây · C9 nóc · C10 Edison · C11 xích · C12 chạy thử · C13 soát lại'],
    ['D · Phần mềm', 'Nạp qbk-robo-xiaozhi-vi.bin (mục 8) · cài WiFi · gắn robot vào xiaozhi.me · thử nói chuyện · học lệnh máy lạnh · nhảy, nhạc']]], [16, 90, 409])]))

# ---------------- 8. FIRMWARE ----------------
S.append(PageBreak())
S.append(Paragraph('8. Firmware', H1))
S.append(Paragraph('Hai file trong thư mục <b>firmware/bin/</b> của repo, đều nạp ở địa chỉ <b>0x0</b>. Mã nguồn, cách biên dịch lại và ghi chú chi tiết ở <b>firmware/README.md</b>.', P))
S.append(tbl(['File', 'Dùng khi nào'], [
    ['qbk-test.bin', 'Phần B: thử từng module. Màn hiện trạng thái từng module; chạm nút để thử loa, motor, IR phát.'],
    ['qbk-robo-xiaozhi-vi.bin', 'Robot hoàn chỉnh: trợ lý AI Xiaozhi, giao diện tiếng Việt.'],
], [130, 385], bold_first=True))
S.append(Paragraph('8.1 Cách nạp', H2))
S.append(numbered(['Gạt công tắc robot sang TẮT. Cắm cáp USB-C (loại truyền dữ liệu) vào cổng COM của board.',
 'Mở https://espressif.github.io/esptool-js/ bằng Chrome hoặc Edge, baudrate 921600, bấm Connect, chọn cổng COM. Không thấy cổng: cài driver chip USB của board (CH340 hoặc CH343).',
 'Lần đầu nạp: bấm Erase Flash.', 'Flash Address ghi 0x0, chọn file .bin, bấm Program, đợi 1–3 phút. Xong bấm RST.']))
S.append(Paragraph('8.2 Lần đầu bật firmware chính', H2))
S.append(numbered(['Điện thoại vào mạng WiFi “Xiaozhi-xxxx” do robot phát, trang cài đặt tự mở (hoặc vào 192.168.4.1), chọn WiFi nhà 2.4 GHz, nhập mật khẩu.',
 'Robot đọc mã 6 số: vào xiaozhi.me, thêm thiết bị bằng mã đó, chọn giọng nói, tính cách, tên gọi.',
 'Nói “Hi ESP” hoặc chạm vào đầu robot để nói chuyện; chạm lần nữa để dừng. Giữ nút chạm 5 giây: cài lại WiFi.']))
S.append(Paragraph('8.3 Có thể nói với robot', H2))
S.append(tbl(['Nói', 'Robot làm'], [
    ['“Đi tới 2 giây”, “lùi lại”, “quay trái”, “dừng lại”', 'Chạy bánh xích. Đang tiến gặp vật cản dưới 8 cm thì tự dừng.'],
    ['“Phía trước có gì gần không?”', 'Đo bằng TOF050C (tầm khoảng 20 cm).'],
    ['“Phòng đang bao nhiêu độ?”', 'Đọc nhiệt độ, độ ẩm từ SHT31.'],
    ['“Học lệnh bật máy lạnh”, rồi bấm remote vào nóc robot trong 12 giây', 'Học lệnh IR, lưu theo tên (bật, tắt, 26 độ…). Học xong kêu “ting”, hiện chữ trên màn. Lưu ở vùng nhớ riêng 128 KB.'],
    ['“Bật máy lạnh”, “chỉnh 26 độ”, “tắt máy lạnh”', 'Phát lệnh đã học.'],
    ['“Nhảy đi”, “nhảy kiểu robot”, “vừa hát vừa nhảy”', '5 điệu nhảy: lắc lư, xoay vòng, tiến lùi, kiểu robot, vui vẻ.'],
    ['“Mở nhạc”, “hát mừng sinh nhật”, “biểu diễn đi”', '5 bài có sẵn: Chúc mừng sinh nhật, Kìa con bướm vàng, Ngôi sao lấp lánh, Jingle Bells, Nhạc nhảy QBK; robot nhảy theo.'],
    ['“Chụp ảnh xem trước mặt có gì”', 'Camera chụp, AI mô tả.'],
], [215, 300]))
S.append(Paragraph('Chạm vào đầu robot khi đang nhảy hoặc phát nhạc để dừng.', SM))
S.append(Paragraph('8.4 Chỉnh khi chạy thật', H2))
S.append(Paragraph('Có thể phải chỉnh sau khi nạp thử (trong firmware/xiaozhi-board/qbk-robo/config.h): hướng xoay và độ lệch màn, chiều quay motor, khoảng dừng vật cản. Gửi em ảnh màn hoặc mô tả, em sửa và biên dịch lại.', P))

# --- số trang mục 6, 7 ---
PAGES = {}
class Doc(BaseDocTemplate):
    def afterFlowable(self, f):
        if isinstance(f, Paragraph) and f.style is H1:
            t = f.getPlainText()
            for k in ('1.','2.','3.','4.','5.','6.', '7.', '8.'):
                if t.startswith(k) and k not in PAGES: PAGES[k] = self.page

def footer(c, doc):
    if doc.page == 1: return
    c.saveState(); c.setStrokeColor(LINE); c.setLineWidth(0.5); c.line(40, 30, 555, 30)
    c.setFont('DV', 7); c.setFillColor(MUTED)
    c.drawString(40, 18, 'QBK-Robo · hồ sơ dự án, vật tư, sơ đồ, hướng dẫn lắp'); c.drawRightString(555, 18, str(doc.page)); c.restoreState()

doc = Doc(OUT, pagesize=A4, leftMargin=40, rightMargin=40, topMargin=40, bottomMargin=46, title='QBK-Robo – Hồ sơ dự án', author='QBK')
doc.addPageTemplates([PageTemplate(frames=[Frame(40, 46, W, A4[1] - 86, leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0)], onPage=footer)])
doc.build(S)
print(' '.join(str(PAGES.get(k)) for k in ('1.','2.','3.','4.','5.','6.','7.','8.')))
