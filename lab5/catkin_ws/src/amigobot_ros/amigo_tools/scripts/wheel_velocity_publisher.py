#!/usr/bin/env python3
"""
wheel_velocity_publisher.py
===========================
Publishes per-wheel rotational velocities on /wheel_velocities as a
std_msgs/Float32MultiArray with data = [omega_left, omega_right] in rad/s.

This is the topic Lab Task 4 asks you to integrate into an odometry estimate.
It exists so that the *same* student code runs in Gazebo and on the AmigoBot.

Two sources, selected with the ~source parameter:

  source = "joint_states"   (used in simulation)
      Reads sensor_msgs/JointState.  If the publisher fills the .velocity
      field we use it directly; otherwise we numerically differentiate the
      .position field.  In Gazebo the differential-drive plugin publishes the
      wheel joint states, so these are genuine simulated encoder readings.

  source = "twist"          (used on the real AmigoBot)
      The AmigoBot's ARCOS firmware reports the *body* twist (v, w) computed
      from its two wheel encoders, and RosAria republishes that in the twist
      field of nav_msgs/Odometry.  There is no per-wheel topic, so we invert
      the differential-drive kinematics to recover the wheel speeds:

          v_left  = v - w * L / 2          omega_left  = v_left  / r
          v_right = v + w * L / 2          omega_right = v_right / r

      Be honest about this in your report: on hardware the wheel velocities
      are *reconstructed*, not measured independently.  The information still
      originates from the encoders, but any rounding ARCOS applied to (v, w)
      is baked in before you see it.

Parameters
----------
~source                 str    "joint_states" | "twist"      (default joint_states)
~wheel_radius           float  [m]                            (default 0.0508)
~wheel_separation       float  [m]                            (default 0.280)
~left_joint             str                                   (default left_wheel_joint)
~right_joint            str                                   (default right_wheel_joint)
~rate                   float  publish rate [Hz]              (default 20.0)
~publish_joint_states   bool   twist mode only: integrate and
                               publish /joint_states so RViz can
                               animate the wheels                (default False)

Topics
------
subscribe   joint_states  (sensor_msgs/JointState)   source=joint_states
            odom          (nav_msgs/Odometry)        source=twist
publish     wheel_velocities (std_msgs/Float32MultiArray)
            joint_states     (sensor_msgs/JointState)  optional, twist mode
"""

import math

import rospy
from nav_msgs.msg import Odometry
from sensor_msgs.msg import JointState
from std_msgs.msg import Float32MultiArray, MultiArrayDimension


def wrap_to_pi(angle):
    """Map an angle to (-pi, pi]."""
    return math.atan2(math.sin(angle), math.cos(angle))


class WheelVelocityPublisher(object):

    def __init__(self):
        self.source = rospy.get_param("~source", "joint_states")
        self.r = float(rospy.get_param("~wheel_radius", 0.0508))
        self.L = float(rospy.get_param("~wheel_separation", 0.280))
        self.left_joint = rospy.get_param("~left_joint", "left_wheel_joint")
        self.right_joint = rospy.get_param("~right_joint", "right_wheel_joint")
        self.rate_hz = float(rospy.get_param("~rate", 20.0))
        self.publish_js = bool(rospy.get_param("~publish_joint_states", False))

        if self.r <= 0.0 or self.L <= 0.0:
            rospy.logfatal("wheel_radius and wheel_separation must be positive "
                           "(got r=%.4f, L=%.4f)", self.r, self.L)
            raise rospy.ROSInitException("bad geometry parameters")

        # latest estimate, rad/s
        self.omega_left = 0.0
        self.omega_right = 0.0
        self.have_data = False

        # state for numerical differentiation / integration
        self._last_pos = {}          # joint name -> (position, stamp)
        self._int_angle = {self.left_joint: 0.0, self.right_joint: 0.0}
        self._last_int_time = None

        self.pub = rospy.Publisher("wheel_velocities", Float32MultiArray,
                                   queue_size=10)
        self.js_pub = None

        if self.source == "joint_states":
            self.sub = rospy.Subscriber("joint_states", JointState,
                                        self.joint_state_cb, queue_size=10)
            rospy.loginfo("wheel_velocity_publisher: reading /joint_states "
                          "(joints '%s' and '%s')",
                          self.left_joint, self.right_joint)
        elif self.source == "twist":
            self.sub = rospy.Subscriber("odom", Odometry,
                                        self.odom_cb, queue_size=10)
            if self.publish_js:
                self.js_pub = rospy.Publisher("joint_states", JointState,
                                              queue_size=10)
            rospy.loginfo("wheel_velocity_publisher: inverting body twist from "
                          "/odom  (r=%.4f m, L=%.4f m)", self.r, self.L)
        else:
            rospy.logfatal("unknown ~source '%s' (expected 'joint_states' or "
                           "'twist')", self.source)
            raise rospy.ROSInitException("bad ~source parameter")

    # ------------------------------------------------------------------ #
    # callbacks
    # ------------------------------------------------------------------ #
    def joint_state_cb(self, msg):
        for name in (self.left_joint, self.right_joint):
            if name not in msg.name:
                return

        stamp = msg.header.stamp.to_sec()
        if stamp == 0.0:
            stamp = rospy.Time.now().to_sec()

        speeds = {}
        for name in (self.left_joint, self.right_joint):
            i = msg.name.index(name)

            # Preferred: the publisher gave us velocities directly.
            if len(msg.velocity) > i:
                speeds[name] = msg.velocity[i]
                if len(msg.position) > i:
                    self._last_pos[name] = (msg.position[i], stamp)
                continue

            # Fallback: differentiate position.  Wheel joints are continuous,
            # so unwrap the difference before dividing by dt.
            if len(msg.position) <= i:
                return
            pos = msg.position[i]
            prev = self._last_pos.get(name)
            self._last_pos[name] = (pos, stamp)
            if prev is None:
                return
            dt = stamp - prev[1]
            if dt <= 1e-6:
                return
            speeds[name] = wrap_to_pi(pos - prev[0]) / dt

        self.omega_left = speeds[self.left_joint]
        self.omega_right = speeds[self.right_joint]
        self.have_data = True

    def odom_cb(self, msg):
        v = msg.twist.twist.linear.x       # m/s
        w = msg.twist.twist.angular.z      # rad/s
        v_left = v - w * self.L / 2.0
        v_right = v + w * self.L / 2.0
        self.omega_left = v_left / self.r
        self.omega_right = v_right / self.r
        self.have_data = True

    # ------------------------------------------------------------------ #
    def _publish_fake_joint_states(self, now):
        if self.js_pub is None:
            return
        if self._last_int_time is None:
            self._last_int_time = now
            return
        dt = now - self._last_int_time
        self._last_int_time = now
        if dt <= 0.0:
            return

        self._int_angle[self.left_joint] += self.omega_left * dt
        self._int_angle[self.right_joint] += self.omega_right * dt

        js = JointState()
        js.header.stamp = rospy.Time.from_sec(now)
        js.name = [self.left_joint, self.right_joint]
        js.position = [self._int_angle[self.left_joint],
                       self._int_angle[self.right_joint]]
        js.velocity = [self.omega_left, self.omega_right]
        self.js_pub.publish(js)

    def spin(self):
        rate = rospy.Rate(self.rate_hz)
        start = rospy.Time.now()
        while not rospy.is_shutdown():
            if self.have_data:
                msg = Float32MultiArray()
                dim = MultiArrayDimension()
                dim.label = "wheel"      # index 0 = left, index 1 = right
                dim.size = 2
                dim.stride = 2
                msg.layout.dim = [dim]
                msg.layout.data_offset = 0
                msg.data = [float(self.omega_left), float(self.omega_right)]
                self.pub.publish(msg)
                self._publish_fake_joint_states(rospy.Time.now().to_sec())
            elif (rospy.Time.now() - start).to_sec() > 5.0:
                rospy.logwarn_throttle(
                    10.0,
                    "wheel_velocity_publisher: no input yet on '%s'. "
                    "Is the simulator or RosAria running?"
                    % ("joint_states" if self.source == "joint_states"
                       else "odom"))
            rate.sleep()


def main():
    rospy.init_node("wheel_velocity_publisher")
    try:
        node = WheelVelocityPublisher()
    except rospy.ROSInitException:
        return
    node.spin()


if __name__ == "__main__":
    try:
        main()
    except rospy.ROSInterruptException:
        pass
