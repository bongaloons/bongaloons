#include <Arduino.h>

int right_val = 0;
int left_val = 0;
int delay_num = 60;
int last_hit_time = millis();

void setup() {
    Serial.begin(9600);
}


void loop() {

    // right side
    right_val = analogRead(A0);
    left_val = analogRead(A1);

    if ((millis() - last_hit_time) > delay_num) {
      last_hit_time = millis();

      if (right_val < 200) {
        Serial.println("0");
      }
      if (left_val < 200) {
        Serial.println("1");
      }
    }
    
    // if (left_val < 200 && (millis() - last_hit_time) > delay_num) {
    //   last_hit_time = millis();
      
    // }

    // end
    // delay(delay_num); // more polling delays
    delay(delay_num); // polling delays
}