/*
* File:     SSC32.cpp
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


#include "SSC32.h"

// constructor
SSC32::SSC32() {
	initServoModes();
}
// start serial port
void SSC32::begin(int baud) {
	Serial.begin(baud);
}

// Initialize all the servos
void SSC32::initServoModes() {
	for(int i=0; i<numberOfPorts; i++) {
		SSCPORT[i] = false;
	}
}

// Set the servo mode to on or off
void SSC32::servoMode(int servoNum, bool on) {
	SSCPORT[servoNum] = on;
}

// Set the servo mode on for a group of servos
void SSC32::enableServos(int servoNum[]) {
	for(int i = 0; i <numberOfPorts;i++) {
		servoMode(servoNum[i],true);
	}
}
// Set the servo mode off for a group of servos
void SSC32::disableServos(int servoNum[]) {
	for(int i = 0; i <numberOfPorts;i++) {
		servoMode(servoNum[i],false);
	}
}
// See if the servo is enabled or not
bool SSC32::getServoMode(int servoNum) {
	return SSCPORT[servoNum];
}

// Move the servos according to the frame
// Movement is completed by the time specified in moveTime
void SSC32::setFrame(int theFrame[], int moveTime) {
	
	int frameIndex = 0;
	String dataToSend;
	// Look through all the ports
	for(int i=0; i<numberOfPorts; i++) {
		// If the port is enabled
		if(getServoMode(i) == true) {
			dataToSend += '#' + String(i) + 'P' + String(theFrame[frameIndex]);
			frameIndex++; 
		}
	}
	// Print out the time and send it
	dataToSend.concat('T');
	dataToSend.concat(moveTime);
	Serial.println(dataToSend);
}

// Move the servos according to the frame
void SSC32::setFrame(int theFrame[]) {
	int frameIndex = 0;
	String dataToSend;
	// Look through all the ports
	for(int i=0; i<numberOfPorts; i++) {
		
		// If the port is enabled
		if(getServoMode(i) == true) {
			dataToSend += '#' + String(i) + 'P' + String(theFrame[frameIndex]);
			frameIndex++;
		}
	}
	Serial.println(dataToSend);
}

// Move the servos according to the frame
void SSC32::setFrame(int channel[],int theFrame[]) {
	int frameIndex = (sizeof(channel)/sizeof(int)) - 1;
	String dataToSend;
	// Look through all the ports
	
	for(int i=0; i < frameIndex; i++) {
		
		dataToSend += '#' + String(channel[i]) + 'P' + String(theFrame[i]);
	}
	Serial.println(dataToSend);
}
// Move a specific servo
bool SSC32::moveServo(int channel,int pos){
	if(getServoMode(channel) == false) return false;
	String dataToSend = '#' + String(channel) + 'P' + String(pos);
	Serial.println(dataToSend);
	return true;
}
// set center position offset can only change between 100 to -100 us
void SSC32::setOffset(int channel, int offset){
	String dataToSend = '#' + String(channel) + 'PO' + String(offset);
	Serial.println(dataToSend);
}
// set center position offset can only change between 100 to -100 us
void SSC32::setOffset(int channel[], int offset[]){
	String dataToSend = "";
	for(int i = 0; i < sizeof(channel)-1;i++){
	dataToSend += '#' + String(channel[i]) + 'P' + String(offset[i]);
	}
	Serial.println(dataToSend);
}

void SSC32::descreteOut(int channel,bool level){
	
	String dataToSend = '#' + String(channel) + String((level)?'H':'L');
	Serial.println(dataToSend);
}

void SSC32::descreteOut(int channel[],bool level[]){
	
	String dataToSend;
	for(int i =0; i<sizeof(channel)-1;i++){
		dataToSend ='#' + String(channel[i]) + String((level[i])?'H':'L');
	}
	Serial.println(dataToSend);
}

void SSC32::byteOut(int bank, int value){
	String dataToSend = '#' + String(bank) +':'+ String(value);
	Serial.println(dataToSend);
}
// see if the previous move is complete
// true = still in progress
bool SSC32::moveStatus(){
	Serial.println('Q');
	Serial.flush();
	while(!(Serial.available()>0)){}
	char byteIn = Serial.read();
	while(byteIn != '+' || byteIn != '.')
	{
		
		if(byteIn == '+')
		{			
			return true;
		}
		if(byteIn == '.') 
		{
			return false;
		}
		byteIn = Serial.read();
	}
}

int SSC32::getServoPos(int channel)
{
	Serial.println(String('QP') + String(channel));
	Serial.flush();
	while(!(Serial.available()>0)){}
	return (Serial.read()*10);
}

Vector<int> SSC32::getServoPos(int channel[])
{
	Vector<int> pulseWidth;
	for(int i = 0;i<sizeof(channel);i++)
	{
		pulseWidth.push_back(getServoPos(channel[i]));
	}
	return pulseWidth;
}
/*Vector<bool> digitalRead(char port[])
{
	Serial.println(port);
	Serial.flush();
	while(!(Serial.available()>0)){}
}*/
int analogRead(char port[])
{
	//code
}
String getVersion()
{
	Serial.println("VER");
	Serial.flush();
	while(!(Serial.available()>0)){}
	String versionNumber;
	while((Serial.available()>0))
	{
		versionNumber += String(Serial.read());
	}
	return versionNumber;
}
