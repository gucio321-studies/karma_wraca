#include "HX711.h"
#include <Wire.h> 
#include <LiquidCrystal.h>
#include <Stepper.h>

// HX711 circuit wiring
const int LOADCELL_DOUT_PIN = A0;
const int LOADCELL_SCK_PIN = 6;
// lcd wiring
const int rs = 12, en = 13, d4 = 2, d5 = 3, d6 = 4, d7 = 5;
// rotary encoder wiring
const int rsw = 7;
const int rdt = A1;
const int rclk = A2;


// libraries
HX711 scale;
Stepper stepper(256, 8, 10, 9, 11);
LiquidCrystal lcd(rs, en, d4, d5, d6, d7);

//variables
int counter = 0; 
int currentStateCLK;
int previousStateCLK; 
bool state2 = 1;
bool hourstime = 1;
bool minutestime = 1;
bool secondstime = 1;
bool twodigittime = 1;
bool onedigittime = 1;
bool switchvalue;
bool oldswitchvalue;
int hours = 0;
int minutes = 0;
int seconds = 0;
int amountg = 0;
int amountt = 0;
int hours1 = 25;
int hours2 = 25;
int hours3 = 25;
int hours4 = 25;
int hours5 = 25;
int minutes1 = 61;
int minutes2 = 61;
int minutes3 = 61;
int minutes4 = 61;
int minutes5 = 61;
int seconds1 = 61;
int seconds2 = 61;
int seconds3 = 61;
int seconds4 = 61;
int seconds5 = 61;
int hoursg;
int minutesg;
int secondsg;
int neededvalue;


void setup() 
{
  lcd.begin(20,4);
  scale.begin(LOADCELL_DOUT_PIN, LOADCELL_SCK_PIN);
  stepper.setSpeed(60);
  pinMode(rdt, INPUT);
  pinMode(rsw, INPUT_PULLUP);
  pinMode(rclk, INPUT);
  
    lcd.clear();
    lcd.print("Wybierz dzienna");
    lcd.setCursor(0,1);
    lcd.print("liczbe porcji: 1");
    previousStateCLK = digitalRead(rclk);
    delay(500);

    while(state2)
    {    
      switchvalue = digitalRead(rsw);
      currentStateCLK = digitalRead(rclk);
      if (currentStateCLK != previousStateCLK)
      {
        if (digitalRead(rdt) != currentStateCLK) 
        {    
           counter++;
        } 
        else 
        { 
         counter--;
        }
        if (counter < 0)
        {
              counter = -counter;
        }
        amountt = (counter%5) +1 ;
        lcd.clear();
        lcd.print("Wybierz dzienna");
        lcd.setCursor(0,1);
        lcd.print("liczbe porcji: ");
        lcd.print(amountt);
 
    
      }
        state2 = button(state2, 1); 
        previousStateCLK = currentStateCLK;
   } 
   counter=0;
   lcd.clear();
        lcd.print("Wybierz ilosc karmy,");
        lcd.setCursor(0,1);
        lcd.print("dawanej na jedna");
        lcd.setCursor(0,2);
        lcd.print("porcje: 0g");
        delay(500);
     

   while(twodigittime==true)
   {
    switchvalue = digitalRead(rsw);
    currentStateCLK = digitalRead(rclk);
      if (currentStateCLK != previousStateCLK)
      {
        if (digitalRead(rdt) != currentStateCLK) 
        {    
          counter = counter+10;
        } 
        else 
        { 
         counter = counter-10;
        } 
        amountg = counter;
        lcd.clear();
        lcd.print("Wybierz ilosc karmy,");
        lcd.setCursor(0,1);
        lcd.print("dawanej na jedna");
        lcd.setCursor(0,2);
        lcd.print("porcje: ");
        lcd.print(amountg);
        lcd.print("g");
      }
       twodigittime = button(twodigittime, 0);
       previousStateCLK = currentStateCLK;
   }
   delay(500);
   
    while(onedigittime==1)
   {
    switchvalue = digitalRead(rsw);
    currentStateCLK = digitalRead(rclk);
      if (currentStateCLK != previousStateCLK)
      {
        if (digitalRead(rdt) != currentStateCLK) 
        {    
           counter++;
        } 
        else 
        { 
         counter--;
        } 
        amountg = counter;
        lcd.clear();
        lcd.print("Wybierz ilosc karmy");
        lcd.setCursor(0,1);
        lcd.print("dawanej na jedna");
        lcd.setCursor(0,2);
        lcd.print("porcje: ");
        lcd.print(amountg);
        lcd.print("g");
      }
      onedigittime = button(onedigittime, 1);
       previousStateCLK = currentStateCLK;
   }
   hours1 = askingbouttime(1, 24, 1, 1, "Wybierz godzine", "podawania karmy");
   minutes1 = askingbouttime(1, 60, 1, 2, "Wybierz godzine", "podawania karmy"); 
   seconds1 = askingbouttime(1, 60, 1, 3, "Wybierz godzine", "podawania karmy");   
   lcd.clear();
   switch(amountt)
   {
    case 2:
   {
    hours2 = askingbouttime(1, 24, 1, 1, "Wybierz godzine", "podawania karmy");
    minutes2 = askingbouttime(1, 60, 1, 2, "Wybierz godzine", "podawania karmy"); 
    seconds2 = askingbouttime(1, 60, 1, 3, "Wybierz godzine", "podawania karmy");   
    break;
   }
    case 3:
   {
    hours2 = askingbouttime(1, 24, 1, 1, "Wybierz godzine", "podawania karmy");
    minutes2 = askingbouttime(1, 60, 1, 2, "Wybierz godzine", "podawania karmy"); 
    seconds2 = askingbouttime(1, 60, 1, 3, "Wybierz godzine", "podawania karmy"); 
    lcd.clear();  
    hours3 = askingbouttime(1, 24, 1, 1, "Wybierz godzine", "podawania karmy");
    minutes3 = askingbouttime(1, 60, 1, 2, "Wybierz godzine", "podawania karmy"); 
    seconds3 = askingbouttime(1, 60, 1, 3, "Wybierz godzine", "podawania karmy");   
    break;
   }
    case 4:
   {
    hours2 = askingbouttime(1, 24, 1, 1, "Wybierz godzine", "podawania karmy");
    minutes2 = askingbouttime(1, 60, 1, 2, "Wybierz godzine", "podawania karmy"); 
    seconds2 = askingbouttime(1, 60, 1, 3, "Wybierz godzine", "podawania karmy");   
    lcd.clear();
     hours3 = askingbouttime(1, 24, 1, 1, "Wybierz godzine", "podawania karmy");
    minutes3 = askingbouttime(1, 60, 1, 2, "Wybierz godzine", "podawania karmy"); 
    seconds3 = askingbouttime(1, 60, 1, 3, "Wybierz godzine", "podawania karmy");   
    lcd.clear();
    hours4 = askingbouttime(1, 24, 1, 1, "Wybierz godzine", "podawania karmy");
    minutes4 = askingbouttime(1, 60, 1, 2, "Wybierz godzine", "podawania karmy"); 
    seconds4 = askingbouttime(1, 60, 1, 3, "Wybierz godzine", "podawania karmy");   
    break;
   }
    case 5:
   {
    hours2 = askingbouttime(1, 24, 1, 1, "Wybierz godzine", "podawania karmy");
    minutes2 = askingbouttime(1, 60, 1, 2, "Wybierz godzine", "podawania karmy"); 
    seconds2 = askingbouttime(1, 60, 1, 3, "Wybierz godzine", "podawania karmy");   
    lcd.clear();
     hours3 = askingbouttime(1, 24, 1, 1, "Wybierz godzine", "podawania karmy");
    minutes3 = askingbouttime(1, 60, 1, 2, "Wybierz godzine", "podawania karmy"); 
    seconds3 = askingbouttime(1, 60, 1, 3, "Wybierz godzine", "podawania karmy");  
    lcd.clear(); 
    hours4 = askingbouttime(1, 24, 1, 1, "Wybierz godzine", "podawania karmy");
    minutes4 = askingbouttime(1, 60, 1, 2, "Wybierz godzine", "podawania karmy"); 
    seconds4 = askingbouttime(1, 60, 1, 3, "Wybierz godzine", "podawania karmy");   
    lcd.clear();
    hours5 = askingbouttime(1, 24, 1, 1, "Wybierz godzine", "podawania karmy");
    minutes5 = askingbouttime(1, 60, 1, 2, "Wybierz godzine", "podawania karmy"); 
    seconds5 = askingbouttime(1, 60, 1, 3, "Wybierz godzine", "podawania karmy");   
    break;
   }
}

hours = askingbouttime(1, 24, 1, 1, "Jaka mamy godzine?", "");
minutes = askingbouttime(1, 60, 1, 2, "Jaka mamy godzine?", ""); 
seconds = askingbouttime(1, 60, 1, 3, "Jaka mamy godzine?", ""); 
lcd.clear();
}


unsigned long previousMillis = 0;
const long interval = 1000;




void loop() 
{
  unsigned long currentMillis = millis();   
  
  if (currentMillis - previousMillis >= interval) 
      {
          // Zapamiętanie obecnego czasu dla następnego porównania
          previousMillis = currentMillis; 

          // **Zliczanie sekund, minut, godzin**
          seconds++;
          if (seconds >= 60)
          {
            minutes++;
            seconds -= 60;
            if (minutes >= 60)
            {
              hours++ ;
              minutes -= 60;
              if(hours >= 24)
              {
                hours -= 24;
              }
            }
          }

  
  
  
    if((hours == hours1 && minutes == minutes1 && seconds == seconds1) || 
        (hours == hours2 && minutes == minutes2 && seconds == seconds2) ||
        (hours == hours3 && minutes == minutes3 && seconds == seconds3) ||
        (hours == hours4 && minutes == minutes4 && seconds == seconds4) ||
        (hours == hours5 && minutes == minutes5 && seconds == seconds5))
    {
    
      if(scale.read() < 0)
      {
        lcd.clear();
      }
      else
      {
       lcd.clear();
       lcd.print("czekanie na"); 
      }     
    }
  }


int askingbouttime(bool stateh, int reszta,
                   int changevalue, int whosetimeisit,
                  String question1, String question2)
{
  delay(300);
  switch(whosetimeisit)
  {
    case 1:
    {
      hoursg=0;
      minutesg=0;
      secondsg=0;
    }
  }
   lcd.clear();
   lcd.print(question1);
   if(question2 != "")
   {
   lcd.setCursor(0,1);
   lcd.print(question2);
   lcd.setCursor(0,3);
   }
   else
   {
    lcd.setCursor(0,2);
   }
          if(hoursg < 10)
          {
          lcd.print("0");
          }
          lcd.print(hoursg);
          lcd.print(":");
          if(minutesg < 10)
          {
          lcd.print("0");
          }
          lcd.print(minutesg);
          lcd.print(":");
          if(secondsg < 10)
          {
          lcd.print("0");
          }
          lcd.print(secondsg);
   while(stateh == true)
   {
    bool switchvalue = digitalRead(rsw);
    int currentStateCLK = digitalRead(rclk);
      if (currentStateCLK != previousStateCLK)
      {
        if (digitalRead(rdt) != currentStateCLK) 
        {    
           counter = counter+changevalue;
        } 
        else 
        { 
         counter = counter-changevalue;
        } 
        if(counter <0)
        {
           neededvalue = -counter%reszta; 
        }
        else
        {
           neededvalue = counter%reszta;
        }
         lcd.clear();
         lcd.print(question1);
         if(question2 != "")
         {
         lcd.setCursor(0,1);
         lcd.print(question2);
         lcd.setCursor(0,3);
         }
         else
         {
           lcd.setCursor(0,2);
         }
          switch(whosetimeisit)
          {
            case 1:
            {
               hoursg = neededvalue;  
               break;   
            }
            case 2:
            {
              minutesg = neededvalue;
              break;
            }
             case 3:
            {
              secondsg = neededvalue;
              break;
            }
          }
          
           if(hoursg < 10)
          {
          lcd.print("0");
          }
          lcd.print(hoursg);
          lcd.print(":");
          if(minutesg < 10)
          {
          lcd.print("0");
          }
          lcd.print(minutesg);
          lcd.print(":");
          if(secondsg < 10)
          {
          lcd.print("0");
          }
          lcd.print(secondsg);
   }
   if(switchvalue == LOW && oldswitchvalue== HIGH) 
      {
          delay(20);
          if(switchvalue == LOW && oldswitchvalue== HIGH) 
          {
             stateh = false;
             counter = 0;
          }
      }   
    previousStateCLK = currentStateCLK;
    oldswitchvalue = switchvalue;

 
   }
   return(neededvalue);
}
int button(bool state, bool resett)
{
   if(switchvalue == LOW && oldswitchvalue == HIGH) 
      {
          delay(20);
          if(switchvalue == LOW && oldswitchvalue == HIGH) 
          {
             state = false;
             if (resett)
             {
             counter = 0;
             }
             return(state);
          }
      }
      oldswitchvalue = switchvalue;
}
