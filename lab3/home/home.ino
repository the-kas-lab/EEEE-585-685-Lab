#include "SSC32.h"
SSC32 mySSC32;
bool mybool = true;
int channels[] = {0,1,2,3,4,5,16,17,18,19,21,22};
int homeFrame[] = {1515,1500,1550,1500,1450,1500,1500,1500,1500,1500,1500,1500};
void setup() {                
  mySSC32.begin(9600);
  mySSC32.enableServos(channels);
  
 

  pinMode(13,OUTPUT);
  sethome();
}

void loop() {
    sethome();
}

void sethome()
{

  mySSC32.setFrame(homeFrame);
  mySSC32.setFrame(channels,homeFrame);
}
