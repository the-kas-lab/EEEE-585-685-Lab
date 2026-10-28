#!/usr/bin/env python3
"""
Extra credit -- reactive wandering with obstacle avoidance.

Drive forward until a sonar reports an obstacle inside a threshold, then turn
away and continue.  Keep it simple and reactive; no map, no planner.

Things that will bite you, in the order they usually bite:

  * Sonar is specular.  A wall at a shallow angle reflects the pulse away and
    reads as "clear" all the way to max range.  Do not trust a single ping.
  * Crosstalk between transducers produces isolated short readings.  Filter,
    for example by requiring two consecutive frames to agree.
  * The AmigoBot cannot see below its own body.  A table leg base or a cable
    is invisible.  Stay near the robot while it runs.
  * The rear pair (6, 7) matters when you back up.
"""

import rospy
from geometry_msgs.msg import Twist
from sensor_msgs.msg import PointCloud


def main():
    rospy.init_node("wander")
    # TODO 1: read ~speed [m/s] and ~stop_distance [m] with rospy.get_param,
    #         with sensible defaults (0.15 and 0.45 are a good start).
    # TODO 2: everything else.
    rospy.spin()


if __name__ == "__main__":
    try:
        main()
    except rospy.ROSInterruptException:
        pass
