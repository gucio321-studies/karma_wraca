#include <Servo.h>

Servo myservo;  // create servo object to control a servo

int potpin = 0;  // analog pin used to connect the potentiometer
int val;    // variable to read the value from the analog pin

void setup() {
  myservo.attach(9);  // attaches the servo on pin 9 to the servo object
}

void loop() {
  // Move servo from 0 to 180 degrees
  for (int i = 0; i < 180; i++) {     // scale it to use it with the servo (value between 0 and 180)
    myservo.write(i);                  // sets the servo position according to the scaled value
    delay(15);                           // waits for the servo to get there
  }
  
  // Move servo from 180 back to 0 degrees
  for (int i = 0; i < 180; i++) {
    val = 180 - i;     // scale it to use it with the servo (value between 0 and 180)
    myservo.write(val);                  // sets the servo position according to the scaled value
    delay(15);                           // waits for the servo to get there
  }
}