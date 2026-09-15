#include <ros/ros.h>
#include <sensor_msgs/JointState.h>
#include "lynxmotion_ssc32/ssc32.h"
#include "math.h"
#include <algorithm>
#include <string>
#include <iostream>
#include <sstream>
#include <vector>

using namespace std;
using namespace lynxmotion_ssc32;

SSC32 ssc32_dev;
Joint *channels[32];
std::string port;
int baud;
std::map<std::string, Joint*> joints_map;

void relaxJoints( )
{
	ROS_INFO( "Relaxing joints" );
	if( ssc32_dev.is_connected( ) )
	{
		for( unsigned int i = 0; i < 32; i++ )
		{
			if( channels[i] != NULL )
				ssc32_dev.discrete_output( i, SSC32::Low );
		}
	}
}

void chatterCallback(const sensor_msgs::JointState::ConstPtr& joint_state)
{
	vector<string> joint_names = joint_state->name;
	vector<double> joint_position = joint_state->position;

	int jnt_size = joint_names.size();

	double* pos = joint_position.data();

	SSC32::ServoCommand *cmd;
	cmd = new SSC32::ServoCommand[jnt_size];
	for( unsigned int j = 0; j < jnt_size ; j++ )
	{
		Joint *joint = joints_map[joint_names[j]];
		if( joint->properties.initialize )
		{
			cmd[j].ch = joint->properties.channel;
			cmd[j].pw = ( unsigned int )( (2000.0*(joint->properties.offset_angle + pos[j])/3.14) + 1500);
			
			if( joint->properties.invert )
				cmd[j].pw = ( unsigned int )( (2000.0*(joint->properties.offset_angle - pos[j])/3.14) + 1500);

			unsigned int j_min = ( unsigned int )( (2000.0*(joint->properties.min_angle)/3.14) + 1500);
			unsigned int j_max = ( unsigned int )( (2000.0*(joint->properties.min_angle)/3.14) + 1500);

			if( cmd[j].pw < j_min)
				cmd[j].pw = j_min;
			else if( cmd[j].pw > ((2000.0*(joint->properties.max_angle)/3.14) + 1500))
				cmd[j].pw = ( unsigned int )( (2000.0*(joint->properties.max_angle)/3.14) + 1500);
		}
	}

	// Send command
	ssc32_dev.move_servo( cmd, jnt_size );
	delete [] cmd;
}


int main( int argc, char** argv )
{
	ros::init( argc, argv, "joint_controller" );
	ros::NodeHandle nh;

	nh.param<std::string>( "port", port, "/dev/ttyUSB0" );
	nh.param<int>( "baud", baud, 115200 );

	XmlRpc::XmlRpcValue joints_list;
	if( nh.getParam( "joints", joints_list ) )
	{
		ROS_ASSERT( joints_list.getType( ) == XmlRpc::XmlRpcValue::TypeStruct );

		XmlRpcValueAccess joints_struct_access( joints_list );
		XmlRpc::XmlRpcValue::ValueStruct joints_struct = joints_struct_access.getValueStruct( );

		XmlRpc::XmlRpcValue::ValueStruct::iterator joints_it;

		for( joints_it = joints_struct.begin( ); joints_it != joints_struct.end( ); joints_it++ )
		{
			Joint *joint = new Joint;
			joint->name = static_cast<std::string>( joints_it->first );

			std::string joint_graph_name = "joints/" + joint->name + "/";

			nh.param<int>( joint_graph_name + "channel", joint->properties.channel, 0 );

			// Channel must be between 0 and 31, inclusive
			ROS_ASSERT( joint->properties.channel >= 0 );
			ROS_ASSERT( joint->properties.channel <= 31 );

			nh.param<double>( joint_graph_name + "max_angle", joint->properties.max_angle, M_PI_2 );
			nh.param<double>( joint_graph_name + "min_angle", joint->properties.min_angle, -M_PI_2 );
			nh.param<double>( joint_graph_name + "offset_angle", joint->properties.offset_angle, 0 );
			nh.param<bool>( joint_graph_name + "initialize", joint->properties.initialize, true );
			nh.param<bool>( joint_graph_name + "invert", joint->properties.invert, false );

			// Make sure no two joints have the same channel
			ROS_ASSERT( channels[joint->properties.channel] == NULL );

			// Make sure no two joints have the same name
			ROS_ASSERT( joints_map.find( joint->name ) == joints_map.end( ) );

			channels[joint->properties.channel] = joint;
			joints_map[joint->name] = joint;
		}
	}
	else
	{
		ROS_FATAL( "No joints were given" );
		ROS_BREAK( );
	}


	if(!ssc32_dev.open_port( port.c_str( ), baud ))
	{	
		ROS_ERROR("Unable to open port custom");
		return 0;
  	}
	ros::Subscriber sub = nh.subscribe("joint_states", 10, chatterCallback);
	ros::spin();

	relaxJoints();

	return 0;
}
