// QBK-Robo: firmware thử phần cứng.
// Màn TFT hiện trạng thái từng module, cập nhật liên tục. Chạm nút TTP223 để thử loa, motor, IR phát.
// Mọi kết quả cũng in ra cổng Serial (115200) qua cổng USB-C "COM".
#include <stdio.h>
#include <string.h>
#include <math.h>
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "esp_log.h"
#include "esp_timer.h"
#include "driver/gpio.h"
#include "driver/spi_master.h"
#include "driver/i2c_master.h"
#include "driver/i2s_std.h"
#include "driver/ledc.h"
#include "esp_adc/adc_oneshot.h"
#include "esp_adc/adc_cali.h"
#include "esp_adc/adc_cali_scheme.h"
#include "esp_lcd_panel_io.h"
#include "esp_lcd_panel_vendor.h"
#include "esp_lcd_panel_ops.h"
#include "esp_lvgl_port.h"
#include "esp_camera.h"


// ---- Chân (giống firmware chính) ----
#define PIN_LCD_CLK 21
#define PIN_LCD_MOSI 47
#define PIN_LCD_DC 14
#define PIN_I2S_BCLK 2
#define PIN_I2S_WS 42
#define PIN_I2S_DIN 41
#define PIN_I2S_DOUT 40
#define PIN_SDA 38
#define PIN_SCL 39
#define PIN_TOUCH 3
#define PIN_IR_RX 0
#define PIN_IR_TX 20   // GPIO20 (USB D+) lên mức cao lúc khởi động: dùng cho IR, không dùng cho motor
#define PIN_ML1 45
#define PIN_ML2 46
#define PIN_MR1 19
#define PIN_MR2 48

// ---- Trạng thái ----
static volatile int g_ir_edges = 0;
static int g_tof_mm = -2, g_mic_level = 0;
static float g_temp = NAN, g_hum = NAN, g_batt = NAN;
static bool g_touch = false, g_cam_ok = false, g_tof_ok = false, g_sht_ok = false;
static char g_cam_name[24] = "?";
static char g_action[48] = "Cham dau robot de thu loa, motor, IR";

static i2c_master_bus_handle_t i2c_bus;
static i2c_master_dev_handle_t tof_dev, sht_dev;
static i2s_chan_handle_t i2s_tx, i2s_rx;
static adc_oneshot_unit_handle_t adc;
static adc_cali_handle_t adc_cali;
static lv_obj_t* lbl;

// ======================= Màn hình =======================
static void display_init(void) {
    spi_bus_config_t bus = {.mosi_io_num = PIN_LCD_MOSI, .miso_io_num = -1, .sclk_io_num = PIN_LCD_CLK,
                            .quadwp_io_num = -1, .quadhd_io_num = -1, .max_transfer_sz = 160 * 128 * 2};
    ESP_ERROR_CHECK(spi_bus_initialize(SPI3_HOST, &bus, SPI_DMA_CH_AUTO));
    esp_lcd_panel_io_handle_t io;
    esp_lcd_panel_io_spi_config_t io_cfg = {.cs_gpio_num = -1, .dc_gpio_num = PIN_LCD_DC, .spi_mode = 0,
                                            .pclk_hz = 27000000, .trans_queue_depth = 10, .lcd_cmd_bits = 8, .lcd_param_bits = 8};
    ESP_ERROR_CHECK(esp_lcd_new_panel_io_spi(SPI3_HOST, &io_cfg, &io));
    esp_lcd_panel_handle_t panel;
    esp_lcd_panel_dev_config_t pcfg = {.reset_gpio_num = -1, .rgb_ele_order = LCD_RGB_ELEMENT_ORDER_RGB, .bits_per_pixel = 16};
    ESP_ERROR_CHECK(esp_lcd_new_panel_st7789(io, &pcfg, &panel));
    esp_lcd_panel_reset(panel);
    vTaskDelay(pdMS_TO_TICKS(120));   // ST7735S cần 120 ms sau reset
    esp_lcd_panel_init(panel);
    esp_lcd_panel_invert_color(panel, false);
    esp_lcd_panel_set_gap(panel, 1, 2);
    esp_lcd_panel_disp_on_off(panel, true);

    const lvgl_port_cfg_t lcfg = ESP_LVGL_PORT_INIT_CONFIG();
    lvgl_port_init(&lcfg);
    lvgl_port_display_cfg_t dcfg = {
        .io_handle = io, .panel_handle = panel, .buffer_size = 160 * 32, .double_buffer = true,
        .hres = 160, .vres = 128, .monochrome = false,
        .rotation = {.swap_xy = true, .mirror_x = true, .mirror_y = false},
        .color_format = LV_COLOR_FORMAT_RGB565,
        .flags = {.buff_dma = true, .swap_bytes = true},
    };
    lv_display_t* disp = lvgl_port_add_disp(&dcfg);
    (void)disp;
    lvgl_port_lock(0);
    lv_obj_t* scr = lv_screen_active();
    lv_obj_set_style_bg_color(scr, lv_color_hex(0x101820), 0);
    lv_obj_t* title = lv_label_create(scr);
    lv_label_set_text(title, "QBK-Robo TEST");
    lv_obj_set_style_text_color(title, lv_color_hex(0xF0A24A), 0);
    lv_obj_align(title, LV_ALIGN_TOP_MID, 0, 1);
    lbl = lv_label_create(scr);
    lv_obj_set_style_text_color(lbl, lv_color_hex(0xFFFFFF), 0);
    lv_obj_set_width(lbl, 156);
    lv_label_set_long_mode(lbl, LV_LABEL_LONG_WRAP);
    lv_obj_align(lbl, LV_ALIGN_TOP_LEFT, 2, 16);
    // dải màu thử: đỏ, xanh lá, xanh dương
    const uint32_t cols[3] = {0xFF0000, 0x00FF00, 0x0000FF};
    for (int i = 0; i < 3; i++) {
        lv_obj_t* b = lv_obj_create(scr);
        lv_obj_set_size(b, 53, 6);
        lv_obj_set_style_bg_color(b, lv_color_hex(cols[i]), 0);
        lv_obj_set_style_border_width(b, 0, 0);
        lv_obj_set_style_radius(b, 0, 0);
        lv_obj_align(b, LV_ALIGN_BOTTOM_LEFT, i * 53, 0);
    }
    lvgl_port_unlock();
}

// ======================= I2C: TOF050C + SHT31 =======================
static bool tof_w8(uint16_t r, uint8_t v) { uint8_t b[3] = {r >> 8, r & 0xFF, v}; return i2c_master_transmit(tof_dev, b, 3, 100) == ESP_OK; }
static bool tof_r8(uint16_t r, uint8_t* v) { uint8_t b[2] = {r >> 8, r & 0xFF}; return i2c_master_transmit_receive(tof_dev, b, 2, v, 1, 100) == ESP_OK; }
static void tof_init(void) {
    uint8_t f = 0;
    if (!tof_r8(0x016, &f)) return;
    static const uint16_t regs[][2] = {
        {0x0207, 0x01}, {0x0208, 0x01}, {0x0096, 0x00}, {0x0097, 0xfd}, {0x00e3, 0x00}, {0x00e4, 0x04}, {0x00e5, 0x02}, {0x00e6, 0x01},
        {0x00e7, 0x03}, {0x00f5, 0x02}, {0x00d9, 0x05}, {0x00db, 0xce}, {0x00dc, 0x03}, {0x00dd, 0xf8}, {0x009f, 0x00}, {0x00a3, 0x3c},
        {0x00b7, 0x00}, {0x00bb, 0x3c}, {0x00b2, 0x09}, {0x00ca, 0x09}, {0x0198, 0x01}, {0x01b0, 0x17}, {0x01ad, 0x00}, {0x00ff, 0x05},
        {0x0100, 0x05}, {0x0199, 0x05}, {0x01a6, 0x1b}, {0x01ac, 0x3e}, {0x01a7, 0x1f}, {0x0030, 0x00}, {0x0011, 0x10}, {0x010a, 0x30},
        {0x003f, 0x46}, {0x0031, 0xFF}, {0x0041, 0x63}, {0x002e, 0x01}, {0x001b, 0x09}, {0x003e, 0x31}, {0x0014, 0x24}, {0x0016, 0x00}};
    if (f == 1) for (int i = 0; i < sizeof(regs) / sizeof(regs[0]); i++) tof_w8(regs[i][0], regs[i][1]);
    g_tof_ok = true;
}
static int tof_read(void) {
    if (!g_tof_ok || !tof_w8(0x018, 0x01)) return -1;
    for (int i = 0; i < 30; i++) {
        uint8_t s = 0;
        if (!tof_r8(0x04F, &s)) return -1;
        if ((s & 7) == 4) { uint8_t mm = 0, st = 0; tof_r8(0x062, &mm); tof_r8(0x04D, &st); tof_w8(0x015, 7); return ((st >> 4) || mm >= 200) ? 999 : mm; }
        vTaskDelay(pdMS_TO_TICKS(5));
    }
    return -1;
}
static bool sht_read(float* t, float* h) {
    uint8_t c[2] = {0x24, 0x00}, d[6];
    if (i2c_master_transmit(sht_dev, c, 2, 100) != ESP_OK) return false;
    vTaskDelay(pdMS_TO_TICKS(20));
    if (i2c_master_receive(sht_dev, d, 6, 100) != ESP_OK) return false;
    *t = -45 + 175.0f * ((d[0] << 8) | d[1]) / 65535.0f;
    *h = 100.0f * ((d[3] << 8) | d[4]) / 65535.0f;
    return true;
}
static void i2c_init(void) {
    i2c_master_bus_config_t c = {.i2c_port = I2C_NUM_0,   /* camera tự dùng cổng 1 */ .sda_io_num = PIN_SDA, .scl_io_num = PIN_SCL, .clk_source = I2C_CLK_SRC_DEFAULT,
                                 .glitch_ignore_cnt = 7, .flags.enable_internal_pullup = 1};
    ESP_ERROR_CHECK(i2c_new_master_bus(&c, &i2c_bus));
    printf("I2C scan (SDA=38, SCL=39):");
    for (int a = 1; a < 127; a++) if (i2c_master_probe(i2c_bus, a, 50) == ESP_OK) printf(" 0x%02X", a);
    printf("\n");
    i2c_device_config_t d = {.dev_addr_length = I2C_ADDR_BIT_LEN_7, .scl_speed_hz = 100000};
    if (i2c_master_probe(i2c_bus, 0x29, 50) == ESP_OK) { d.device_address = 0x29; i2c_master_bus_add_device(i2c_bus, &d, &tof_dev); tof_init(); }
    if (i2c_master_probe(i2c_bus, 0x44, 50) == ESP_OK) { d.device_address = 0x44; i2c_master_bus_add_device(i2c_bus, &d, &sht_dev); g_sht_ok = true; }
}

// ======================= Âm thanh =======================
static void audio_init(void) {
    i2s_chan_config_t cc = I2S_CHANNEL_DEFAULT_CONFIG(I2S_NUM_0, I2S_ROLE_MASTER);
    cc.auto_clear = true;
    ESP_ERROR_CHECK(i2s_new_channel(&cc, &i2s_tx, &i2s_rx));
    i2s_std_config_t sc = {
        .clk_cfg = I2S_STD_CLK_DEFAULT_CONFIG(16000),
        .slot_cfg = I2S_STD_PHILIPS_SLOT_DEFAULT_CONFIG(I2S_DATA_BIT_WIDTH_32BIT, I2S_SLOT_MODE_MONO),
        .gpio_cfg = {.mclk = I2S_GPIO_UNUSED, .bclk = PIN_I2S_BCLK, .ws = PIN_I2S_WS, .dout = PIN_I2S_DOUT, .din = PIN_I2S_DIN},
    };
    sc.slot_cfg.slot_mask = I2S_STD_SLOT_LEFT;
    ESP_ERROR_CHECK(i2s_channel_init_std_mode(i2s_tx, &sc));
    ESP_ERROR_CHECK(i2s_channel_init_std_mode(i2s_rx, &sc));
    i2s_channel_enable(i2s_tx);
    i2s_channel_enable(i2s_rx);
}
static void play_tone(float f, int ms) {
    const int n = 256; int32_t buf[256];
    int total = 16000 * ms / 1000; static float ph = 0;
    for (int done = 0; done < total; done += n) {
        for (int i = 0; i < n; i++) { buf[i] = (int32_t)(sinf(ph) * 0.25f * 2147483647.0f); ph += 2 * M_PI * f / 16000; if (ph > 2 * M_PI) ph -= 2 * M_PI; }
        size_t w; i2s_channel_write(i2s_tx, buf, sizeof(buf), &w, 200);
    }
}
static void mic_task(void* a) {
    int32_t buf[256];
    while (1) {
        size_t r = 0;
        if (i2s_channel_read(i2s_rx, buf, sizeof(buf), &r, 200) == ESP_OK && r > 0) {
            int n = r / 4; double s = 0;
            for (int i = 0; i < n; i++) { double v = (buf[i] >> 14) / 131072.0; s += v * v; }
            double rms = sqrt(s / n);
            int lvl = (int)(rms * 400); if (lvl > 20) lvl = 20;
            g_mic_level = lvl;
        }
    }
}

// ======================= Motor, IR, ADC, camera =======================
static void motors_init(void) {
    const int all[5] = {PIN_ML1, PIN_ML2, PIN_MR1, PIN_MR2, PIN_IR_TX};
    for (int i = 0; i < 5; i++) { gpio_reset_pin(all[i]); gpio_set_direction(all[i], GPIO_MODE_OUTPUT); gpio_set_level(all[i], 0); }
    ledc_timer_config_t t = {.speed_mode = LEDC_LOW_SPEED_MODE, .duty_resolution = LEDC_TIMER_10_BIT, .timer_num = LEDC_TIMER_2, .freq_hz = 1000, .clk_cfg = LEDC_AUTO_CLK};
    ledc_timer_config(&t);
    const int pins[4] = {PIN_ML1, PIN_ML2, PIN_MR1, PIN_MR2};
    for (int i = 0; i < 4; i++) {
        ledc_channel_config_t c = {.gpio_num = pins[i], .speed_mode = LEDC_LOW_SPEED_MODE, .channel = LEDC_CHANNEL_2 + i, .timer_sel = LEDC_TIMER_2, .duty = 0};
        ledc_channel_config(&c);
    }
    // IR phát: sóng mang 38 kHz trên GPIO20, tắt khi không dùng
    ledc_timer_config_t t3 = {.speed_mode = LEDC_LOW_SPEED_MODE, .duty_resolution = LEDC_TIMER_8_BIT, .timer_num = LEDC_TIMER_3, .freq_hz = 38000, .clk_cfg = LEDC_AUTO_CLK};
    ledc_timer_config(&t3);
    ledc_channel_config_t ir = {.gpio_num = PIN_IR_TX, .speed_mode = LEDC_LOW_SPEED_MODE, .channel = LEDC_CHANNEL_6, .timer_sel = LEDC_TIMER_3, .duty = 0};
    ledc_channel_config(&ir);
}
static void motor_ch(int ch, int duty) { ledc_set_duty(LEDC_LOW_SPEED_MODE, LEDC_CHANNEL_2 + ch, duty); ledc_update_duty(LEDC_LOW_SPEED_MODE, LEDC_CHANNEL_2 + ch); }
static void IRAM_ATTR ir_isr(void* a) { g_ir_edges++; }
static void ir_rx_init(void) {
    gpio_config_t c = {.pin_bit_mask = 1ULL << PIN_IR_RX, .mode = GPIO_MODE_INPUT, .pull_up_en = 1, .intr_type = GPIO_INTR_NEGEDGE};
    gpio_config(&c);
    gpio_install_isr_service(0);
    gpio_isr_handler_add(PIN_IR_RX, ir_isr, NULL);
    gpio_config_t t = {.pin_bit_mask = 1ULL << PIN_TOUCH, .mode = GPIO_MODE_INPUT, .pull_down_en = 1};
    gpio_config(&t);
}
static void adc_init(void) {
    adc_oneshot_unit_init_cfg_t u = {.unit_id = ADC_UNIT_1};
    adc_oneshot_new_unit(&u, &adc);
    adc_oneshot_chan_cfg_t c = {.atten = ADC_ATTEN_DB_12, .bitwidth = ADC_BITWIDTH_DEFAULT};
    adc_oneshot_config_channel(adc, ADC_CHANNEL_0, &c);
    adc_cali_curve_fitting_config_t cc = {.unit_id = ADC_UNIT_1, .chan = ADC_CHANNEL_0, .atten = ADC_ATTEN_DB_12, .bitwidth = ADC_BITWIDTH_DEFAULT};
    adc_cali_create_scheme_curve_fitting(&cc, &adc_cali);
}
static float battery_v(void) {
    int sum = 0;
    for (int i = 0; i < 16; i++) { int raw = 0, mv = 0; adc_oneshot_read(adc, ADC_CHANNEL_0, &raw); adc_cali_raw_to_voltage(adc_cali, raw, &mv); sum += mv; }
    return sum / 16.0f * 2 / 1000.0f;   // cầu chia 100k/100k
}
static void camera_init(void) {
    camera_config_t c = {
        .pin_pwdn = -1, .pin_reset = -1, .pin_xclk = 15, .pin_sccb_sda = 4, .pin_sccb_scl = 5,
        .pin_d7 = 16, .pin_d6 = 17, .pin_d5 = 18, .pin_d4 = 12, .pin_d3 = 10, .pin_d2 = 8, .pin_d1 = 9, .pin_d0 = 11,
        .pin_vsync = 6, .pin_href = 7, .pin_pclk = 13, .xclk_freq_hz = 20000000, .ledc_timer = LEDC_TIMER_0, .ledc_channel = LEDC_CHANNEL_0,
        .pixel_format = PIXFORMAT_JPEG, .frame_size = FRAMESIZE_QVGA, .jpeg_quality = 12, .fb_count = 1,
        .fb_location = CAMERA_FB_IN_PSRAM, .grab_mode = CAMERA_GRAB_WHEN_EMPTY, .sccb_i2c_port = 0};
    if (esp_camera_init(&c) == ESP_OK) {
        sensor_t* s = esp_camera_sensor_get();
        camera_fb_t* fb = esp_camera_fb_get();
        g_cam_ok = fb != NULL;
        if (fb) esp_camera_fb_return(fb);
        snprintf(g_cam_name, sizeof(g_cam_name), "PID 0x%04X", s ? s->id.PID : 0);
    }
}

// ======================= Chuỗi thử khi chạm =======================
static void action_sequence(void) {
    strcpy(g_action, "Loa: 3 tieng bip");
    for (int i = 0; i < 3; i++) { play_tone(440 * (i + 2) / 2.0f, 250); vTaskDelay(pdMS_TO_TICKS(120)); }
    const char* names[4] = {"Motor TRAI tien", "Motor TRAI lui", "Motor PHAI tien", "Motor PHAI lui"};
    for (int i = 0; i < 4; i++) {
        strcpy(g_action, names[i]); printf("%s\n", names[i]);
        motor_ch(i, 700); vTaskDelay(pdMS_TO_TICKS(800)); motor_ch(i, 0); vTaskDelay(pdMS_TO_TICKS(300));
    }
    strcpy(g_action, "IR phat 1 giay (soi bang camera DT)");
    ledc_set_duty(LEDC_LOW_SPEED_MODE, LEDC_CHANNEL_6, 85); ledc_update_duty(LEDC_LOW_SPEED_MODE, LEDC_CHANNEL_6);
    vTaskDelay(pdMS_TO_TICKS(1000));
    ledc_set_duty(LEDC_LOW_SPEED_MODE, LEDC_CHANNEL_6, 0); ledc_update_duty(LEDC_LOW_SPEED_MODE, LEDC_CHANNEL_6);
    strcpy(g_action, "Xong. Cham de thu lai");
}

void app_main(void) {
    printf("\n===== QBK-Robo TEST =====\n");
    motors_init();
    display_init();
    i2c_init();
    audio_init();
    ir_rx_init();
    adc_init();
    camera_init();
    xTaskCreate(mic_task, "mic", 4096, NULL, 5, NULL);
    printf("Camera: %s %s\n", g_cam_ok ? "OK" : "LOI", g_cam_name);
    play_tone(880, 150);

    int64_t last_print = 0;
    bool prev_touch = false;
    while (1) {
        g_touch = gpio_get_level(PIN_TOUCH);
        g_tof_mm = tof_read();
        if (g_sht_ok) { float t, h; if (sht_read(&t, &h)) { g_temp = t; g_hum = h; } }
        g_batt = battery_v();

        char bar[21]; memset(bar, '|', g_mic_level); bar[g_mic_level] = 0;
        char tof[16], sht[24];
        if (g_tof_mm == 999) strcpy(tof, "khong co vat"); else if (g_tof_mm >= 0) snprintf(tof, sizeof(tof), "%d mm", g_tof_mm); else strcpy(tof, g_tof_ok ? "loi doc" : "KHONG THAY");
        if (!isnan(g_temp)) snprintf(sht, sizeof(sht), "%.1fC %.0f%%", g_temp, g_hum); else strcpy(sht, g_sht_ok ? "loi doc" : "KHONG THAY");
        char text[300];
        snprintf(text, sizeof(text),
                 "TOF: %s\nSHT31: %s\nMic: %s\nPin: %.2f V\nCham: %s  IR thu: %d\nCam: %s %s\n> %s",
                 tof, sht, bar, g_batt, g_touch ? "CO" : "khong", g_ir_edges, g_cam_ok ? "OK" : "LOI", g_cam_name, g_action);
        lvgl_port_lock(0); lv_label_set_text(lbl, text); lvgl_port_unlock();
        if (esp_timer_get_time() - last_print > 1000000) {
            printf("TOF=%s SHT31=%s MIC=%d PIN=%.2fV CHAM=%d IR_THU=%d CAM=%s\n", tof, sht, g_mic_level, g_batt, g_touch, g_ir_edges, g_cam_ok ? "OK" : "LOI");
            last_print = esp_timer_get_time();
        }
        if (g_touch && !prev_touch) action_sequence();
        prev_touch = g_touch;
        vTaskDelay(pdMS_TO_TICKS(150));
    }
}
