#!/usr/bin/env python3
"""
sonar_splitter.py
=================
Hardware-side half of the sonar bridge -- the exact inverse of
sonar_aggregator.py.

RosAria publishes one sensor_msgs/PointCloud with an echo point per
transducer.  This node recovers the scalar range of each transducer,

    r_i = || p_i - o_i ||     (in the x-y plane)

where o_i is the mounting position of transducer i, and republishes it as
sensor_msgs/Range on /sonar/range_0 ... /sonar/range_7.  That gives you the
same eight Range topics in the lab that you had in simulation, so RViz layouts
and any Range-based obstacle-avoidance code carry over.

Point ordering is assumed to follow transducer index 0..7 unless the incoming
cloud carries an "index" channel, in which case that channel wins.

Parameters
----------
~sonar_poses    list of dicts {id, x, y, z, yaw}
~min_range      [m]                                   (default 0.10)
~max_range      [m]                                   (default 4.00)
~fov            cone width [rad]                      (default 0.14)
~frame_prefix   frame name prefix per transducer      (default sonar_)
~frame_suffix                                          (default _link)
~range_topic_ns output topic prefix                   (default sonar/range_)

Topics
------
subscribe   sonar                 (sensor_msgs/PointCloud)
publish     <range_topic_ns><id>  (sensor_msgs/Range)
"""

import math

import rospy
from sensor_msgs.msg import PointCloud, Range

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


class SonarSplitter(object):

    def __init__(self):
        poses = rospy.get_param("~sonar_poses", DEFAULT_POSES)
        self.poses = {int(p["id"]): p for p in poses}
        self.order = sorted(self.poses.keys())

        self.min_range = float(rospy.get_param("~min_range", 0.10))
        self.max_range = float(rospy.get_param("~max_range", 4.00))
        self.fov = float(rospy.get_param("~fov", 0.14))
        self.frame_prefix = rospy.get_param("~frame_prefix", "sonar_")
        self.frame_suffix = rospy.get_param("~frame_suffix", "_link")
        prefix = rospy.get_param("~range_topic_ns", "sonar/range_")

        self.pubs = {sid: rospy.Publisher("%s%d" % (prefix, sid), Range,
                                          queue_size=5)
                     for sid in self.order}

        self.sub = rospy.Subscriber("sonar", PointCloud, self.cloud_cb,
                                    queue_size=5)
        rospy.loginfo("sonar_splitter: '%s' -> %d Range topics ('%s*')",
                      rospy.resolve_name("sonar"), len(self.order), prefix)

    def _indices(self, msg):
        """Transducer index for each point in the cloud."""
        for ch in msg.channels:
            if ch.name in ("index", "id", "sonar_index"):
                if len(ch.values) == len(msg.points):
                    return [int(round(v)) for v in ch.values]
        # Fall back on positional ordering.
        return list(self.order)[:len(msg.points)]

    def cloud_cb(self, msg):
        indices = self._indices(msg)
        for point, sid in zip(msg.points, indices):
            pose = self.poses.get(sid)
            if pose is None or sid not in self.pubs:
                continue

            r = math.hypot(point.x - float(pose["x"]),
                           point.y - float(pose["y"]))

            out = Range()
            out.header.stamp = msg.header.stamp if msg.header.stamp != rospy.Time() \
                else rospy.Time.now()
            out.header.frame_id = "%s%d%s" % (self.frame_prefix, sid,
                                              self.frame_suffix)
            out.radiation_type = Range.ULTRASOUND
            out.field_of_view = self.fov
            out.min_range = self.min_range
            out.max_range = self.max_range
            out.range = min(max(r, self.min_range), self.max_range)
            self.pubs[sid].publish(out)


def main():
    rospy.init_node("sonar_splitter")
    SonarSplitter()
    rospy.spin()


if __name__ == "__main__":
    try:
        main()
    except rospy.ROSInterruptException:
        pass
