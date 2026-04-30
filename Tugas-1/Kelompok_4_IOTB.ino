#include <Wire.h>
#include <Adafruit_GFX.h>
#include <Adafruit_SSD1306.h>
#define SCREEN_WIDTH 128
#define SCREEN_HEIGHT 64
// Declaration for an SSD1306 display connected to I2C (SDA, SCL pins)
// The parameter -1 means the display doesn't have a reset pin
Adafruit_SSD1306 display(SCREEN_WIDTH, SCREEN_HEIGHT, &Wire, -1);
int x;

void setup() {
  display.begin(SSD1306_SWITCHCAPVCC, 0x3C);
  display.clearDisplay();
  display.setTextSize(2);
  display.setTextColor(WHITE);
}

void loop() {

  for (x = 128; x > -150; x--) {  // 128 = lebar OLED
    display.clearDisplay();
    display.setCursor(x, 20);
    display.print("i love youu <3");
    display.display();
    delay(20);
  }

}