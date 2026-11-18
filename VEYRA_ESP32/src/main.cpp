
#include <Arduino.h>
#include <WiFi.h>

void setup() {
    Serial.begin(115200);
    delay(1000);

    WiFi.mode(WIFI_STA);
    WiFi.disconnect();

    Serial.println("\nVEYRA: Wi-Fi scan starting...");

    int networks = WiFi.scanNetworks();

    if (networks == 0) {
        Serial.println("No networks found.");
    } else {
        Serial.printf("Found %d networks:\n", networks);

        for (int i = 0; i < networks; i++) {
            Serial.printf(
                "%d. %s | Signal: %d dBm\n",
                i + 1,
                WiFi.SSID(i).c_str(),
                WiFi.RSSI(i)
            );
        }
    }
}

void loop() {
    delay(1000);
}
