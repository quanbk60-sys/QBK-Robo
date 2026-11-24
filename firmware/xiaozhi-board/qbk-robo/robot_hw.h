// QBK-Robo: motor, cảm biến TOF050C (VL6180X), SHT31, IR học/phát lệnh điều hòa.
#ifndef QBK_ROBOT_HW_H
#define QBK_ROBOT_HW_H

#include <driver/i2c_master.h>
#include <driver/ledc.h>
#include <driver/rmt_rx.h>
#include <driver/rmt_tx.h>
#include <driver/rmt_encoder.h>
#include <freertos/FreeRTOS.h>
#include <freertos/semphr.h>
#include <freertos/queue.h>
#include <esp_log.h>
#include <nvs.h>
#include <string>
#include <vector>
#include <cmath>

#include "config.h"

// ======================= Motor =======================
class Motors {
public:
    void Init() {
        ledc_timer_config_t t = {};
        t.speed_mode = LEDC_LOW_SPEED_MODE;
        t.duty_resolution = LEDC_TIMER_10_BIT;
        t.timer_num = LEDC_TIMER_2;          // timer 0 dành cho XCLK camera
        t.freq_hz = MOTOR_PWM_HZ;
        t.clk_cfg = LEDC_AUTO_CLK;
        ESP_ERROR_CHECK(ledc_timer_config(&t));
        const gpio_num_t pins[4] = {MOTOR_L_IN1, MOTOR_L_IN2, MOTOR_R_IN1, MOTOR_R_IN2};
        for (int i = 0; i < 4; i++) {
            ledc_channel_config_t c = {};
            c.gpio_num = pins[i];
            c.speed_mode = LEDC_LOW_SPEED_MODE;
            c.channel = (ledc_channel_t)(LEDC_CHANNEL_2 + i);
            c.timer_sel = LEDC_TIMER_2;
            c.duty = 0;
            ESP_ERROR_CHECK(ledc_channel_config(&c));
        }
        ok_ = true;
    }
    // left, right: -100..100 (%)
    void Set(int left, int right) {
        if (!ok_) return;
        if (MOTOR_L_INVERT) left = -left;
        if (MOTOR_R_INVERT) right = -right;
        Drive(LEDC_CHANNEL_2, LEDC_CHANNEL_3, left);
        Drive(LEDC_CHANNEL_4, LEDC_CHANNEL_5, right);
    }
    void Stop() { Set(0, 0); }

private:
    bool ok_ = false;
    static void Drive(ledc_channel_t a, ledc_channel_t b, int v) {
        if (v > 100) v = 100;
        if (v < -100) v = -100;
        uint32_t duty = (uint32_t)(abs(v) * 1023 / 100);
        ledc_set_duty(LEDC_LOW_SPEED_MODE, a, v > 0 ? duty : 0);
        ledc_set_duty(LEDC_LOW_SPEED_MODE, b, v < 0 ? duty : 0);
        ledc_update_duty(LEDC_LOW_SPEED_MODE, a);
        ledc_update_duty(LEDC_LOW_SPEED_MODE, b);
    }
};

// ======================= Cảm biến I2C =======================
class SensorBus {
public:
    bool Init() {
        i2c_master_bus_config_t cfg = {};
        cfg.i2c_port = I2C_NUM_1;           // I2C 0 dành cho camera (SCCB)
        cfg.sda_io_num = SENSOR_I2C_SDA;
        cfg.scl_io_num = SENSOR_I2C_SCL;
        cfg.clk_source = I2C_CLK_SRC_DEFAULT;
        cfg.glitch_ignore_cnt = 7;
        cfg.flags.enable_internal_pullup = 1;
        if (i2c_new_master_bus(&cfg, &bus_) != ESP_OK) return false;
        lock_ = xSemaphoreCreateMutex();
        tof_ok_ = AddDev(TOF_I2C_ADDR, &tof_) && TofInit();
        sht_ok_ = AddDev(SHT31_I2C_ADDR, &sht_);
        ESP_LOGI("QBK", "TOF050C %s, SHT31 %s", tof_ok_ ? "OK" : "KHONG THAY", sht_ok_ ? "OK" : "KHONG THAY");
        return true;
    }
    bool tof_ok() const { return tof_ok_; }
    bool sht_ok() const { return sht_ok_; }

    // Khoảng cách mm (0..255). -1 nếu lỗi.
    int ReadDistanceMm() {
        if (!tof_ok_) return -1;
        Lock l(lock_);
        if (!W8(0x018, 0x01)) return -1;               // SYSRANGE_START single shot
        for (int i = 0; i < 30; i++) {
            uint8_t s = 0;
            if (!R8(0x04F, &s)) return -1;               // RESULT_INTERRUPT_STATUS_GPIO
            if ((s & 0x07) == 0x04) {
                uint8_t mm = 0;
                R8(0x062, &mm);                          // RESULT_RANGE_VAL
                W8(0x015, 0x07);                         // clear interrupts
                return mm;
            }
            vTaskDelay(pdMS_TO_TICKS(5));
        }
        return -1;
    }

    bool ReadClimate(float& temp_c, float& humidity) {
        if (!sht_ok_) return false;
        Lock l(lock_);
        uint8_t cmd[2] = {0x24, 0x00};                    // high repeatability, no clock stretching
        if (i2c_master_transmit(sht_, cmd, 2, 100) != ESP_OK) return false;
        vTaskDelay(pdMS_TO_TICKS(20));
        uint8_t d[6];
        if (i2c_master_receive(sht_, d, 6, 100) != ESP_OK) return false;
        if (Crc(d) != d[2] || Crc(d + 3) != d[5]) return false;
        temp_c = -45.0f + 175.0f * ((d[0] << 8) | d[1]) / 65535.0f;
        humidity = 100.0f * ((d[3] << 8) | d[4]) / 65535.0f;
        return true;
    }

private:
    struct Lock { SemaphoreHandle_t m; Lock(SemaphoreHandle_t x) : m(x) { xSemaphoreTake(m, portMAX_DELAY); } ~Lock() { xSemaphoreGive(m); } };
    i2c_master_bus_handle_t bus_ = nullptr;
    i2c_master_dev_handle_t tof_ = nullptr, sht_ = nullptr;
    SemaphoreHandle_t lock_ = nullptr;
    bool tof_ok_ = false, sht_ok_ = false;

    bool AddDev(uint8_t addr, i2c_master_dev_handle_t* h) {
        if (i2c_master_probe(bus_, addr, 100) != ESP_OK) return false;
        i2c_device_config_t d = {};
        d.dev_addr_length = I2C_ADDR_BIT_LEN_7;
        d.device_address = addr;
        d.scl_speed_hz = 100000;
        return i2c_master_bus_add_device(bus_, &d, h) == ESP_OK;
    }
    bool W8(uint16_t reg, uint8_t v) {
        uint8_t b[3] = {(uint8_t)(reg >> 8), (uint8_t)reg, v};
        return i2c_master_transmit(tof_, b, 3, 100) == ESP_OK;
    }
    bool R8(uint16_t reg, uint8_t* v) {
        uint8_t b[2] = {(uint8_t)(reg >> 8), (uint8_t)reg};
        return i2c_master_transmit_receive(tof_, b, 2, v, 1, 100) == ESP_OK;
    }
    bool TofInit() {
        uint8_t fresh = 0;
        if (!R8(0x016, &fresh)) return false;           // SYSTEM_FRESH_OUT_OF_RESET
        if (fresh == 1) {
            // Bộ cài đặt khuyến nghị của ST (AN4545)
            static const uint16_t regs[][2] = {
                {0x0207, 0x01}, {0x0208, 0x01}, {0x0096, 0x00}, {0x0097, 0xfd}, {0x00e3, 0x00}, {0x00e4, 0x04},
                {0x00e5, 0x02}, {0x00e6, 0x01}, {0x00e7, 0x03}, {0x00f5, 0x02}, {0x00d9, 0x05}, {0x00db, 0xce},
                {0x00dc, 0x03}, {0x00dd, 0xf8}, {0x009f, 0x00}, {0x00a3, 0x3c}, {0x00b7, 0x00}, {0x00bb, 0x3c},
                {0x00b2, 0x09}, {0x00ca, 0x09}, {0x0198, 0x01}, {0x01b0, 0x17}, {0x01ad, 0x00}, {0x00ff, 0x05},
                {0x0100, 0x05}, {0x0199, 0x05}, {0x01a6, 0x1b}, {0x01ac, 0x3e}, {0x01a7, 0x1f}, {0x0030, 0x00},
                // cài đặt công khai
                {0x0011, 0x10}, {0x010a, 0x30}, {0x003f, 0x46}, {0x0031, 0xFF}, {0x0041, 0x63}, {0x002e, 0x01},
                {0x001b, 0x09}, {0x003e, 0x31}, {0x0014, 0x24}, {0x0016, 0x00},
            };
            for (auto& r : regs) if (!W8(r[0], (uint8_t)r[1])) return false;
        }
        return true;
    }
    static uint8_t Crc(const uint8_t* d) {
        uint8_t c = 0xFF;
        for (int i = 0; i < 2; i++) {
            c ^= d[i];
            for (int b = 0; b < 8; b++) c = (c & 0x80) ? (uint8_t)((c << 1) ^ 0x31) : (uint8_t)(c << 1);
        }
        return c;
    }
};

// ======================= IR điều hòa (học + phát) =======================
// Lưu tín hiệu thô (thời gian mức cao/thấp, đơn vị µs) vào NVS theo tên lệnh.
class IrAircon {
public:
    bool Init() {
        rmt_rx_channel_config_t rx = {};
        rx.gpio_num = IR_RX_GPIO;
        rx.clk_src = RMT_CLK_SRC_DEFAULT;
        rx.resolution_hz = 1000000;
        rx.mem_block_symbols = 1024;
        rx.flags.with_dma = true;
        if (rmt_new_rx_channel(&rx, &rx_) != ESP_OK) {
            // không có DMA thì dùng bộ nhớ trong
            rx.flags.with_dma = false;
            rx.mem_block_symbols = 192;
            if (rmt_new_rx_channel(&rx, &rx_) != ESP_OK) return false;
        }
        rmt_rx_event_callbacks_t cbs = {};
        cbs.on_recv_done = OnRecv;
        rx_queue_ = xQueueCreate(1, sizeof(rmt_rx_done_event_data_t));
        rmt_rx_register_event_callbacks(rx_, &cbs, rx_queue_);
        rmt_enable(rx_);

        rmt_tx_channel_config_t tx = {};
        tx.gpio_num = IR_TX_GPIO;
        tx.clk_src = RMT_CLK_SRC_DEFAULT;
        tx.resolution_hz = 1000000;
        tx.mem_block_symbols = 64;
        tx.trans_queue_depth = 4;
        if (rmt_new_tx_channel(&tx, &tx_) != ESP_OK) return false;
        rmt_carrier_config_t car = {};
        car.frequency_hz = 38000;
        car.duty_cycle = 0.33f;
        rmt_apply_carrier(tx_, &car);
        rmt_copy_encoder_config_t ec = {};
        rmt_new_copy_encoder(&ec, &enc_);
        rmt_enable(tx_);
        buf_.resize(1024);
        ok_ = true;
        return true;
    }
    bool ok() const { return ok_; }

    // Chờ tối đa timeout_ms để bắt tín hiệu remote. Trả về số xung đã lưu, 0 nếu không bắt được.
    int Learn(const std::string& name, int timeout_ms) {
        if (!ok_) return 0;
        std::vector<uint32_t> frames;                  // các symbol thô, khung sau cách khung trước bằng 1 symbol "gap"
        TickType_t deadline = xTaskGetTickCount() + pdMS_TO_TICKS(timeout_ms);
        bool got_any = false;
        while (true) {
            rmt_receive_config_t rc = {};
            rc.signal_range_min_ns = 1250;
            rc.signal_range_max_ns = 30 * 1000 * 1000;  // im lặng > 30 ms = hết khung
            xQueueReset(rx_queue_);
            if (rmt_receive(rx_, buf_.data(), buf_.size() * sizeof(rmt_symbol_word_t), &rc) != ESP_OK) break;
            TickType_t wait = got_any ? pdMS_TO_TICKS(250) : (deadline > xTaskGetTickCount() ? deadline - xTaskGetTickCount() : 0);
            rmt_rx_done_event_data_t ev;
            if (xQueueReceive(rx_queue_, &ev, wait) != pdTRUE) {
                rmt_disable(rx_); rmt_enable(rx_);       // hủy lần nhận đang chờ
                break;
            }
            if (ev.num_symbols < 8) continue;           // nhiễu
            if (got_any) frames.push_back(GapSymbol(40000));
            for (size_t i = 0; i < ev.num_symbols; i++) frames.push_back(ev.received_symbols[i].val);
            got_any = true;
            if (frames.size() > 1800) break;
        }
        if (!got_any) return 0;
        if (!Save(name, frames)) return 0;
        return (int)frames.size();
    }

    bool Send(const std::string& name) {
        if (!ok_) return false;
        std::vector<uint32_t> s;
        if (!Load(name, s) || s.empty()) return false;
        // Tách theo symbol gap để chờ đúng khoảng nghỉ giữa các khung
        size_t start = 0;
        for (size_t i = 0; i <= s.size(); i++) {
            bool end = (i == s.size()) || IsGap(s[i]);
            if (!end) continue;
            if (i > start) {
                rmt_transmit_config_t tc = {};
                rmt_transmit(tx_, enc_, &s[start], (i - start) * sizeof(uint32_t), &tc);
                rmt_tx_wait_all_done(tx_, 1000);
            }
            if (i < s.size()) vTaskDelay(pdMS_TO_TICKS(40));
            start = i + 1;
        }
        return true;
    }

    std::vector<std::string> List() {
        std::vector<std::string> out;
        nvs_iterator_t it = nullptr;
        esp_err_t e = nvs_entry_find(NVS_DEFAULT_PART_NAME, "ir_codes", NVS_TYPE_BLOB, &it);
        while (e == ESP_OK) {
            nvs_entry_info_t info;
            nvs_entry_info(it, &info);
            out.push_back(info.key);
            e = nvs_entry_next(&it);
        }
        nvs_release_iterator(it);
        return out;
    }

    bool Erase(const std::string& name) {
        nvs_handle_t h;
        if (nvs_open("ir_codes", NVS_READWRITE, &h) != ESP_OK) return false;
        bool ok = nvs_erase_key(h, Key(name).c_str()) == ESP_OK;
        nvs_commit(h); nvs_close(h);
        return ok;
    }

private:
    bool ok_ = false;
    rmt_channel_handle_t rx_ = nullptr, tx_ = nullptr;
    rmt_encoder_handle_t enc_ = nullptr;
    QueueHandle_t rx_queue_ = nullptr;
    std::vector<rmt_symbol_word_t> buf_;

    static bool OnRecv(rmt_channel_handle_t, const rmt_rx_done_event_data_t* ed, void* ctx) {
        BaseType_t w = pdFALSE;
        xQueueSendFromISR((QueueHandle_t)ctx, ed, &w);
        return w == pdTRUE;
    }
    // Symbol đặc biệt đánh dấu khoảng nghỉ giữa 2 khung: duration0 = 0x7FFF, level0 = 0, duration1 = 0
    static uint32_t GapSymbol(int) { rmt_symbol_word_t s = {}; s.duration0 = 0x7FFF; s.level0 = 0; s.duration1 = 0; s.level1 = 0; return s.val; }
    static bool IsGap(uint32_t v) { rmt_symbol_word_t s; s.val = v; return s.duration0 == 0x7FFF && s.duration1 == 0 && s.level0 == 0; }
    static std::string Key(const std::string& name) {
        std::string k;
        for (char c : name) { if (isalnum((unsigned char)c)) k += (char)tolower(c); else if (c == ' ' || c == '_' || c == '-') k += '_'; }
        if (k.empty()) k = "lenh";
        if (k.size() > 15) k.resize(15);
        return k;
    }
    bool Save(const std::string& name, const std::vector<uint32_t>& s) {
        nvs_handle_t h;
        if (nvs_open("ir_codes", NVS_READWRITE, &h) != ESP_OK) return false;
        bool ok = nvs_set_blob(h, Key(name).c_str(), s.data(), s.size() * sizeof(uint32_t)) == ESP_OK;
        nvs_commit(h); nvs_close(h);
        return ok;
    }
    bool Load(const std::string& name, std::vector<uint32_t>& s) {
        nvs_handle_t h;
        if (nvs_open("ir_codes", NVS_READONLY, &h) != ESP_OK) return false;
        size_t len = 0;
        bool ok = nvs_get_blob(h, Key(name).c_str(), nullptr, &len) == ESP_OK && len > 0;
        if (ok) { s.resize(len / sizeof(uint32_t)); ok = nvs_get_blob(h, Key(name).c_str(), s.data(), &len) == ESP_OK; }
        nvs_close(h);
        return ok;
    }
};

#endif // QBK_ROBOT_HW_H
