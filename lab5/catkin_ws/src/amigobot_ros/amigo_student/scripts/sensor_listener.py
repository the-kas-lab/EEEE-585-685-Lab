#!/usr/bin/env python3
"""
Task 3 -- subscriber.

Subscribe to the sonar ring and to odometry, and print a readable summary at a
fixed rate (do NOT print inside the callback at full sensor rate -- you will
flood the terminal and slow the node down).

Topics of interest:
    /sonar             sensor_msgs/PointCloud   one echo point per transducer,
                                                plus "index" and "range"
                                                channels
    /sonar/range_0..7  sensor_msgs/Range        the same data, one topic each
    /odom              nav_msgs/Odometry        driver dead reckoning

Unlike the 2025 version of this lab, sonar is available in simulation too, so
you can develop and debug this before you ever touch the hardware.
"""

import rospy
from nav_msgs.msg import Odometry
from sensor_msgs.msg import PointCloud


class SensorListener(object):

    def __init__(self):
        self.ranges = {}
        self.pose = None
        # TODO 1: subscribe to "sonar" (PointCloud) and "odom" (Odometry).

    def sonar_cb(self, msg):
        # TODO 2: pull the "range" and "index" channels out of msg.channels
        #         and store them in self.ranges as {index: range}.
        #         If the channels are missing, fall back on computing the
        #         distance from each point to its transducer's mounting pose.
        pass

    def odom_cb(self, msg):
        # TODO 3: store position and yaw.  Converting a quaternion to yaw:
        #             yaw = atan2(2(wz + xy), 1 - 2(y^2 + z^2))
        pass

    def report(self, _event):
        # TODO 4: print the eight ranges and the current pose on one line.
        pass


def main():
    rospy.init_node("sensor_listener")
    node = SensorListener()
    rospy.Timer(rospy.Duration(0.5), node.report)
    rospy.spin()


if __name__ == "__main__":
    try:
        main()
    except rospy.ROSInterruptException:
        pass
