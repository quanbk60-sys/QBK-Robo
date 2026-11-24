// QBK-Robo: nhảy múa và giải trí (phát nhạc nhúng sẵn + điệu nhảy bánh xích + biểu cảm trên màn).
#ifndef QBK_FUN_H
#define QBK_FUN_H

#include <freertos/FreeRTOS.h>
#include <freertos/task.h>
#include <esp_timer.h>
#include <esp_log.h>
#include <atomic>
#include <string>
#include <functional>

#include "application.h"
#include "board.h"
#include "display/display.h"
#include "robot_hw.h"
#include "songs_data.h"

// Một bước nhảy: tốc độ bánh trái, bánh phải (-100..100), số phách
struct DanceStep { int8_t l, r; float beats; };

// Các điệu nhảy. Hạn chế đi tới, chủ yếu lắc, xoay tại chỗ để robot không chạy xa.
static const DanceStep kDanceLacLu[] = {{-60, 60, 0.5f}, {60, -60, 0.5f}, {-60, 60, 0.5f}, {60, -60, 0.5f}, {0, 0, 0.5f}, {50, 50, 0.25f}, {-50, -50, 0.25f}, {0, 0, 0.5f}};
static const DanceStep kDanceXoay[]  = {{80, -80, 2.0f}, {0, 0, 0.5f}, {-80, 80, 2.0f}, {0, 0, 0.5f}};
static const DanceStep kDanceTienLui[] = {{55, 55, 0.5f}, {0, 0, 0.5f}, {-55, -55, 0.5f}, {0, 0, 0.5f}, {-70, 70, 0.5f}, {70, -70, 0.5f}, {0, 0, 1.0f}};
static const DanceStep kDanceRobot[] = {{70, -70, 0.25f}, {0, 0, 0.75f}, {-70, 70, 0.25f}, {0, 0, 0.75f}, {60, 60, 0.25f}, {0, 0, 0.75f}, {-60, -60, 0.25f}, {0, 0, 0.75f}};
static const DanceStep kDanceVuiVe[] = {{-60, 60, 0.25f}, {60, -60, 0.25f}, {-60, 60, 0.25f}, {60, -60, 0.25f}, {90, -90, 1.0f}, {0, 0, 0.5f}, {-90, 90, 1.0f}, {0, 0, 0.5f}};

struct DanceStyle { const char* id; const char* title; const DanceStep* steps; int count; };
#define DSTYLE(id, title, arr) {id, title, arr, (int)(sizeof(arr) / sizeof(arr[0]))}
static const DanceStyle kDanceStyles[] = {
    DSTYLE("lac_lu", "Lắc lư", kDanceLacLu),
    DSTYLE("xoay", "Xoay vòng", kDanceXoay),
    DSTYLE("tien_lui", "Tiến lùi", kDanceTienLui),
    DSTYLE("robot", "Kiểu robot", kDanceRobot),
    DSTYLE("vui_ve", "Vui vẻ", kDanceVuiVe),
};

static const char* kDanceEmotions[] = {"happy", "laughing", "cool", "winking", "loving", "funny", "silly", "confident"};

class FunShow {
public:
    FunShow(Motors& m, SensorBus& s) : motors_(m), sensors_(s) {}

    static const DanceStyle* FindStyle(const std::string& id) {
        for (auto& d : kDanceStyles) if (id == d.id) return &d;
        return nullptr;
    }
    static const SongInfo* FindSong(const std::string& id) {
        for (auto& s : kSongs) if (id == s.id) return &s;
        return nullptr;
    }
    bool busy() const { return running_.load(); }

    // Nhảy không nhạc, chạy nền để AI vừa hát/nói vừa nhảy.
    bool StartDance(const DanceStyle* style, int seconds, int bpm) {
        if (running_.load()) Stop();
        if (running_.load()) return false;      // tác vụ cũ chưa thoát hẳn
        req_style_ = style; req_song_ = nullptr; req_seconds_ = seconds; req_bpm_ = bpm;
        return Launch();
    }
    // Phát nhạc + nhảy theo nhịp. Đợi AI nói xong câu trả lời rồi mới bắt đầu.
    bool StartSong(const SongInfo* song, const DanceStyle* style) {
        if (running_.load()) Stop();
        if (running_.load()) return false;
        req_style_ = style; req_song_ = song; req_seconds_ = (int)(song->seconds + 0.5f); req_bpm_ = song->bpm;
        return Launch();
    }
    // Chỉ báo dừng, không chờ (dùng trong callback nút bấm). Tác vụ nhảy tự dừng motor và nhạc trong ~50 ms.
    void RequestStop() { cancel_ = true; motors_.Stop(); }
    void Stop() {
        cancel_ = true;
        // Đợi tác vụ cũ thoát hẳn (dọn nhạc tối đa ~1 s) để nó không đè lên tác vụ mới
        for (int i = 0; i < 150 && running_.load(); i++) vTaskDelay(pdMS_TO_TICKS(20));
        motors_.Stop();
    }

private:
    Motors& motors_;
    SensorBus& sensors_;
    std::atomic<bool> running_{false}, cancel_{false};
    const DanceStyle* req_style_ = nullptr;
    const SongInfo* req_song_ = nullptr;
    int req_seconds_ = 10, req_bpm_ = 120;

    bool Launch() {
        cancel_ = false;
        running_ = true;
        if (xTaskCreate(Task, "qbk_fun", 6144, this, 4, nullptr) != pdPASS) { running_ = false; return false; }
        return true;
    }

    static inline std::atomic<bool> sound_running_{false};
    static void SoundTask(void* arg) {
        auto* song = static_cast<const SongInfo*>(arg);
        Application::GetInstance().PlaySound(std::string_view(reinterpret_cast<const char*>(song->data), song->size));
        sound_running_ = false;
        vTaskDelete(nullptr);
    }

    static void SetFace(const char* emotion, const std::string& msg) {
        auto& app = Application::GetInstance();
        std::string m = msg; std::string e = emotion;
        app.Schedule([e, m]() {
            auto* d = Board::GetInstance().GetDisplay();
            if (!d) return;
            d->SetEmotion(e.c_str());
            if (!m.empty()) d->SetChatMessage("system", m.c_str());
        });
    }

    static void Task(void* arg) {
        auto* self = static_cast<FunShow*>(arg);
        auto& app = Application::GetInstance();
        const SongInfo* song = self->req_song_;
        const DanceStyle* style = self->req_style_;

        if (song) {
            // Đợi AI bắt đầu nói (tối đa 8 s) rồi nói xong (tối đa 20 s), sau đó tạm dừng nghe để micro không thu tiếng nhạc.
            int64_t t0 = esp_timer_get_time();
            while (!self->cancel_ && app.GetDeviceState() != kDeviceStateSpeaking && esp_timer_get_time() - t0 < 8000000) vTaskDelay(pdMS_TO_TICKS(100));
            t0 = esp_timer_get_time();
            while (!self->cancel_ && app.GetDeviceState() == kDeviceStateSpeaking && esp_timer_get_time() - t0 < 20000000) vTaskDelay(pdMS_TO_TICKS(100));
            if (!self->cancel_ && app.GetDeviceState() == kDeviceStateListening) {
                app.StopListening();                 // báo máy chủ dừng nghe rồi về chế độ nghỉ
                vTaskDelay(pdMS_TO_TICKS(400));
            }
            if (!self->cancel_) {
                SetFace("happy", std::string("♪ ") + song->title);
                // Nạp nhạc ở tác vụ riêng: PlaySound chờ hàng đợi giải mã nên chạy chung sẽ làm điệu nhảy trễ
                self->sound_running_ = true;
                xTaskCreate(SoundTask, "qbk_snd", 4096, (void*)song, 4, nullptr);
            }
        }

        const float beat_ms = 60000.0f / (float)self->req_bpm_;
        const int64_t end = esp_timer_get_time() + (int64_t)self->req_seconds_ * 1000000;
        int step = 0, emo = 0;
        int64_t next_face = 0;
        while (!self->cancel_ && esp_timer_get_time() < end) {
            if (!style) { vTaskDelay(pdMS_TO_TICKS(50)); continue; }   // chỉ phát nhạc: vẫn đợi hết bài để chạm là tắt được
            const DanceStep& s = style->steps[step % style->count];
            int l = s.l, r = s.r;
            // Không lao về phía vật cản
            if (l > 0 && r > 0) {
                int mm = self->sensors_.ReadDistanceMm();
                if (mm >= 0 && mm < OBSTACLE_STOP_MM + 40) { l = -l; r = -r; }
            }
            self->motors_.Set(l, r);
            if (esp_timer_get_time() >= next_face) {
                SetFace(kDanceEmotions[emo++ % (sizeof(kDanceEmotions) / sizeof(kDanceEmotions[0]))], "");
                next_face = esp_timer_get_time() + (int64_t)(beat_ms * 2) * 1000;
            }
            int wait = (int)(s.beats * beat_ms);
            while (wait > 0 && !self->cancel_) { int d = wait > 50 ? 50 : wait; vTaskDelay(pdMS_TO_TICKS(d)); wait -= d; }
            step++;
        }
        self->motors_.Stop();
        if (song && self->cancel_) {   // dừng nhạc khi bị hủy
            for (int i = 0; i < 20 && sound_running_.load(); i++) { app.GetAudioService().ResetDecoder(); vTaskDelay(pdMS_TO_TICKS(50)); }
            app.GetAudioService().ResetDecoder();
        }
        SetFace("happy", "");
        self->running_ = false;
        vTaskDelete(nullptr);
    }
};

#endif // QBK_FUN_H
