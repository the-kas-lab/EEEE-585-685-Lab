#!/usr/bin/env python3
"""
drive_pattern.py
================
Open-loop motion generator used for two things:

  1. A quick smoke test that /cmd_vel actually reaches the robot
     (pattern:=circle -- this is also the check-off in Lab Task 2).
  2. Repeatable dead-reckoning experiments (pattern:=square, pattern:=spin).

Everything is timed, not closed-loop.  That is deliberate: an open-loop command
sequence gives you a known *commanded* trajectory to compare the *estimated*
and *actual* trajectories against.

Patterns
--------
circle   constant (v, w) forever, radius = v / w
square   N laps of: drive `side` metres, turn 90 degrees left
spin     `turns` full rotations in place.  Use this to calibrate the
         wheel separation L: if the robot over-rotates, your L is too small.
stop     publish a single zero Twist and exit

Parameters
----------
~pattern       str    circle | square | spin | stop     (default circle)
~speed         float  linear speed [m/s]                (default 0.15)
~turn_speed    float  angular speed [rad/s]             (default 0.6)
~side          float  square side [m]                   (default 1.0)
~laps          int    square laps                       (default 1)
~turns         float  spin revolutions                  (default 10)
~radius        float  circle radius [m]                 (default 0.5)
~settle        float  pause between segments [s]        (default 0.7)

Topics
------
publish   cmd_vel  (geometry_msgs/Twist)
"""

import math
import time

import rospy
from geometry_msgs.msg import Twist


class DrivePattern(object):

    def __init__(self):
        self.pattern = rospy.get_param("~pattern", "circle")
        self.speed = float(rospy.get_param("~speed", 0.15))
        self.turn_speed = float(rospy.get_param("~turn_speed", 0.6))
        self.side = float(rospy.get_param("~side", 1.0))
        self.laps = int(rospy.get_param("~laps", 1))
        self.turns = float(rospy.get_param("~turns", 10))
        self.radius = float(rospy.get_param("~radius", 0.5))
        self.settle = float(rospy.get_param("~settle", 0.7))

        self.pub = rospy.Publisher("cmd_vel", Twist, queue_size=1)
        rospy.on_shutdown(self.stop)

        # Give the publisher time to hook up, otherwise the first few
        # commands are dropped and every distance comes out short.
        rospy.sleep(1.0)

    # ------------------------------------------------------------------ #
    def send(self, v, w):
        msg = Twist()
        msg.linear.x = v
        msg.angular.z = w
        self.pub.publish(msg)

    def stop(self):
        for _ in range(5):
            self.send(0.0, 0.0)
            time.sleep(0.02)

    def hold(self, v, w, duration):
        """Publish (v, w) at 20 Hz for `duration` seconds."""
        rate = rospy.Rate(20.0)
        end = rospy.Time.now() + rospy.Duration.from_sec(duration)
        while not rospy.is_shutdown() and rospy.Time.now() < end:
            self.send(v, w)
            rate.sleep()

    def pause(self):
        self.stop()
        rospy.sleep(self.settle)

    # ------------------------------------------------------------------ #
    def run(self):
        if self.pattern == "stop":
            self.stop()
            return

        if self.pattern == "circle":
            w = self.speed / self.radius if self.radius > 1e-6 else self.turn_speed
            rospy.loginfo("drive_pattern: circle, v=%.3f m/s, w=%.3f rad/s, "
                          "radius=%.3f m.  Ctrl-C to stop.",
                          self.speed, w, self.speed / w if w else float("inf"))
            rate = rospy.Rate(20.0)
            while not rospy.is_shutdown():
                self.send(self.speed, w)
                rate.sleep()
            return

        if self.pattern == "spin":
            duration = abs(self.turns) * 2.0 * math.pi / abs(self.turn_speed)
            rospy.loginfo("drive_pattern: %.1f revolutions at %.3f rad/s "
                          "(%.1f s).  Mark the robot's start heading first.",
                          self.turns, self.turn_speed, duration)
            self.hold(0.0, math.copysign(self.turn_speed, self.turns), duration)
            self.stop()
            rospy.loginfo("drive_pattern: done.  Measure the heading error and "
                          "correct wheel_separation by "
                          "L_new = L_old * (commanded / actual).")
            return

        if self.pattern == "square":
            leg = self.side / self.speed
            quarter = (math.pi / 2.0) / self.turn_speed
            rospy.loginfo("drive_pattern: %d lap(s) of a %.2f m square "
                          "(%.1f s per side, %.1f s per corner)",
                          self.laps, self.side, leg, quarter)
            for lap in range(self.laps):
                for corner in range(4):
                    if rospy.is_shutdown():
                        return
                    rospy.loginfo("  lap %d, side %d", lap + 1, corner + 1)
                    self.hold(self.speed, 0.0, leg)
                    self.pause()
                    self.hold(0.0, self.turn_speed, quarter)
                    self.pause()
            self.stop()
            rospy.loginfo("drive_pattern: done.  Measure the gap between the "
                          "start and finish positions with a tape measure.")
            return

        rospy.logerr("drive_pattern: unknown ~pattern '%s'", self.pattern)


def main():
    rospy.init_node("drive_pattern")
    DrivePattern().run()


if __name__ == "__main__":
    try:
        main()
    except rospy.ROSInterruptException:
        pass
