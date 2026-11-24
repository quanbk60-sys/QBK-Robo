idf_component_register(SRCS "main.c" INCLUDE_DIRS "."
    REQUIRES esp_lcd esp_driver_i2c esp_driver_i2s esp_driver_ledc esp_driver_rmt esp_driver_gpio esp_adc esp_timer esp_driver_spi)
