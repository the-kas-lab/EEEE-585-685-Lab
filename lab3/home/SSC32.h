/*
* File:     SSC32.h
* Author:   Matt Haywood
* Date:     8/12/15
*
* Description: 
* Lynxmotion Serial Servo Controller 32 Library for the Arduino
* - Frames are used to organize all of the positions of the servos
* - Sends the position and time commands through Serial
* - Servos can be disabled and enabled easily
*
*/


#ifndef SSC32_h
#define SSC32_h
#define ARRAY_SIZE(x) (sizeof(x) / sizeof((x)[0]))
#include "Arduino.h"
#include "Vector.h"



const int numberOfPorts = 32;

class SSC32 {

public:

	SSC32();
	void begin(int baud);
	
	void servoMode(int servoNum, bool on);
	void enableServos(int servoNum[]);
	void disableServos(int servoNum[]);
	
	bool getServoMode(int servoNum);
	
	bool moveServo(int channel,int pos);
	void setFrame(int channel[],int theFrame[]);
	void setFrame(int theFrame[]);
	void setFrame(int theFrame[], int moveTime);
	void setOffset(int channel, int offset);
	void setOffset(int channel[], int offset[]);
	
	void descreteOut(int channel,bool level);
	void descreteOut(int channel[],bool level[]);
	void byteOut(int bank, int value);
	bool moveStatus();
	int getServoPos(int channel);
	Vector<int> getServoPos(int channel[]);
//	Vector<bool> digitalRead(char port[]);
	int analogRead(char port[]);
	String getVersion();
	
	
private:
	void initServoModes();
	bool SSCPORT[numberOfPorts];

};

#endif
