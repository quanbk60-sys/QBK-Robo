# QBK-Robo · Firmware

Hai file để nạp, đều nạp ở **địa chỉ 0x0**:

| File | Dùng khi nào |
|---|---|
| `bin/qbk-test.bin` | Phần B: thử từng module bằng dây Dupont. Màn hiện trạng thái từng module. |
| `bin/qbk-robo-xiaozhi-vi.bin` | Robot hoàn chỉnh: trợ lý AI Xiaozhi, giao diện tiếng Việt. |

## Cách nạp (máy tính, trình duyệt Chrome hoặc Edge)

1. Gạt công tắc robot sang **TẮT**. Cắm cáp USB-C (loại truyền dữ liệu) vào cổng **COM** của board.
2. Mở trang nạp ESP32 trên trình duyệt: https://espressif.github.io/esptool-js/
3. Baudrate để 921600, bấm **Connect**, chọn cổng COM của board.
   - Không thấy cổng: cài driver chip USB của board (CH340 hoặc CH343).
   - Không kết nối được: giữ nút **BOOT**, bấm **RST** 1 lần, nhả BOOT, bấm Connect lại.
4. Lần đầu nạp: bấm **Erase Flash** (xóa sạch), đợi xong.
5. Ở ô Flash Address ghi **0x0**, chọn file `.bin`, bấm **Program**. Đợi 1–3 phút.
6. Xong bấm **RST** trên board (hoặc rút cáp cắm lại).

Nạp bằng máy tính có Python: `esptool --chip esp32s3 --port COMx write-flash 0x0 qbk-robo-xiaozhi-vi.bin`

## Firmware thử phần cứng (qbk-test.bin)

Màn TFT hiện liên tục:

- **TOF**: khoảng cách mm (đưa tay lại gần thì số đổi). `KHONG THAY` = sai dây SDA/SCL hoặc chưa cấp 3V3.
- **SHT31**: nhiệt độ, độ ẩm (hà hơi vào thì độ ẩm tăng).
- **Mic**: thanh `||||` dài ra khi nói gần mic.
- **Pin**: điện áp pin đọc qua GPIO1 (3,6–4,2 V khi chạy pin).
- **Chạm**: `CO` khi chạm nút TTP223. **IR thu**: số xung tăng khi bấm remote vào mắt thu.
- **Cam**: `OK` kèm mã cảm biến camera.
- Dải màu dưới cùng phải là **đỏ – xanh lá – xanh dương** từ trái sang phải. Sai thứ tự hoặc chữ bị lật: báo em để đổi cấu hình màn.

**Chạm vào nút TTP223** để chạy chuỗi thử: loa kêu 3 tiếng bíp → motor trái tiến, lùi → motor phải tiến, lùi → IR phát 1 giây (soi bằng camera điện thoại sẽ thấy đèn IR nháy tím).

Mở Serial Monitor 115200 (cổng COM) sẽ thấy cùng thông tin và danh sách địa chỉ I2C (phải có 0x29 và 0x44).

## Firmware chính (qbk-robo-xiaozhi-vi.bin)

Lần đầu bật:

1. Màn hiện hướng dẫn kết nối WiFi. Điện thoại vào mạng WiFi tên **Xiaozhi-xxxx** do robot phát, trang cài đặt tự mở (hoặc vào 192.168.4.1), chọn WiFi nhà (2.4 GHz), nhập mật khẩu.
2. Robot đọc **mã 6 số**. Vào https://xiaozhi.me, đăng nhập, thêm thiết bị bằng mã đó. Ở đây chọn ngôn ngữ tiếng Việt, giọng nói, tính cách, tên gọi robot.
3. Nói **"Hi ESP"** hoặc **chạm vào đầu robot** để bắt đầu nói chuyện. Chạm lần nữa để dừng.
4. Giữ nút chạm 3 giây: vào lại chế độ cài WiFi.

Có thể nói với robot:

| Nói | Robot làm |
|---|---|
| "Đi tới 2 giây", "lùi lại", "quay trái", "dừng lại" | Chạy bánh xích. Đang tiến gặp vật cản dưới 8 cm thì tự dừng |
| "Phía trước có gì gần không?" | Đo khoảng cách bằng TOF050C |
| "Phòng đang bao nhiêu độ?" | Đọc SHT31 |
| "Học lệnh bật máy lạnh" rồi bấm remote vào nóc robot | Học lệnh IR, lưu với tên (bật, tắt, 26 độ…) |
| "Bật máy lạnh", "chỉnh 26 độ", "tắt máy lạnh" | Phát lệnh đã học |
| "Nhảy đi", "nhảy kiểu robot", "vừa hát vừa nhảy" | 5 điệu nhảy bánh xích, đổi biểu cảm theo nhịp |
| "Mở nhạc", "hát mừng sinh nhật", "biểu diễn đi" | Phát 1 trong 5 bài nhạc có sẵn và nhảy theo |
| "Chụp ảnh xem trước mặt có gì" | Camera chụp và AI mô tả |
| Kể chuyện, đố vui, oẳn tù tì, học tiếng Anh | AI tự làm |

Chạm vào đầu robot khi đang nhảy / phát nhạc để dừng.

Bài nhạc có sẵn: Chúc mừng sinh nhật, Kìa con bướm vàng, Ngôi sao lấp lánh, Jingle Bells, Nhạc nhảy QBK. Điệu nhảy: lắc lư, xoay vòng, tiến lùi, kiểu robot, vui vẻ.

## Chân GPIO (đã đổi so với hồ sơ bản đầu)

MX1508 IN3 dùng **GPIO19**, IR phát dùng **GPIO48** (tránh đèn RGB có sẵn trên board ở GPIO48 làm nháy khi chạy motor).
Các chân còn lại giữ như bảng 4.3 trong hồ sơ. Camera: GPIO4–13, 15–18.

## Mã nguồn

- `xiaozhi-board/qbk-robo/`: board riêng trong Xiaozhi (cấu hình chân, motor, cảm biến, IR, nhảy múa, nhạc).
- `xiaozhi-board/xiaozhi-register-board.patch`: đăng ký board vào Kconfig và CMake của Xiaozhi.
- `xiaozhi-board/XIAOZHI_COMMIT`: commit Xiaozhi đã dùng (ESP-IDF release/v6.1).
- `qbk-test/`: firmware thử phần cứng (ESP-IDF thuần, LVGL).
- `songs/`: script tổng hợp 5 bài nhạc và file OGG.

Biên dịch lại firmware chính:

```
git clone https://github.com/78/xiaozhi-esp32 && cd xiaozhi-esp32
git checkout $(cat ../firmware/xiaozhi-board/XIAOZHI_COMMIT)
git apply ../firmware/xiaozhi-board/xiaozhi-register-board.patch
cp -r ../firmware/xiaozhi-board/qbk-robo main/boards/
python scripts/build.py qbk-robo --language vi-VN
```

## Chỉnh khi chạy thật

Các chỗ có thể phải đổi sau khi nạp thử (trong `config.h`): hướng xoay màn (`DISPLAY_MIRROR_X/Y`, `DISPLAY_OFFSET_X/Y`), chiều motor (`MOTOR_L_INVERT`, `MOTOR_R_INVERT`), khoảng dừng vật cản (`OBSTACLE_STOP_MM`). Gửi em ảnh màn hoặc mô tả, em sửa và biên dịch lại.
