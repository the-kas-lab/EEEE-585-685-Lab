#!/usr/bin/env python3
"""
odom_error_logger.py
====================
Logs the disagreement between an odometry estimate and a reference pose, and
writes it to CSV.  This is the measurement tool for the dead-reckoning section
of your report.

In simulation the natural reference is /ground_truth/state, published by the
Gazebo P3D plugin, which reads the true pose straight out of the physics
engine.  On the real robot there is no ground truth, so you compare your
/my_odom against the driver's /odom (that tells you whether your integration
matches ARCOS's, not whether either is correct), and you measure absolute
error by hand with a tape measure at the end of the run.

Both signals are zeroed on their first sample by default, so it does not
matter where the robot was spawned or what pose the driver booted with.

Parameters
----------
~estimate       topic of the estimate under test    (default my_odom)
~reference      topic of the reference pose         (default ground_truth/state)
~output         CSV path, "" disables file output   (default ~/amigo_odom_error.csv)
~rate           sample rate [Hz]                    (default 10.0)
~zero_reference align both signals to their first
                sample                              (default True)
~timeout        warn if either topic is silent for
                this many seconds                   (default 5.0)

Output columns
--------------
t, est_x, est_y, est_yaw, ref_x, ref_y, ref_yaw,
err_x, err_y, err_euclidean, err_yaw, ref_path_length
"""

import math
import os

import rospy
from nav_msgs.msg import Odometry


def yaw_from_quaternion(q):
    """Yaw of a geometry_msgs/Quaternion, without pulling in tf."""
    siny = 2.0 * (q.w * q.z + q.x * q.y)
    cosy = 1.0 - 2.0 * (q.y * q.y + q.z * q.z)
    return math.atan2(siny, cosy)


def wrap_to_pi(angle):
    return math.atan2(math.sin(angle), math.cos(angle))


class Pose2D(object):
    __slots__ = ("x", "y", "yaw", "stamp")

    def __init__(self, x=0.0, y=0.0, yaw=0.0, stamp=0.0):
        self.x, self.y, self.yaw, self.stamp = x, y, yaw, stamp


class OdomErrorLogger(object):

    def __init__(self):
        est_topic = rospy.get_param("~estimate", "my_odom")
        ref_topic = rospy.get_param("~reference", "ground_truth/state")
        self.rate_hz = float(rospy.get_param("~rate", 10.0))
        self.zero = bool(rospy.get_param("~zero_reference", True))
        self.timeout = float(rospy.get_param("~timeout", 5.0))

        default_out = os.path.join(os.path.expanduser("~"),
                                   "amigo_odom_error.csv")
        self.output = rospy.get_param("~output", default_out)

        self.est = None
        self.ref = None
        self.est_origin = None
        self.ref_origin = None
        self.path_length = 0.0
        self._last_ref_xy = None
        self.max_err = 0.0
        self.rows = []
        self.t0 = None

        rospy.Subscriber(est_topic, Odometry, self.est_cb, queue_size=10)
        rospy.Subscriber(ref_topic, Odometry, self.ref_cb, queue_size=10)
        rospy.loginfo("odom_error_logger: '%s' (estimate) vs '%s' (reference)",
                      rospy.resolve_name(est_topic),
                      rospy.resolve_name(ref_topic))
        rospy.on_shutdown(self.finish)

    # ------------------------------------------------------------------ #
    @staticmethod
    def _to_pose(msg):
        return Pose2D(msg.pose.pose.position.x,
                      msg.pose.pose.position.y,
                      yaw_from_quaternion(msg.pose.pose.orientation),
                      msg.header.stamp.to_sec())

    def _relative(self, pose, origin):
        """Pose expressed in the frame of the first sample."""
        if origin is None:
            return pose
        dx = pose.x - origin.x
        dy = pose.y - origin.y
        c, s = math.cos(-origin.yaw), math.sin(-origin.yaw)
        return Pose2D(c * dx - s * dy,
                      s * dx + c * dy,
                      wrap_to_pi(pose.yaw - origin.yaw),
                      pose.stamp)

    def est_cb(self, msg):
        pose = self._to_pose(msg)
        if self.est_origin is None and self.zero:
            self.est_origin = pose
        self.est = pose

    def ref_cb(self, msg):
        pose = self._to_pose(msg)
        if self.ref_origin is None and self.zero:
            self.ref_origin = pose
        self.ref = pose

        rel = self._relative(pose, self.ref_origin)
        if self._last_ref_xy is not None:
            self.path_length += math.hypot(rel.x - self._last_ref_xy[0],
                                           rel.y - self._last_ref_xy[1])
        self._last_ref_xy = (rel.x, rel.y)

    # ------------------------------------------------------------------ #
    def spin(self):
        rate = rospy.Rate(self.rate_hz)
        while not rospy.is_shutdown():
            now = rospy.Time.now().to_sec()
            if self.est is None or self.ref is None:
                rospy.logwarn_throttle(
                    self.timeout,
                    "odom_error_logger: waiting for both topics "
                    "(estimate=%s, reference=%s)"
                    % (self.est is not None, self.ref is not None))
                rate.sleep()
                continue

            if self.t0 is None:
                self.t0 = now

            e = self._relative(self.est, self.est_origin)
            r = self._relative(self.ref, self.ref_origin)

            err_x = e.x - r.x
            err_y = e.y - r.y
            err_d = math.hypot(err_x, err_y)
            err_yaw = wrap_to_pi(e.yaw - r.yaw)
            self.max_err = max(self.max_err, err_d)

            self.rows.append((now - self.t0, e.x, e.y, e.yaw,
                              r.x, r.y, r.yaw,
                              err_x, err_y, err_d, err_yaw,
                              self.path_length))

            rospy.loginfo_throttle(
                2.0,
                "path %.2f m | error %.3f m (%.1f%% of path), yaw %.1f deg"
                % (self.path_length, err_d,
                   100.0 * err_d / self.path_length if self.path_length > 0.05
                   else 0.0,
                   math.degrees(err_yaw)))
            rate.sleep()

    # ------------------------------------------------------------------ #
    def finish(self):
        if not self.rows:
            rospy.loginfo("odom_error_logger: nothing recorded")
            return

        final = self.rows[-1]
        rospy.loginfo("odom_error_logger summary: %d samples, "
                      "path %.3f m, final error %.3f m, peak error %.3f m, "
                      "final heading error %.2f deg",
                      len(self.rows), final[11], final[9], self.max_err,
                      math.degrees(final[10]))

        if not self.output:
            return
        try:
            with open(self.output, "w") as fh:
                fh.write("t,est_x,est_y,est_yaw,ref_x,ref_y,ref_yaw,"
                         "err_x,err_y,err_euclidean,err_yaw,ref_path_length\n")
                for row in self.rows:
                    fh.write(",".join("%.6f" % v for v in row) + "\n")
            rospy.loginfo("odom_error_logger: wrote %s", self.output)
        except IOError as exc:
            rospy.logerr("odom_error_logger: could not write %s (%s)",
                         self.output, exc)


def main():
    rospy.init_node("odom_error_logger")
    OdomErrorLogger().spin()


if __name__ == "__main__":
    try:
        main()
    except rospy.ROSInterruptException:
        pass
