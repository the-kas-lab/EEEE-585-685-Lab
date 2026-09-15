#include "ros/ros.h"
#include "std_msgs/String.h"
#include <sensor_msgs/JointState.h>
#include <string>
#include <iostream>
#include <sstream>
#include <vector>

using namespace std;

vector<string> joint_names;
vector<double> pan_position_;

void chatterCallback(const sensor_msgs::JointState::ConstPtr& joint_state)
{
  vector<string> joint_names = joint_state->name;
  vector<double> pan_position_ = joint_state->position;
  double* pos = pan_position_.data();
  cout<<pos[0]<<" , "<<pos[1]<<" , "<<pos[2]<<" , "<<pos[3]<<" , "<<pos[4]<<endl;
}


int main(int argc, char **argv)
{
  ros::init(argc, argv, "listener");
  ros::NodeHandle n;
  ros::Subscriber sub = n.subscribe("joint_states", 10, chatterCallback);
  ros::spin();

  return 0;
}
