import sys, os
from reportlab.lib.pagesizes import A4, landscape
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib import colors
from reportlab.platypus import (BaseDocTemplate, PageTemplate, Frame, Paragraph, Spacer, Table, TableStyle,
                                KeepTogether, Image, PageBreak, ListFlowable, ListItem, NextPageTemplate)

OUT, SCHEM = sys.argv[1], sys.argv[2]
pdfmetrics.registerFont(TTFont('DV', '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'))
pdfmetrics.registerFont(TTFont('DVB', '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'))
INK = colors.HexColor('#1f2430'); BODY = colors.HexColor('#2a2f36'); MUTED = colors.HexColor('#5d6670')
ACC = colors.HexColor('#b8621f'); LINE = colors.HexColor('#d6dbe3'); HEAD = colors.HexColor('#f3f1ec'); ALT = colors.HexColor('#f8f9fc')
WARN = colors.HexColor('#b4541f'); OK = colors.HexColor('#2f8f5b'); MISS = colors.HexColor('#c0392b'); SUB = colors.HexColor('#2f6fdc')
W = 515

TITLE = ParagraphStyle('t', fontName='DVB', fontSize=24, leading=30, textColor=INK)
SUBT = ParagraphStyle('s', fontName='DVB', fontSize=13, leading=18, textColor=ACC, spaceAfter=6)
H1 = ParagraphStyle('h1', fontName='DVB', fontSize=17, leading=22, textColor=INK, spaceBefore=6, spaceAfter=6)
H2 = ParagraphStyle('h2', fontName='DVB', fontSize=12, leading=16, textColor=ACC, spaceBefore=10, spaceAfter=4)
P = ParagraphStyle('p', fontName='DV', fontSize=9.2, leading=13, textColor=BODY, spaceAfter=4)
SM = ParagraphStyle('sm', parent=P, fontSize=8, leading=11, textColor=MUTED)
CAPT = ParagraphStyle('cap', parent=SM, alignment=1)
CELL = ParagraphStyle('c', fontName='DV', fontSize=8.3, leading=11, textColor=BODY)
CELLB = ParagraphStyle('cb', parent=CELL, fontName='DVB')
TH = ParagraphStyle('th', parent=CELL, fontName='DVB', fontSize=8, textColor=INK)
NOTE = ParagraphStyle('n', parent=P, fontSize=8.6, leading=12)
BIG = ParagraphStyle('big', fontName='DVB', fontSize=22, leading=26, textColor=INK, alignment=1)
BIGL = ParagraphStyle('bigl', fontName='DV', fontSize=8.5, leading=11, textColor=MUTED, alignment=1)

def tag(text, col):
    return f'<font name="DVB" color="{col.hexval()}">{text}</font>'
HAVE = tag('Có', OK); SWAP = tag('Thay được', SUB); NEED = tag('Thiếu', MISS); OPT = tag('Tùy chọn', MUTED); NOUSE = tag('Không dùng', MUTED)

def tbl(head, rows, widths, bold_first=False):
    data = [[Paragraph(h, TH) for h in head]]
    for r in rows:
        data.append([Paragraph(str(c), CELLB if (bold_first and i == 0) else CELL) for i, c in enumerate(r)])
    t = Table(data, colWidths=widths, repeatRows=1)
    st = [('BACKGROUND', (0, 0), (-1, 0), HEAD), ('GRID', (0, 0), (-1, -1), 0.5, LINE), ('VALIGN', (0, 0), (-1, -1), 'TOP'),
          ('TOPPADDING', (0, 0), (-1, -1), 3), ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
          ('LEFTPADDING', (0, 0), (-1, -1), 4), ('RIGHTPADDING', (0, 0), (-1, -1), 4)]
    for i in range(2, len(data), 2): st.append(('BACKGROUND', (0, i), (-1, i), ALT))
    t.setStyle(TableStyle(st)); return t

def note(title, text, color=ACC):
    t = Table([[Paragraph(f'<font name="DVB" color="{color.hexval()}">{title}.</font> {text}', NOTE)]], colWidths=[W])
    t.setStyle(TableStyle([('LINEBEFORE', (0, 0), (0, 0), 2.5, color), ('BACKGROUND', (0, 0), (-1, -1), ALT),
                           ('LEFTPADDING', (0, 0), (-1, -1), 8), ('TOPPADDING', (0, 0), (-1, -1), 5), ('BOTTOMPADDING', (0, 0), (-1, -1), 5)]))
    return t

def numbered(items):
    return ListFlowable([ListItem(Paragraph(x, P), leftIndent=14) for x in items], bulletType='1', leftIndent=14,
                        bulletFontName='DVB', bulletFontSize=8.6, bulletColor=ACC, bulletFormat='%s.')

B = '□'
S = []
# ---------------- TRANG 1 ----------------
S += [Paragraph('QBK-Robo theo sơ đồ DB-Wall-E Big', TITLE),
      Paragraph('Đối chiếu đồ đã mua với sơ đồ: còn thiếu gì, khác ở đâu, xử lý thế nào', SUBT)]
S.append(Paragraph('Sơ đồ gốc: “SƠ ĐỒ DB-WALL-E BIG ESP32-S3”, thiết kế bởi @hoanganhsell (DB-Robot), firmware online tại home.ledienbien.edu.vn/firmware.html. Bản đối chiếu ngày 25/11/2026, lập theo đồ anh đã đặt trên Shopee.', SM))
S.append(Spacer(1, 8))
kpi = Table([[Paragraph('7', BIG), Paragraph('5', BIG), Paragraph('7', BIG)],
             [Paragraph('món đã có, dùng giống sơ đồ', BIGL), Paragraph('món dùng đồ khác thay được', BIGL), Paragraph('món còn thiếu (6 bắt buộc + vỏ)', BIGL)]],
            colWidths=[W / 3] * 3)
kpi.setStyle(TableStyle([('BOX', (0, 0), (-1, -1), 0.5, LINE), ('INNERGRID', (0, 0), (-1, -1), 0, colors.white),
                         ('LINEAFTER', (0, 0), (1, 1), 0.5, LINE), ('BACKGROUND', (0, 0), (-1, -1), ALT),
                         ('TOPPADDING', (0, 0), (-1, 0), 8), ('BOTTOMPADDING', (0, 1), (-1, 1), 8)]))
S.append(kpi)
S.append(Spacer(1, 10))
S.append(note('Tóm lại', 'Board ESP32-S3 N16R8 của anh dùng được cho sơ đồ này: <b>rút camera ra</b> là trống đủ chân. '
              'Phải mua thêm <b>5 servo</b> (2 servo 360° chạy bánh, 3 servo 180° cho tay và đầu), <b>dải LED WS2812</b>, '
              '<b>cảm biến siêu âm HC-SR04</b> với 2 trở chia áp, và <b>nút nhấn</b>. Màn hình, cảm biến khoảng cách và mạch nguồn '
              'có thể dùng đồ anh đang có, chỉ cần chọn lại trong trang cấu hình của firmware.'))
S.append(Spacer(1, 10))
S.append(Image(SCHEM, width=W, height=W * 1434 / 2048))
S.append(Spacer(1, 3))
S.append(Paragraph('Sơ đồ gốc DB-Wall-E Big (ảnh anh gửi).', CAPT))
S.append(PageBreak())

# ---------------- 1. ĐỐI CHIẾU ----------------
S.append(Paragraph('1. Đối chiếu từng linh kiện', H1))
S.append(Paragraph('“Có”: đồ anh đã có, giống sơ đồ. “Thay được”: đồ anh khác loại nhưng dùng thay được (xem mục 3). “Thiếu”: phải mua.', SM))
rows = [
 ['Board ESP32-S3 DevKitC-1 N16R8 (không camera)', 'ESP32-S3 N16R8 có camera OV3660 (board WROOM CAM, mỗi bên 20 chân)', SWAP, 'Cùng chip. Rút camera ra, nối theo số GPIO in trên board'],
 ['Màn TFT 2.8" ST7789 240×320 NO_IPS (có khe thẻ SD)', 'TFT 1.8" ST7735S 128×160 (không có khe thẻ SD)', SWAP, 'Firmware có tùy chọn chip 7735. Giao diện nhỏ hơn, mất nhạc offline bằng thẻ SD'],
 ['Mic INMP441', 'INMP441', HAVE, ''],
 ['Ampli MAX98357A + loa 4Ω', 'MAX98357A + loa oval 3W 4Ω', HAVE, ''],
 ['Cảm biến laser VL53L0X (đo tới ~2 m)', 'TOF050C (VL6180X, đo tới ~20 cm)', SWAP, 'Firmware có hỗ trợ VL6180X. Né vật cản ở tầm gần'],
 ['Cảm biến siêu âm HC-SR04', 'Chưa có', NEED, 'Gắn ở mắt robot, đo xa'],
 ['Trở 1kΩ + 2kΩ (chia áp chân Echo)', 'Chưa có (anh có trở 100k)', NEED, 'Bắt buộc nếu lắp HC-SR04'],
 ['Nút chạm TTP223', 'TTP223', HAVE, ''],
 ['Nút nhấn Vol+, Boot, Vol−', 'Board có sẵn nút BOOT', NEED, 'Cần 2 nút (Vol±), thêm 1 nút Boot nếu muốn bấm từ ngoài vỏ'],
 ['Dải LED WS2812 8 bóng', 'Chưa có (2 LED mua thêm chưa rõ loại)', NEED, 'Nếu 2 LED kia là WS2812 thì dùng tạm được'],
 ['2 servo 360° (bánh trái, bánh phải)', '2 motor N20 + MX1508', NEED, 'Sơ đồ chạy bánh bằng servo, phải mua'],
 ['3 servo 180° (tay trái, tay phải, đầu)', 'Chưa có', NEED, 'Không lắp thì tay, đầu không cử động'],
 ['Mạch sạc TP4056', 'Mạch sạc USB-C trong combo', SWAP, 'Mạch của anh có sẵn tăng áp 5V'],
 ['Mạch tăng áp MT3608 (ra 5V)', '(nằm trong mạch sạc combo)', SWAP, 'Servo chạy mà board tự khởi động lại thì thêm MT3608 như sơ đồ'],
 ['Tụ hóa 470µF 16V', 'Tụ 470µF 16V ×5', HAVE, ''],
 ['Công tắc gạt', 'Công tắc gạt (anh có sẵn)', HAVE, ''],
 ['Pin 18650 ×1', 'Beston 18650 3300mAh ×2 + đế song song', HAVE, '2 pin song song, chạy lâu hơn'],
 ['Dây nối', 'Dây Dupont trong combo', HAVE, 'Nên thêm dây silicone mềm'],
 ['Vỏ Wall-E in 3D + bộ ốc (đi kèm sơ đồ)', 'Chưa có', NEED, 'Sơ đồ làm cho vỏ này. Không làm vỏ thì bỏ dòng này'],
]
S.append(tbl(['Trong sơ đồ', 'Đồ của anh', 'Tình trạng', 'Ghi chú'], rows, [150, 150, 55, 160]))

# ---------------- 2. CẦN MUA ----------------
S.append(Paragraph('2. Danh sách cần mua', H1))
S.append(KeepTogether([Paragraph('2.1 Bắt buộc để giống sơ đồ', H2), tbl(['', 'Món', 'SL', 'Ghi chú'], [
    [B, 'Servo 360° (MG90S 360 hoặc FS90R)', '2', 'Bánh trái, bánh phải. Nên chọn bánh răng kim loại'],
    [B, 'Servo 180° (MG90S bánh răng kim loại, hoặc SG90)', '3', 'Tay trái, tay phải, đầu. Servo đầu nên dùng MG90S'],
    [B, 'Dải LED WS2812 8 bóng (thanh 8 LED)', '1', 'Đèn màu dưới ngực'],
    [B, 'Cảm biến siêu âm HC-SR04', '1', 'Mắt robot'],
    [B, 'Trở 1kΩ và 2kΩ 1/4W', 'mỗi loại 1', 'Chia áp chân Echo 5V xuống 3,3V'],
    [B, 'Nút nhấn 6×6 mm', '3', 'Vol+, Vol−, Boot (nút Boot ngoài vỏ)'],
], [16, 230, 50, 219])]))
S.append(KeepTogether([Paragraph('2.2 Nên mua', H2), tbl(['', 'Món', 'SL', 'Ghi chú'], [
    [B, 'Vỏ Wall-E in 3D + bộ ốc M2, M2.5, M4', '1 bộ', 'Sơ đồ đi kèm vỏ này. Hỏi shop có kèm xích, bánh, tay, đầu không'],
    [B, 'Mạch tăng áp MT3608 (hoặc loại 5V 2–3 A)', '1', 'Phòng khi mạch sạc combo không đủ dòng cho 5 servo'],
    [B, 'Dây silicone 26AWG nhiều màu', '1 bộ', 'Mềm, dễ đi dây qua cổ và tay'],
    [B, 'Hàng rào đực 2,54 mm (header)', '1 thanh', 'Làm chỗ cắm 5 đầu servo cho gọn'],
], [16, 230, 50, 219])]))
S.append(KeepTogether([Paragraph('2.3 Tùy chọn', H2), tbl(['', 'Món', 'SL', 'Ghi chú'], [
    [B, 'Màn TFT 2.8" ST7789 240×320 NO_IPS (có khe thẻ SD)', '1', 'Giống hệt sơ đồ, giao diện to, có nhạc offline bằng thẻ SD. Không mua thì dùng màn 1.8" của anh'],
    [B, 'Cảm biến VL53L0X', '1', 'Đo xa ~2 m. Không mua thì dùng TOF050C của anh'],
    [B, 'Mạch sạc TP4056', '1', 'Chỉ khi muốn giống hệt. Mạch sạc combo của anh làm được việc này'],
], [16, 230, 50, 219])]))

# ---------------- 3. KHÁC SƠ ĐỒ ----------------
S.append(Paragraph('3. Những điểm khác sơ đồ và cách xử lý', H1))
S.append(tbl(['Điểm khác', 'Ảnh hưởng', 'Xử lý'], [
    ['Board có camera, xếp chân khác (mỗi bên 20 chân, sơ đồ vẽ board 22 chân)',
     'Camera dùng GPIO4–13, 15–18, trùng các chân sơ đồ dùng cho màn, mic, cảm biến',
     '<b>Rút cáp camera ra.</b> Nối theo số GPIO in cạnh chân, không nhìn vị trí trên hình sơ đồ'],
    ['Board chỉ có 1 chân 3V3, 1 chân 5V, 1 chân GND (sơ đồ vẽ 2 chân 3V3, 4 chân GND)',
     'Không đủ chỗ cắm cho từng dây nguồn',
     'Dây cùng loại hàn chụm thành 1 dây rồi mới cắm, hoặc lấy nguồn từ dải 5V, GND trên mạch tăng áp'],
    ['Màn 1.8" ST7735 thay màn 2.8" ST7789',
     'Màn nhỏ, giao diện có thể chật. Màn 1.8" không có khe thẻ SD nên mất nhạc offline',
     'Trong trang cấu hình chọn chip 7735, kích thước 128×160. Không ổn thì mua màn 2.8"'],
    ['TOF050C (VL6180X) thay VL53L0X',
     'Tầm đo ~20 cm thay vì ~2 m',
     'Chọn VL6180X trong trang cấu hình. Muốn đo xa thì dùng thêm HC-SR04'],
    ['Mạch sạc combo (có tăng áp 5V) thay TP4056 + MT3608',
     'Chưa rõ dòng ra tối đa. 5 servo lúc khởi động kéo dòng lớn',
     'Dùng trước. Board tự khởi động lại khi servo chạy thì thêm MT3608 chỉnh ra 5,1 V, cấp riêng cho servo'],
    ['2 pin song song thay 1 pin',
     'Dung lượng gấp đôi',
     'Chỉ nối song song khi 2 pin đã sạc đầy, chênh dưới 0,05 V'],
    ['Đèn D2 trên board nối GPIO2 (sơ đồ dùng GPIO2 cho servo bánh phải)',
     'Đèn nháy khi bánh phải chạy',
     'Bình thường, không cần xử lý'],
    ['Khe thẻ TF mặt sau board (nếu có) dùng GPIO38, 39, 40',
     'Sơ đồ dùng GPIO39, 40',
     'Không cắm thẻ nhớ vào khe sau board'],
], [150, 165, 200]))
S.append(Spacer(1, 6))
_blk=[Paragraph('3.1 Chân sơ đồ dùng', H2)]
_blk.append(Paragraph('Đọc từ sơ đồ gốc. Các chân này board của anh đều có.', P))
_blk.append(tbl(['Nhóm', 'Chân'], [
    ['Servo (ghi rõ trên sơ đồ)', 'Bánh trái <b>GPIO1</b> · bánh phải <b>GPIO2</b> · tay phải <b>GPIO41</b> · tay trái <b>GPIO42</b> · đầu <b>GPIO12</b>'],
    ['Nút Boot', 'GPIO0 (trùng nút BOOT trên board)'],
    ['Các chân khác có dây trong sơ đồ', 'GPIO3, 4, 5, 6, 7, 8, 9, 10, 11, 13, 14, 15, 16, 17, 18, 39, 40, 46, 47 (màn, mic, ampli, cảm biến, LED, nút)'],
    ['Sơ đồ không dùng', 'GPIO19, 20, 21, 45, 48 và 35, 36, 37, 38'],
], [150, 365], bold_first=True))
_blk.append(Paragraph('Chân của từng module (màn, mic, ampli, VL53L0X, HC-SR04, LED, nút) nối theo sơ đồ gốc. Firmware cho chỉnh chân qua trang cấu hình, nên lấy trang cấu hình làm chuẩn cuối cùng.', SM))

S.append(KeepTogether(_blk))

# ---------------- 4. KHÔNG DÙNG ----------------
S.append(Paragraph('4. Đồ của anh không dùng trong sơ đồ này', H1))
S.append(tbl(['Món', 'Ghi chú'], [
    ['Camera OV3660', 'Rút ra, cất lại. Lắp lại được nếu sau này đổi firmware'],
    ['2 motor N20, mạch MX1508, bộ bánh xích N20, 2 bánh răng 64T, bi đa hướng', 'Bánh xe chạy bằng servo 360°'],
    ['3 thanh đồng Ø1,6', 'Không làm khung đồng nếu dùng vỏ Wall-E'],
    ['SHT31, bộ IR thu + phát, 2 đèn Edison, OLED 0.91"', 'Firmware DB-Wall-E không dùng. Muốn giữ chức năng đo nhiệt độ, bật máy lạnh thì cần firmware riêng'],
    ['Trở 100k (đo pin)', 'Bài giới thiệu dùng biến trở 100k (104) để đo % pin. Trở 100k của anh làm cầu chia được'],
], [230, 285]))

# ---------------- 5. BƯỚC TIẾP ----------------
S.append(Paragraph('5. Các bước tiếp theo', H1))
S.append(numbered([
    'Rút camera ra khỏi board.',
    'Nạp firmware DB-Wall-E Big vào board (theo hướng dẫn trên trang firmware của họ).',
    'Điện thoại vào WiFi robot phát ra, mở <b>192.168.4.1:8080</b>. Chụp toàn bộ trang cấu hình gửi em.',
    'Em xem trang cấu hình có mục chip ST7735 128×160, VL6180X không, rồi lập bảng chân cho đúng đồ của anh.',
    'Chốt danh sách mua ở mục 2 (bắt buộc ít nhất 2 servo 360°).',
    'Thử từng module bằng dây Dupont trước khi hàn, theo thứ tự: màn → mic, loa → nút chạm → cảm biến → LED → servo → nguồn pin.',
]))
S.append(Spacer(1, 6))
S.append(note('An toàn', '• Chân Echo của HC-SR04 ra 5V, phải qua cầu chia 1kΩ nối tiếp + 2kΩ xuống GND, không thì hỏng chân ESP32.<br/>'
              '• Chỉnh mạch tăng áp ra 5,0–5,2 V bằng đồng hồ trước khi cắm servo và board.<br/>'
              '• Tụ 470µF đặt sát ngõ ra mạch tăng áp, đúng cực (chân dài là +).<br/>'
              '• Mọi GND nối chung. Không cắm servo khi đang cấp điện.', WARN))
S.append(Spacer(1, 6))
S.append(note('Chưa chắc', 'Khả năng chọn màn ST7735 128×160, cảm biến VL6180X và chỉnh chân lấy từ bài giới thiệu của DB-Robot, em chưa xem trang cấu hình thật. Thứ tự chân board của anh đọc từ ảnh quảng cáo của shop. Hàng về anh chụp board thật và trang cấu hình gửi em đối chiếu.', SUB))

def footer(c, doc):
    c.saveState(); c.setStrokeColor(LINE); c.setLineWidth(0.5); c.line(40, 30, 555, 30)
    c.setFont('DV', 7); c.setFillColor(MUTED)
    c.drawString(40, 18, 'QBK-Robo · đối chiếu với sơ đồ DB-Wall-E Big'); c.drawRightString(555, 18, str(doc.page)); c.restoreState()

doc = BaseDocTemplate(OUT, pagesize=A4, leftMargin=40, rightMargin=40, topMargin=40, bottomMargin=46,
                      title='QBK-Robo theo sơ đồ DB-Wall-E Big', author='QBK')
doc.addPageTemplates([PageTemplate(frames=[Frame(40, 46, W, A4[1] - 86, leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0)], onPage=footer)])
doc.build(S)
print('ok')
