#!/usr/bin/env python3
"""
sonar_aggregator.py
===================
Simulation-side half of the sonar bridge.

Gazebo publishes one sensor_msgs/Range per transducer on /sonar/range_0 ...
/sonar/range_7.  RosAria, on the real AmigoBot, publishes a single
sensor_msgs/PointCloud containing one point per transducer at the location of
the detected echo.  This node converts the former into the latter so that the
subscriber you write for Lab Task 3 works unchanged on hardware.

Each output point is the echo location expressed in the robot body frame:

    p_i = ( x_i + r_i * cos(yaw_i),
            y_i + r_i * sin(yaw_i),
            z_i )

where (x_i, y_i, z_i, yaw_i) is the mounting pose of transducer i and r_i is
its measured range.  Two channels are attached to make life easier than plain
RosAria: "index" (0..7) and "range" (metres).

Parameters
----------
~sonar_poses    list of dicts {id, x, y, z, yaw}.  Normally loaded from
                amigo_description/config/amigo_params.yaml.
~frame_id       output cloud frame                     (default base_link)
~rate           publish rate [Hz]                      (default 10.0)
~range_topic_ns prefix for the input Range topics      (default sonar/range_)
~drop_max_range if True, omit transducers reporting no
                echo instead of placing a point at the
                maximum range                          (default False)

Topics
------
subscribe   <range_topic_ns><id>  (sensor_msgs/Range), one per pose
publish     sonar                 (sensor_msgs/PointCloud)
"""

import math

import rospy
from geometry_msgs.msg import Point32
from sensor_msgs.msg import ChannelFloat32, PointCloud, Range

DEFAULT_POSES = [
    {"id": 0, "x": 0.070, "y": 0.100, "z": 0.02, "yaw": 1.5708},
    {"id": 1, "x": 0.125, "y": 0.075, "z": 0.02, "yaw": 0.7156},
    {"id": 2, "x": 0.144, "y": 0.030, "z": 0.02, "yaw": 0.2618},
    {"id": 3, "x": 0.144, "y": -0.030, "z": 0.02, "yaw": -0.2618},
    {"id": 4, "x": 0.120, "y": -0.075, "z": 0.02, "yaw": -0.7156},
    {"id": 5, "x": 0.070, "y": -0.100, "z": 0.02, "yaw": -1.5708},
    {"id": 6, "x": -0.146, "y": -0.058, "z": 0.02, "yaw": -2.5307},
    {"id": 7, "x": -0.146, "y": 0.058, "z": 0.02, "yaw": 2.5307},
]


class SonarAggregator(object):

    def __init__(self):
        self.poses = rospy.get_param("~sonar_poses", DEFAULT_POSES)
        self.frame_id = rospy.get_param("~frame_id", "base_link")
        self.rate_hz = float(rospy.get_param("~rate", 10.0))
        self.prefix = rospy.get_param("~range_topic_ns", "sonar/range_")
        self.drop_max = bool(rospy.get_param("~drop_max_range", False))

        if not self.poses:
            rospy.logfatal("sonar_aggregator: ~sonar_poses is empty")
            raise rospy.ROSInitException("no sonar poses")

        self.poses = sorted(self.poses, key=lambda p: int(p["id"]))
        self.latest = {}          # id -> Range

        self.pub = rospy.Publisher("sonar", PointCloud, queue_size=10)
        self.subs = []
        for pose in self.poses:
            sid = int(pose["id"])
            topic = "%s%d" % (self.prefix, sid)
            self.subs.append(
                rospy.Subscriber(topic, Range, self.make_cb(sid), queue_size=5))
        rospy.loginfo("sonar_aggregator: bridging %d Range topics ('%s*') "
                      "into PointCloud on '%s'",
                      len(self.poses), self.prefix,
                      rospy.resolve_name("sonar"))

    def make_cb(self, sid):
        def cb(msg):
            self.latest[sid] = msg
        return cb

    def spin(self):
        rate = rospy.Rate(self.rate_hz)
        while not rospy.is_shutdown():
            if self.latest:
                cloud = PointCloud()
                cloud.header.stamp = rospy.Time.now()
                cloud.header.frame_id = self.frame_id

                index_ch = ChannelFloat32(name="index", values=[])
                range_ch = ChannelFloat32(name="range", values=[])

                for pose in self.poses:
                    sid = int(pose["id"])
                    msg = self.latest.get(sid)
                    if msg is None:
                        continue

                    r = msg.range
                    no_echo = (not math.isfinite(r)) or r >= msg.max_range
                    if no_echo:
                        if self.drop_max:
                            continue
                        r = msg.max_range
                    r = max(r, msg.min_range)

                    yaw = float(pose["yaw"])
                    cloud.points.append(Point32(
                        x=float(pose["x"]) + r * math.cos(yaw),
                        y=float(pose["y"]) + r * math.sin(yaw),
                        z=float(pose.get("z", 0.02))))
                    index_ch.values.append(float(sid))
                    range_ch.values.append(float(r))

                cloud.channels = [index_ch, range_ch]
                self.pub.publish(cloud)
            else:
                rospy.logwarn_throttle(
                    10.0, "sonar_aggregator: no Range messages received yet on "
                          "'%s*'" % self.prefix)
            rate.sleep()


def main():
    rospy.init_node("sonar_aggregator")
    try:
        node = SonarAggregator()
    except rospy.ROSInitException:
        return
    node.spin()


if __name__ == "__main__":
    try:
        main()
    except rospy.ROSInterruptException:
        pass
