#!/usr/bin/env python3
"""
Task 4 -- dead reckoning.

Subscribe to /wheel_velocities (std_msgs/Float32MultiArray, data =
[omega_left, omega_right] in rad/s) and publish your own nav_msgs/Odometry on
/my_odom, with frame_id "odom" and child_frame_id "base_link".

Discrete-time differential-drive kinematics, integrated once per message:

    v_L = omega_L * r                  v_R = omega_R * r          [m/s]
    d_L = v_L * dt                     d_R = v_R * dt             [m]

    d_center = (d_R + d_L) / 2                                    [m]
    dphi     = (d_R - d_L) / L                                    [rad]

    theta_k+1 = theta_k + dphi
    x_k+1     = x_k + d_center * cos(theta_k + dphi/2)
    y_k+1     = y_k + d_center * sin(theta_k + dphi/2)

    twist:  v = d_center / dt,   w = dphi / dt

Two notes the old lab manual got wrong, so read them carefully:

  * The heading used to project d_center should be the MIDPOINT heading
    theta_k + dphi/2, not theta_k.  Using theta_k is a first-order rectangular
    rule; the midpoint version is second order and visibly better on curves.
    You may implement either -- but say which one you used, and if you have
    time, plot both against ground truth.  That comparison is worth more in
    the report than any amount of prose.

  * dt must come from the message timestamps or from rospy.Time.now(), NOT
    from a hardcoded 1/rate.  Your callback is not called on a metronome.

Get the quaternion for a planar yaw from
    q = (0, 0, sin(theta/2), cos(theta/2))
or use tf.transformations.quaternion_from_euler(0, 0, theta).

Do NOT broadcast a TF transform from this node: odom -> base_link is already
owned by the driver, and a second publisher will make RViz jitter.
"""

import math

import rospy
from nav_msgs.msg import Odometry
from std_msgs.msg import Float32MultiArray


class MyOdom(object):

    def __init__(self):
        # TODO 1: read ~wheel_radius and ~wheel_separation from the parameter
        #         server (my_odom.launch loads amigo_params.yaml for you).
        self.r = 0.0508
        self.L = 0.280

        # TODO 2: initialise x, y, theta to zero and remember the last stamp.

        # TODO 3: publisher on "my_odom", subscriber on "wheel_velocities".

    def wheel_cb(self, msg):
        # TODO 4: unpack msg.data -> omega_left, omega_right.
        # TODO 5: compute dt, integrate the pose, publish an Odometry message.
        pass


def main():
    rospy.init_node("my_odom")
    MyOdom()
    rospy.spin()


if __name__ == "__main__":
    try:
        main()
    except rospy.ROSInterruptException:
        pass
