#ifndef _BOARD_CONFIG_H_
#define _BOARD_CONFIG_H_

// QBK-Robo: ESP32-S3 N16R8 + camera OV3660, khung đồng, 2 bánh xích N20.
// Bảng chân theo hồ sơ dự án (mục 4.3): MX1508 IN3 = GPIO19, IN4 = GPIO48, IR phát = GPIO20.
// GPIO20 (USB D+) bị kéo lên mức cao lúc khởi động nên dùng cho IR phát (vô hại), không dùng cho motor.

#include <driver/gpio.h>
#include <hal/adc_types.h>

// ---------- Âm thanh: INMP441 + MAX98357A dùng chung BCLK/WS (I2S duplex) ----------
#define AUDIO_INPUT_SAMPLE_RATE  24000
#define AUDIO_OUTPUT_SAMPLE_RATE 24000
#define AUDIO_I2S_GPIO_BCLK GPIO_NUM_2    // mic SCK + ampli BCLK
#define AUDIO_I2S_GPIO_WS   GPIO_NUM_42   // mic WS  + ampli LRC
#define AUDIO_I2S_GPIO_DIN  GPIO_NUM_41   // mic SD
#define AUDIO_I2S_GPIO_DOUT GPIO_NUM_40   // ampli DIN

// ---------- Nút ----------
// GPIO0 (BOOT) dùng cho mắt thu IR nên không gắn nút vào đó.
// Nút chạm TTP223 làm nút chính: chạm = nói / dừng / tắt nhạc, giữ 5 giây = cài WiFi.
#define TOUCH_BUTTON_GPIO       GPIO_NUM_3

// ---------- Camera OV3660 (chân cố định của board) ----------
#define CAMERA_PIN_D0 GPIO_NUM_11
#define CAMERA_PIN_D1 GPIO_NUM_9
#define CAMERA_PIN_D2 GPIO_NUM_8
#define CAMERA_PIN_D3 GPIO_NUM_10
#define CAMERA_PIN_D4 GPIO_NUM_12
#define CAMERA_PIN_D5 GPIO_NUM_18
#define CAMERA_PIN_D6 GPIO_NUM_17
#define CAMERA_PIN_D7 GPIO_NUM_16
#define CAMERA_PIN_XCLK GPIO_NUM_15
#define CAMERA_PIN_PCLK GPIO_NUM_13
#define CAMERA_PIN_VSYNC GPIO_NUM_6
#define CAMERA_PIN_HREF GPIO_NUM_7
#define CAMERA_PIN_SIOC GPIO_NUM_5
#define CAMERA_PIN_SIOD GPIO_NUM_4
#define CAMERA_PIN_PWDN GPIO_NUM_NC
#define CAMERA_PIN_RESET GPIO_NUM_NC
#define XCLK_FREQ_HZ 20000000

// ---------- Màn TFT 1.8" ST7735S 128x160, đặt nằm ngang ----------
// CS nối GND, RES nối EN, BLK nối 3V3 nên không dùng chân ESP32 cho 3 chân này.
#define DISPLAY_CLK_PIN       GPIO_NUM_21
#define DISPLAY_MOSI_PIN      GPIO_NUM_47
#define DISPLAY_DC_PIN        GPIO_NUM_14
#define DISPLAY_CS_PIN        GPIO_NUM_NC
#define DISPLAY_RST_PIN       GPIO_NUM_NC
#define DISPLAY_BACKLIGHT_PIN GPIO_NUM_NC
#define DISPLAY_WIDTH   160
#define DISPLAY_HEIGHT  128
#define DISPLAY_SWAP_XY  true
#define DISPLAY_MIRROR_X true
#define DISPLAY_MIRROR_Y false
#define DISPLAY_INVERT_COLOR false
#define DISPLAY_RGB_ORDER LCD_RGB_ELEMENT_ORDER_RGB
#define DISPLAY_OFFSET_X 1
#define DISPLAY_OFFSET_Y 2
#define DISPLAY_SPI_MODE 0
#define DISPLAY_SPI_HZ   (15 * 1000 * 1000)   // đúng mức ghi tối đa của ST7735S theo datasheet, chắc chắn với dây dài ~15 cm

// ---------- I2C: TOF050C (0x29) + SHT31 (0x44), cổng I2C 0 (camera dùng cổng 1) ----------
#define SENSOR_I2C_SDA GPIO_NUM_38
#define SENSOR_I2C_SCL GPIO_NUM_39
#define TOF_I2C_ADDR   0x29
#define SHT31_I2C_ADDR 0x44

// ---------- Motor N20 qua MX1508 ----------
#define MOTOR_L_IN1 GPIO_NUM_45
#define MOTOR_L_IN2 GPIO_NUM_46
#define MOTOR_R_IN1 GPIO_NUM_19
#define MOTOR_R_IN2 GPIO_NUM_48   // đèn RGB trên board có thể nháy khi motor phải chạy, không sao
#define MOTOR_L_INVERT false      // đảo nếu motor trái quay ngược
#define MOTOR_R_INVERT false      // đảo nếu motor phải quay ngược
#define MOTOR_PWM_HZ   1000
#define OBSTACLE_STOP_MM 80       // đang tiến mà vật cản gần hơn thì dừng
#define TOF_NO_TARGET    999      // giá trị trả về khi không có vật trong tầm đo (~20 cm)

// ---------- IR điều hòa ----------
#define IR_RX_GPIO GPIO_NUM_0
#define IR_TX_GPIO GPIO_NUM_20

// ---------- Đo pin: cầu chia 100k/100k vào GPIO1 (ADC1 kênh 0) ----------
#define BATTERY_ADC_UNIT    ADC_UNIT_1
#define BATTERY_ADC_CHANNEL ADC_CHANNEL_0
#define BATTERY_R_UPPER     100000.0f
#define BATTERY_R_LOWER     100000.0f

#endif // _BOARD_CONFIG_H_
