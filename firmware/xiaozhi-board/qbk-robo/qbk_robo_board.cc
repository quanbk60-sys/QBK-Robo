// QBK-Robo: robot bánh xích khung đồng, ESP32-S3 N16R8 + OV3660.
#include "wifi_board.h"
#include "codecs/no_audio_codec.h"
#include "display/lcd_display.h"
#include "application.h"
#include "button.h"
#include "config.h"
#include "mcp_server.h"
#include "esp32_camera.h"
#include "adc_battery_monitor.h"
#include "robot_hw.h"
#include "fun.h"
#include "assets/lang_config.h"

#include <esp_log.h>
#include <esp_lcd_panel_vendor.h>
#include <esp_lcd_panel_io.h>
#include <esp_lcd_panel_ops.h>
#include <driver/spi_common.h>
#include <cJSON.h>
#include <atomic>
#include <esp_random.h>

#define TAG "QbkRobo"

class QbkRoboBoard : public WifiBoard {
private:
    Button touch_button_;
    LcdDisplay* display_ = nullptr;
    Esp32Camera* camera_ = nullptr;
    AdcBatteryMonitor* battery_ = nullptr;
    Motors motors_;
    SensorBus sensors_;
    IrAircon ir_;
    FunShow fun_{motors_, sensors_};
    std::atomic<int64_t> move_until_us_{0};
    std::atomic<bool> moving_forward_{false};

    void InitializeSpi() {
        spi_bus_config_t buscfg = {};
        buscfg.mosi_io_num = DISPLAY_MOSI_PIN;
        buscfg.miso_io_num = GPIO_NUM_NC;
        buscfg.sclk_io_num = DISPLAY_CLK_PIN;
        buscfg.quadwp_io_num = GPIO_NUM_NC;
        buscfg.quadhd_io_num = GPIO_NUM_NC;
        buscfg.max_transfer_sz = DISPLAY_WIDTH * DISPLAY_HEIGHT * sizeof(uint16_t);
        ESP_ERROR_CHECK(spi_bus_initialize(SPI3_HOST, &buscfg, SPI_DMA_CH_AUTO));
    }

    void InitializeLcdDisplay() {
        esp_lcd_panel_io_handle_t panel_io = nullptr;
        esp_lcd_panel_handle_t panel = nullptr;
        esp_lcd_panel_io_spi_config_t io_config = {};
        io_config.cs_gpio_num = DISPLAY_CS_PIN;
        io_config.dc_gpio_num = DISPLAY_DC_PIN;
        io_config.spi_mode = DISPLAY_SPI_MODE;
        io_config.pclk_hz = DISPLAY_SPI_HZ;
        io_config.trans_queue_depth = 10;
        io_config.lcd_cmd_bits = 8;
        io_config.lcd_param_bits = 8;
        ESP_ERROR_CHECK(esp_lcd_new_panel_io_spi(SPI3_HOST, &io_config, &panel_io));

        esp_lcd_panel_dev_config_t panel_config = {};
        panel_config.reset_gpio_num = DISPLAY_RST_PIN;
        panel_config.rgb_ele_order = DISPLAY_RGB_ORDER;
        panel_config.bits_per_pixel = 16;
        ESP_ERROR_CHECK(esp_lcd_new_panel_st7789(panel_io, &panel_config, &panel));   // ST7735S dùng chung lệnh cơ bản
        esp_lcd_panel_reset(panel);
        vTaskDelay(pdMS_TO_TICKS(120));   // ST7735S cần 120 ms sau reset mới nhận lệnh thức dậy
        esp_lcd_panel_init(panel);
        esp_lcd_panel_invert_color(panel, DISPLAY_INVERT_COLOR);
        esp_lcd_panel_swap_xy(panel, DISPLAY_SWAP_XY);
        esp_lcd_panel_mirror(panel, DISPLAY_MIRROR_X, DISPLAY_MIRROR_Y);
        esp_lcd_panel_disp_on_off(panel, true);
        display_ = new SpiLcdDisplay(panel_io, panel, DISPLAY_WIDTH, DISPLAY_HEIGHT,
                                     DISPLAY_OFFSET_X, DISPLAY_OFFSET_Y, DISPLAY_MIRROR_X, DISPLAY_MIRROR_Y, DISPLAY_SWAP_XY);
    }

    void InitializeCamera() {
        camera_config_t config = {};
        config.pin_d0 = CAMERA_PIN_D0;
        config.pin_d1 = CAMERA_PIN_D1;
        config.pin_d2 = CAMERA_PIN_D2;
        config.pin_d3 = CAMERA_PIN_D3;
        config.pin_d4 = CAMERA_PIN_D4;
        config.pin_d5 = CAMERA_PIN_D5;
        config.pin_d6 = CAMERA_PIN_D6;
        config.pin_d7 = CAMERA_PIN_D7;
        config.pin_xclk = CAMERA_PIN_XCLK;
        config.pin_pclk = CAMERA_PIN_PCLK;
        config.pin_vsync = CAMERA_PIN_VSYNC;
        config.pin_href = CAMERA_PIN_HREF;
        config.pin_sccb_sda = CAMERA_PIN_SIOD;
        config.pin_sccb_scl = CAMERA_PIN_SIOC;
        config.sccb_i2c_port = 0;
        config.pin_pwdn = CAMERA_PIN_PWDN;
        config.pin_reset = CAMERA_PIN_RESET;
        config.xclk_freq_hz = XCLK_FREQ_HZ;
        config.ledc_timer = LEDC_TIMER_0;
        config.ledc_channel = LEDC_CHANNEL_0;
        config.pixel_format = PIXFORMAT_RGB565;
        config.frame_size = FRAMESIZE_VGA;
        config.jpeg_quality = 12;
        config.fb_count = 1;
        config.fb_location = CAMERA_FB_IN_PSRAM;
        config.grab_mode = CAMERA_GRAB_WHEN_EMPTY;
        camera_ = new Esp32Camera(config);
    }

    void InitializeButtons() {
        touch_button_.OnClick([this]() {
            if (fun_.busy()) { fun_.Stop(); return; }      // chạm để dừng nhảy / tắt nhạc
            auto& app = Application::GetInstance();
            if (app.GetDeviceState() == kDeviceStateStarting) {
                EnterWifiConfigMode();
                return;
            }
            app.ToggleChatState();
        });
        // Giữ nút chạm 5 giây: vào chế độ cài WiFi
        touch_button_.OnLongPress([this]() { EnterWifiConfigMode(); });
    }

    // Tác vụ giám sát chuyển động: hết thời gian thì dừng, đang tiến mà có vật cản thì dừng.
    static void MotionTask(void* arg) {
        auto* self = static_cast<QbkRoboBoard*>(arg);
        while (true) {
            int64_t until = self->move_until_us_.load();
            if (until != 0) {
                bool stop = esp_timer_get_time() >= until;
                if (!stop && self->moving_forward_.load() && self->sensors_.tof_ok()) {
                    int mm = self->sensors_.ReadDistanceMm();
                    if (mm >= 0 && mm < OBSTACLE_STOP_MM) {
                        ESP_LOGW(TAG, "Vat can %d mm, dung lai", mm);
                        stop = true;
                    }
                }
                if (stop) {
                    self->motors_.Stop();
                    self->move_until_us_ = 0;
                    self->moving_forward_ = false;
                }
            }
            vTaskDelay(pdMS_TO_TICKS(40));
        }
    }

    void StartMove(int left, int right, int duration_ms, bool forward) {
        moving_forward_ = forward;
        motors_.Set(left, right);
        move_until_us_ = esp_timer_get_time() + (int64_t)duration_ms * 1000;
    }

    void InitializeTools() {
        auto& mcp = McpServer::GetInstance();

        mcp.AddTool("self.robot.move",
            "Di chuyển robot bánh xích. direction: forward (tiến), backward (lùi), left (quay trái tại chỗ), right (quay phải tại chỗ). "
            "duration_ms: thời gian chạy (mili giây). speed: tốc độ 20-100 (%). Khi tiến, robot tự dừng nếu gặp vật cản gần.",
            PropertyList({
                Property("direction", kPropertyTypeString),
                Property("duration_ms", kPropertyTypeInteger, 1000, 100, 10000),
                Property("speed", kPropertyTypeInteger, 70, 20, 100),
            }),
            [this](const PropertyList& p) -> ToolResult {
                std::string dir = p["direction"].value<std::string>();
                int ms = p["duration_ms"].value<int>();
                int sp = p["speed"].value<int>();
                if (fun_.busy()) fun_.Stop();            // đang nhảy thì dừng nhảy trước
                if (dir == "forward") {
                    int mm = sensors_.ReadDistanceMm();
                    if (mm >= 0 && mm < OBSTACLE_STOP_MM) return std::string("{\"moved\":false,\"reason\":\"vat can phia truoc\",\"distance_mm\":") + std::to_string(mm) + "}";
                    StartMove(sp, sp, ms, true);
                } else if (dir == "backward") {
                    StartMove(-sp, -sp, ms, false);
                } else if (dir == "left") {
                    StartMove(-sp, sp, ms, false);
                } else if (dir == "right") {
                    StartMove(sp, -sp, ms, false);
                } else {
                    return std::unexpected(std::string("direction phải là forward, backward, left hoặc right"));
                }
                return true;
            });

        mcp.AddTool("self.robot.stop", "Dừng robot ngay lập tức.", PropertyList(),
            [this](const PropertyList&) -> ToolResult {
                fun_.Stop();
                motors_.Stop();
                move_until_us_ = 0;
                moving_forward_ = false;
                return true;
            });

        // ---------- Nhảy múa, giải trí ----------
        std::string styles, songs;
        for (auto& d : kDanceStyles) styles += std::string(d.id) + " (" + d.title + "), ";
        for (auto& g : kSongs) songs += std::string(g.id) + " (" + g.title + "), ";

        mcp.AddTool("self.robot.dance",
            "Cho robot nhảy múa bằng bánh xích, kèm biểu cảm trên màn. Robot nhảy ở chế độ nền nên bạn có thể vừa hát hoặc nói chuyện trong lúc robot nhảy. "
            "style: một trong " + styles + "hoặc random. seconds: số giây nhảy. bpm: nhịp (80-160), khớp với bài bạn đang hát nếu có. "
            "Người dùng chạm vào đầu robot là dừng.",
            PropertyList({
                Property("style", kPropertyTypeString, std::string("random")),
                Property("seconds", kPropertyTypeInteger, 15, 3, 60),
                Property("bpm", kPropertyTypeInteger, 120, 80, 160),
            }),
            [this](const PropertyList& p) -> ToolResult {
                std::string id = p["style"].value<std::string>();
                const DanceStyle* st = FunShow::FindStyle(id);
                if (!st) st = &kDanceStyles[esp_random() % (sizeof(kDanceStyles) / sizeof(kDanceStyles[0]))];
                move_until_us_ = 0;
                if (!fun_.StartDance(st, p["seconds"].value<int>(), p["bpm"].value<int>())) return std::unexpected(std::string("Không bắt đầu nhảy được"));
                return std::string("{\"dancing\":\"") + st->title + "\"}";
            });

        mcp.AddTool("self.fun.play_song",
            "Phát một bài nhạc có sẵn trong robot và nhảy theo nhạc. Nhạc bắt đầu sau khi bạn nói xong câu trả lời, vì vậy chỉ nói một câu ngắn kiểu: Nhạc lên nào! "
            "song: một trong " + songs + "hoặc random. dance: điệu nhảy (như self.robot.dance), none để chỉ phát nhạc, random để chọn ngẫu nhiên. "
            "Dùng khi người dùng muốn nghe nhạc, mừng sinh nhật, muốn robot biểu diễn.",
            PropertyList({
                Property("song", kPropertyTypeString, std::string("random")),
                Property("dance", kPropertyTypeString, std::string("random")),
            }),
            [this](const PropertyList& p) -> ToolResult {
                const SongInfo* sg = FunShow::FindSong(p["song"].value<std::string>());
                if (!sg) sg = &kSongs[esp_random() % (sizeof(kSongs) / sizeof(kSongs[0]))];
                std::string d = p["dance"].value<std::string>();
                const DanceStyle* st = nullptr;
                if (d != "none") { st = FunShow::FindStyle(d); if (!st) st = &kDanceStyles[esp_random() % (sizeof(kDanceStyles) / sizeof(kDanceStyles[0]))]; }
                move_until_us_ = 0;
                if (!fun_.StartSong(sg, st)) return std::unexpected(std::string("Không phát được nhạc"));
                return std::string("{\"song\":\"") + sg->title + "\",\"dance\":\"" + (st ? st->title : "không") + "\"}";
            });

        mcp.AddTool("self.fun.list", "Liệt kê các bài nhạc và điệu nhảy robot có sẵn.", PropertyList(),
            [this](const PropertyList&) -> ToolResult {
                cJSON* o = cJSON_CreateObject();
                cJSON* a = cJSON_AddArrayToObject(o, "songs");
                for (auto& g : kSongs) cJSON_AddItemToArray(a, cJSON_CreateString((std::string(g.id) + ": " + g.title).c_str()));
                cJSON* b = cJSON_AddArrayToObject(o, "dances");
                for (auto& d : kDanceStyles) cJSON_AddItemToArray(b, cJSON_CreateString((std::string(d.id) + ": " + d.title).c_str()));
                return o;
            });

        mcp.AddTool("self.robot.get_distance", "Đo khoảng cách tới vật cản phía trước robot (mm, đo được tới khoảng 200 mm).", PropertyList(),
            [this](const PropertyList&) -> ToolResult {
                int mm = sensors_.ReadDistanceMm();
                if (mm < 0) return std::unexpected(std::string("Không đọc được cảm biến khoảng cách"));
                if (mm == TOF_NO_TARGET) return std::string("{\"obstacle\":false,\"note\":\"khong co vat nao trong khoang 20 cm phia truoc\"}");
                return std::string("{\"obstacle\":true,\"distance_mm\":") + std::to_string(mm) + "}";
            });

        mcp.AddTool("self.room.get_climate", "Đọc nhiệt độ (°C) và độ ẩm (%) trong phòng từ cảm biến SHT31 của robot.", PropertyList(),
            [this](const PropertyList&) -> ToolResult {
                float t = 0, h = 0;
                if (!sensors_.ReadClimate(t, h)) return std::unexpected(std::string("Không đọc được cảm biến nhiệt độ"));
                char buf[80];
                snprintf(buf, sizeof(buf), "{\"temperature_c\":%.1f,\"humidity_percent\":%.0f}", t, h);
                return std::string(buf);
            });

        mcp.AddTool("self.aircon.learn",
            "Học một lệnh từ remote điều hòa (máy lạnh). Gọi tool này rồi nhắc người dùng chĩa remote vào nóc robot và bấm nút trong vòng 12 giây; robot báo trên màn khi xong. "
            "name: tên lệnh ngắn, không dấu, ví dụ: bat, tat, 26do, 24do, quatmanh.",
            PropertyList({Property("name", kPropertyTypeString)}),
            [this](const PropertyList& p) -> ToolResult {
                std::string name = p["name"].value<std::string>();
                bool started = ir_.LearnAsync(name, 12000, [](const std::string& nm, int n) {
                    auto& app = Application::GetInstance();
                    std::string msg = n > 0 ? "Đã học lệnh: " + nm : (n < 0 ? "Bộ nhớ lệnh đầy, xóa bớt lệnh cũ" : "Chưa bắt được remote, thử lại nhé");
                    app.Schedule([msg, n]() {
                        auto* d = Board::GetInstance().GetDisplay();
                        if (d) { d->SetEmotion(n > 0 ? "happy" : "confused"); d->SetChatMessage("system", msg.c_str()); }
                    });
                    if (n > 0) app.PlaySound(Lang::Sounds::OGG_SUCCESS);
                });
                if (!started) return std::unexpected(std::string("Robot đang học một lệnh khác, đợi vài giây rồi thử lại"));
                return std::string("{\"status\":\"dang_cho_remote_12_giay\",\"name\":\"") + name +
                       "\",\"note\":\"Nhắc người dùng chĩa remote vào nóc robot (cách 5-20 cm) và bấm nút ngay. Robot sẽ kêu ting và hiện chữ trên màn khi học xong.\"}";
            });

        mcp.AddTool("self.aircon.send",
            "Phát một lệnh điều hòa đã học (ví dụ bật, tắt, chỉnh nhiệt độ). name: tên lệnh đã học. Gọi self.aircon.list để xem các lệnh có sẵn.",
            PropertyList({Property("name", kPropertyTypeString)}),
            [this](const PropertyList& p) -> ToolResult {
                std::string name = p["name"].value<std::string>();
                if (!ir_.Send(name)) return std::unexpected(std::string("Chưa học lệnh này. Hãy học lệnh trước bằng self.aircon.learn."));
                return true;
            });

        mcp.AddTool("self.aircon.list", "Liệt kê các lệnh điều hòa đã học.", PropertyList(),
            [this](const PropertyList&) -> ToolResult {
                cJSON* arr = cJSON_CreateArray();
                for (auto& n : ir_.List()) cJSON_AddItemToArray(arr, cJSON_CreateString(n.c_str()));
                return arr;
            });

        mcp.AddTool("self.aircon.forget", "Xóa một lệnh điều hòa đã học.", PropertyList({Property("name", kPropertyTypeString)}),
            [this](const PropertyList& p) -> ToolResult {
                return ir_.Erase(p["name"].value<std::string>());
            });
    }

public:
    QbkRoboBoard() : touch_button_(TOUCH_BUTTON_GPIO, true /* TTP223: mức cao khi chạm */, 5000) {
        motors_.Init();          // đầu tiên: giữ motor đứng yên
        InitializeSpi();
        InitializeLcdDisplay();
        InitializeButtons();
        InitializeCamera();
        sensors_.Init();
        if (!ir_.Init()) ESP_LOGW(TAG, "Khong khoi tao duoc IR");
        battery_ = new AdcBatteryMonitor(BATTERY_ADC_UNIT, BATTERY_ADC_CHANNEL, BATTERY_R_UPPER, BATTERY_R_LOWER, GPIO_NUM_NC);
        xTaskCreate(MotionTask, "qbk_motion", 4096, this, 5, nullptr);
        InitializeTools();
    }

    virtual AudioCodec* GetAudioCodec() override {
        static NoAudioCodecDuplex audio_codec(AUDIO_INPUT_SAMPLE_RATE, AUDIO_OUTPUT_SAMPLE_RATE,
            AUDIO_I2S_GPIO_BCLK, AUDIO_I2S_GPIO_WS, AUDIO_I2S_GPIO_DOUT, AUDIO_I2S_GPIO_DIN);
        return &audio_codec;
    }

    virtual Display* GetDisplay() override { return display_; }
    virtual Camera* GetCamera() override { return camera_; }

    virtual bool GetBatteryLevel(int& level, bool& charging, bool& discharging) override {
        if (!battery_) return false;
        level = battery_->GetBatteryLevel();
        charging = battery_->IsCharging();
        discharging = battery_->IsDischarging();
        return true;
    }
};

DECLARE_BOARD(QbkRoboBoard);
