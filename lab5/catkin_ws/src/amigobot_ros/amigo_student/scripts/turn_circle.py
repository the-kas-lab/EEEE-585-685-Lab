#!/usr/bin/env python3
"""
Task 2 -- publisher.

Drive the AmigoBot in a circle of a commanded radius by publishing
geometry_msgs/Twist on /cmd_vel.

For a differential-drive robot moving on a circle of radius R:

    R = v / w        so    w = v / R

Fill in the TODOs.  The same file must work in Gazebo and on the real robot;
if you find yourself special-casing one of them, something is wrong with your
topic names, not with the robot.
"""

import rospy
from geometry_msgs.msg import Twist


def main():
    rospy.init_node("turn_circle")

    # TODO 1: read ~speed [m/s] and ~radius [m] with rospy.get_param, with
    #         sensible defaults.  Keep speed at or below 0.2 m/s indoors.
    speed = 0.15
    radius = 0.5

    # TODO 2: create a publisher on "cmd_vel" of type Twist.
    pub = None

    # TODO 3: compute the angular velocity that gives the requested radius.
    omega = 0.0

    # ARCOS stops the motors if commands stop arriving, so publish steadily.
    rate = rospy.Rate(20)
    while not rospy.is_shutdown():
        msg = Twist()
        # TODO 4: fill msg.linear.x and msg.angular.z, then publish.
        rate.sleep()

    # TODO 5: publish a zero Twist on shutdown, or the robot keeps going.


if __name__ == "__main__":
    try:
        main()
    except rospy.ROSInterruptException:
        pass
