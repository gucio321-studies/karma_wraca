// Serial commands list:
// Input commands (received by Arduino)::
// - PING - respond with PING
// - EXTRUDE - extrude karma (move servo) (and report DONE)
// Output commands (returned by Arudino):
// - PING - response to PING command
// - DONE - reported when actions (EXTRUDE fro now) is complete

#include <Servo.h>
#include <Ds1302.h>

const auto SERVO_PWM = 9;
const auto TickDelay = 200; // ms
const int MAX_CMD_SIZE = 10;
const int CLOCK_CLK = 5;
const int CLOCK_DAT = 6;
const int CLOCK_RESET = 7;

Servo feeder;
Ds1302 clock(CLOCK_CLK, CLOCK_DAT, CLOCK_RESET);
char command[MAX_CMD_SIZE]; // max of 10 chars

void setup() {
  pinMode(SERVO_PWM, OUTPUT);
  feeder.attach(SERVO_PWM);
  feeder.write(180);
  Serial.begin(9600);
  clock.begin();
  Serial.println("// Karma wraca - Hello!");
}

void loop() {
  //Serial.println("// loop ");
  // read things from the serial
  for (int n = 0; Serial.available() > 0; n++) {
    Serial.println("// loop");
    if (n >= MAX_CMD_SIZE) {
      Serial.println("//ERROR: command too long! Trapping");
      while (1);
    }

    char c = Serial.read();
    if (c == '\n' || c == '\r') {
      execCommand(command);
      for (int i = 0; i < MAX_CMD_SIZE; i++) {
        command[i] = 0;
      }
      break; // need to reset the loop to reset n
    }

    command[n] = c;
  }

  delay(TickDelay);
}

void extrudeKarma() {
  Serial.println("//start move");
  // Move servo from 0 to 180 degrees
  for (int i = 180; i > 0; i--) {     // scale it to use it with the servo (value between 0 and 180)
    feeder.write(i);                  // sets the servo position according to the scaled value
    delay(15);                           // waits for the servo to get there
  }
  
  // Move servo from 180 back to 0 degrees
  for (int i = 180; i > 0; i--) {
    feeder.write(180-i);                  // sets the servo position according to the scaled value
    delay(15);                           // waits for the servo to get there
  }
  Serial.println("//move done");
}

void execCommand(const char* cmd) {
  if (strcmp(cmd, "EXTRUDE") == 0) {
      extrudeKarma();
      Serial.println("DONE");
  } else if (strcmp(cmd, "TIME") == 0) {
      Serial.println("// - reporting time");
      Serial.println(getDS1302UnixTime());
  } else if (strcmp(cmd, "PING") == 0) {
    Serial.println("PING");
  } else {
    Serial.println("//ERROR: unknown command!");
    Serial.println(cmd);
    //while (1);
  }
}

unsigned long getDS1302UnixTime() {
  // Read time and date
  int h = clock.getHour();
  int m = clock.getMinute();
  int s = clock.getSecond();
  int d = clock.getDate();
  int mo = clock.getMonth();
  int y = clock.getYear(); // full year, e.g., 2025

  // Helper lambdas
  auto isLeap = [](int year) {
    return (year % 4 == 0 && (year % 100 != 0 || year % 400 == 0));
  };

  auto daysInMonth = [&](int month, int year) {
    const int days[] = {31,28,31,30,31,30,31,31,30,31,30,31};
    return (month == 2 && isLeap(year)) ? 29 : days[month-1];
  };

  // Count days since 1970
  unsigned long days = 0;
  for(int year=1970; year<y; year++) days += isLeap(year) ? 366 : 365;
  for(int month=1; month<mo; month++) days += daysInMonth(month, y);
  days += d - 1;

  // Convert to seconds
  return days * 86400UL + h*3600UL + m*60UL + s;
}
