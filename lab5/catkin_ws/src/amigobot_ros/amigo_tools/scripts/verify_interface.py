#!/usr/bin/env python3
"""
verify_interface.py
===================
Automated smoke test for the AmigoBot lab interface.  Run it against a live
simulator or a live robot; it checks that every topic in the interface contract
exists, publishes at a sane rate, and carries data that is physically
consistent with the parameters in amigo_params.yaml.

    # simulation (robot must have ~1.5 m of clear space ahead)
    rosrun amigo_tools verify_interface.py

    # hardware -- slower, shorter, no ground truth
    rosrun amigo_tools verify_interface.py _hardware:=true

    # skip the parts that move the robot
    rosrun amigo_tools verify_interface.py _move:=false

Exit status is 0 if every check passed, 1 otherwise, so you can wire this into
a pre-lab checklist.

Parameters
----------
~hardware    bool   real robot: no ground truth, gentler motion  (default False)
~move        bool   run the motion tests                        (default True)
~wheel_radius, ~wheel_separation, ~min_range, ~max_range
             loaded from amigo_params.yaml; used to check consistency
"""

import math
import sys
import threading
import time

import rospy
import tf2_ros
from geometry_msgs.msg import Twist
from nav_msgs.msg import Odometry
from sensor_msgs.msg import JointState, PointCloud, Range
from std_msgs.msg import Float32MultiArray

GREEN, RED, YELLOW, RESET = "\033[32m", "\033[31m", "\033[33m", "\033[0m"


class Results(object):
    def __init__(self):
        self.rows = []

    def add(self, ok, name, detail=""):
        self.rows.append((ok, name, detail))
        tag = {True: GREEN + "PASS" + RESET,
               False: RED + "FAIL" + RESET,
               None: YELLOW + "WARN" + RESET}[ok]
        print("  [%s] %-42s %s" % (tag, name, detail))
        sys.stdout.flush()

    def summary(self):
        failed = [r for r in self.rows if r[0] is False]
        warned = [r for r in self.rows if r[0] is None]
        print("\n" + "=" * 72)
        print("%d checks: %d passed, %d failed, %d warnings"
              % (len(self.rows), len(self.rows) - len(failed) - len(warned),
                 len(failed), len(warned)))
        if failed:
            print(RED + "\nFAILED:" + RESET)
            for _, name, detail in failed:
                print("  - %s  %s" % (name, detail))
        print("=" * 72)
        return 0 if not failed else 1


class Collector(object):
    """Counts messages on a topic and keeps the most recent one."""

    def __init__(self, topic, msg_type):
        self.topic = topic
        self.count = 0
        self.last = None
        self.t_first = None
        self.lock = threading.Lock()
        self.sub = rospy.Subscriber(topic, msg_type, self._cb, queue_size=50)

    def _cb(self, msg):
        with self.lock:
            if self.t_first is None:
                self.t_first = time.time()
            self.count += 1
            self.last = msg

    def rate(self):
        with self.lock:
            if self.t_first is None or self.count < 2:
                return 0.0
            span = time.time() - self.t_first
            return (self.count - 1) / span if span > 0 else 0.0

    def reset(self):
        with self.lock:
            self.count = 0
            self.t_first = None


def yaw_of(odom):
    q = odom.pose.pose.orientation
    return math.atan2(2.0 * (q.w * q.z + q.x * q.y),
                      1.0 - 2.0 * (q.y * q.y + q.z * q.z))


def wrap(a):
    return math.atan2(math.sin(a), math.cos(a))


def xy_of(odom):
    return (odom.pose.pose.position.x, odom.pose.pose.position.y)


class Verifier(object):

    def __init__(self):
        self.hw = bool(rospy.get_param("~hardware", False))
        self.do_move = bool(rospy.get_param("~move", True))
        self.r = float(rospy.get_param("~wheel_radius", 0.0508))
        self.L = float(rospy.get_param("~wheel_separation", 0.280))
        self.min_range = float(rospy.get_param("~min_range", 0.10))
        self.max_range = float(rospy.get_param("~max_range", 4.00))

        self.res = Results()
        self.cmd_pub = rospy.Publisher("cmd_vel", Twist, queue_size=1)

        self.odom = Collector("odom", Odometry)
        self.wheels = Collector("wheel_velocities", Float32MultiArray)
        self.sonar = Collector("sonar", PointCloud)
        self.joints = Collector("joint_states", JointState)
        self.ranges = [Collector("sonar/range_%d" % i, Range) for i in range(8)]
        self.truth = None if self.hw else Collector("ground_truth/state", Odometry)
        # Peak roll/pitch seen by ground truth while the motion tests run.
        self.max_tilt = None
        if self.truth is not None:
            rospy.Subscriber("ground_truth/state", Odometry, self._tilt_cb,
                             queue_size=10)

        self.tf_buffer = tf2_ros.Buffer()
        self.tf_listener = tf2_ros.TransformListener(self.tf_buffer)

    def _tilt_cb(self, msg):
        if self.max_tilt is None:
            return               # not armed until the motion tests start
        q = msg.pose.pose.orientation
        roll = math.atan2(2.0 * (q.w * q.x + q.y * q.z),
                          1.0 - 2.0 * (q.x * q.x + q.y * q.y))
        pitch = math.asin(max(-1.0, min(1.0, 2.0 * (q.w * q.y - q.z * q.x))))
        if max(abs(roll), abs(pitch)) > max(abs(self.max_tilt[0]),
                                            abs(self.max_tilt[1])):
            self.max_tilt = (roll, pitch)

    # ------------------------------------------------------------------ #
    def drive(self, v, w, seconds):
        """Publish (v, w) at 20 Hz for `seconds` of wall time, then stop."""
        end = time.time() + seconds
        msg = Twist()
        msg.linear.x, msg.angular.z = v, w
        while time.time() < end and not rospy.is_shutdown():
            self.cmd_pub.publish(msg)
            time.sleep(0.05)
        for _ in range(5):
            self.cmd_pub.publish(Twist())
            time.sleep(0.02)
        time.sleep(0.6)          # let the base coast to a stop

    # ------------------------------------------------------------------ #
    def check_topics(self):
        print("\n--- 1. topics and rates " + "-" * 48)
        time.sleep(4.0)          # collect a few seconds of traffic

        for coll, name, lo in ((self.odom, "/odom", 5.0),
                               (self.wheels, "/wheel_velocities", 10.0),
                               (self.sonar, "/sonar", 4.0),
                               (self.joints, "/joint_states", 5.0)):
            hz = coll.rate()
            self.res.add(coll.count > 0 and hz >= lo, "%s publishing" % name,
                         "%.1f Hz" % hz if coll.count else "no messages")

        alive = sum(1 for c in self.ranges if c.count > 0)
        self.res.add(alive == 8, "/sonar/range_0..7 all publishing",
                     "%d of 8 alive" % alive)

        if self.truth is not None:
            self.res.add(self.truth.count > 0, "/ground_truth/state publishing",
                         "%.1f Hz" % self.truth.rate())

    def check_tf(self):
        print("\n--- 2. TF tree " + "-" * 57)
        for parent, child in (("odom", "base_link"),
                              ("base_link", "base_footprint"),
                              ("base_link", "sonar_0_link"),
                              ("base_link", "left_wheel_link")):
            try:
                self.tf_buffer.lookup_transform(parent, child, rospy.Time(0),
                                                rospy.Duration(3.0))
                self.res.add(True, "TF %s -> %s" % (parent, child))
            except Exception as exc:
                hint = ""
                if (parent, child) == ("odom", "base_link"):
                    hint = "(is the driver running? RosAria and the Gazebo " \
                           "diff-drive plugin both broadcast it)"
                self.res.add(False, "TF %s -> %s" % (parent, child),
                             "%s %s" % (type(exc).__name__, hint))

    def check_sonar_values(self):
        print("\n--- 3. sonar sanity " + "-" * 52)
        cloud = self.sonar.last
        if cloud is None:
            self.res.add(False, "sonar cloud content", "no data")
            return

        self.res.add(len(cloud.points) == 8, "sonar cloud has 8 points",
                     "%d points" % len(cloud.points))

        names = [ch.name for ch in cloud.channels]
        self.res.add("range" in names and "index" in names,
                     "sonar cloud has index/range channels", str(names))

        vals = [c.last.range for c in self.ranges if c.last is not None]
        if not vals:
            self.res.add(False, "sonar range values", "no Range messages")
            return

        pinned = sum(1 for v in vals if abs(v - self.min_range) < 1e-3)
        self.res.add(pinned == 0, "no transducer pinned at min_range",
                     "%d of %d pinned -- rays are hitting the chassis; "
                     "raise sonar_min_range" % (pinned, len(vals))
                     if pinned else "min=%.2f max=%.2f m"
                     % (min(vals), max(vals)))

        # Eight independent transducers reading the same value means they are
        # all seeing one common spurious surface -- most often the floor,
        # caught by a vertical ray fan.  This is the check that would have
        # caught the ground-plane bug.
        if len(vals) >= 4:
            spread = max(vals) - min(vals)
            self.res.add(spread > 0.05, "transducers disagree with each other",
                         "spread %.3f m over %d sensors%s"
                         % (spread, len(vals),
                            "" if spread > 0.05 else
                            " -- all reading the same surface, suspect the "
                            "ray fan is hitting the floor"))

        detecting = sum(1 for v in vals if v < self.max_range - 0.05)
        # On hardware an empty patch of floor is legitimate: warn, don't fail.
        self.res.add(True if detecting > 0 else (None if self.hw else False),
                     "at least one transducer sees something",
                     "%d of %d below max range%s"
                     % (detecting, len(vals),
                        "" if detecting else " -- drive nearer a wall"))

        # Cross-check the two representations against each other.
        chans = {ch.name: ch.values for ch in cloud.channels}
        if "range" in chans and "index" in chans:
            worst = 0.0
            for idx, rng in zip(chans["index"], chans["range"]):
                last = self.ranges[int(round(idx))].last
                if last is not None:
                    worst = max(worst, abs(last.range - rng))
            self.res.add(worst < 0.25, "PointCloud and Range agree",
                         "max disagreement %.3f m" % worst)

    def check_wheel_velocities_static(self):
        print("\n--- 4. wheel velocities at rest " + "-" * 40)
        msg = self.wheels.last
        if msg is None:
            self.res.add(False, "wheel_velocities content", "no data")
            return
        self.res.add(len(msg.data) == 2, "wheel_velocities has 2 elements",
                     "len=%d" % len(msg.data))
        if len(msg.data) == 2:
            self.res.add(abs(msg.data[0]) < 0.15 and abs(msg.data[1]) < 0.15,
                         "wheel velocities ~0 while stopped",
                         "[%.3f, %.3f] rad/s" % (msg.data[0], msg.data[1]))

    # ------------------------------------------------------------------ #
    def check_straight(self):
        print("\n--- 5. straight-line motion " + "-" * 44)
        v = 0.10 if self.hw else 0.15
        secs = 3.0
        expected = v * secs

        start_odom = self.odom.last
        start_truth = self.truth.last if self.truth else None
        if start_odom is None:
            self.res.add(False, "straight-line test", "no /odom to compare")
            return

        samples = []
        stop = threading.Event()

        def sample():
            while not stop.is_set():
                m = self.wheels.last
                if m is not None and len(m.data) == 2:
                    samples.append((m.data[0], m.data[1]))
                time.sleep(0.05)

        t = threading.Thread(target=sample)
        t.daemon = True
        t.start()
        self.drive(v, 0.0, secs)
        stop.set()
        t.join(timeout=1.0)

        end_odom = self.odom.last
        d_odom = math.hypot(xy_of(end_odom)[0] - xy_of(start_odom)[0],
                            xy_of(end_odom)[1] - xy_of(start_odom)[1])
        self.res.add(abs(d_odom - expected) < 0.25 * expected,
                     "/odom moved the commanded distance",
                     "%.3f m vs %.3f m commanded" % (d_odom, expected))

        if start_truth is not None and self.truth.last is not None:
            d_true = math.hypot(
                xy_of(self.truth.last)[0] - xy_of(start_truth)[0],
                xy_of(self.truth.last)[1] - xy_of(start_truth)[1])
            self.res.add(abs(d_true - expected) < 0.25 * expected,
                         "ground truth moved the commanded distance",
                         "%.3f m vs %.3f m" % (d_true, expected))

        # omega = v / r for both wheels, and they should be near-equal.
        moving = [s for s in samples if abs(s[0]) + abs(s[1]) > 0.5]
        if moving:
            wl = sum(s[0] for s in moving) / len(moving)
            wr = sum(s[1] for s in moving) / len(moving)
            expect_w = v / self.r
            self.res.add(abs(wl - expect_w) < 0.30 * expect_w
                         and abs(wr - expect_w) < 0.30 * expect_w,
                         "wheel speeds match v/r",
                         "[%.2f, %.2f] vs %.2f rad/s" % (wl, wr, expect_w))
            self.res.add(abs(wl - wr) < 0.15 * expect_w,
                         "left and right agree on a straight line",
                         "difference %.3f rad/s" % abs(wl - wr))
        else:
            self.res.add(False, "wheel speeds during motion",
                         "wheel_velocities stayed near zero while moving -- "
                         "check the source parameter")

    def check_rotation(self):
        print("\n--- 6. rotation and wheelbase consistency " + "-" * 30)
        w = 0.5
        secs = 3.0
        expected = w * secs

        start = self.truth.last if self.truth else self.odom.last
        if start is None:
            self.res.add(False, "rotation test", "no pose source")
            return
        y0 = yaw_of(start)

        samples = []
        stop = threading.Event()

        def sample():
            while not stop.is_set():
                m = self.wheels.last
                if m is not None and len(m.data) == 2:
                    samples.append((m.data[0], m.data[1]))
                time.sleep(0.05)

        t = threading.Thread(target=sample)
        t.daemon = True
        t.start()
        self.drive(0.0, w, secs)
        stop.set()
        t.join(timeout=1.0)

        end = self.truth.last if self.truth else self.odom.last
        turned = abs(wrap(yaw_of(end) - y0))
        # 1.5 rad is under pi, so no unwrapping ambiguity here.
        self.res.add(abs(turned - expected) < 0.30 * expected,
                     "robot turned the commanded angle",
                     "%.2f rad vs %.2f rad" % (turned, expected))

        moving = [s for s in samples if abs(s[1] - s[0]) > 0.5]
        if moving:
            wl = sum(s[0] for s in moving) / len(moving)
            wr = sum(s[1] for s in moving) / len(moving)
            implied_L = (wr - wl) * self.r / w
            self.res.add(abs(implied_L - self.L) < 0.25 * self.L,
                         "implied wheelbase matches parameter",
                         "%.3f m implied vs %.3f m configured"
                         % (implied_L, self.L))

    def check_level(self):
        """Simulation only: the model must stay level while it drives.

        A base whose centre of mass sits on the wheel axle tips onto its nose
        during ordinary driving and stays there, and the front sonars then
        range off the floor at ~0.26 m.  The checks above can all pass while
        that happens, so track the peak tilt over every motion test, plus two
        hard stops (forward then back, so repeated runs do not walk the robot
        into a wall).
        """
        print("\n--- 7. stability while driving (simulation) " + "-" * 28)
        if self.max_tilt is None:
            self.res.add(None, "robot stays level while driving",
                         "no ground truth")
            return
        self.drive(0.4, 0.0, 1.0)
        self.drive(-0.4, 0.0, 1.0)
        time.sleep(1.0)
        roll, pitch = self.max_tilt
        tilt = math.degrees(max(abs(roll), abs(pitch)))
        self.res.add(tilt < 3.0, "robot stays level while driving",
                     "peak roll %.1f deg, peak pitch %.1f deg"
                     % (math.degrees(roll), math.degrees(pitch)))

    def check_my_odom(self):
        print("\n--- 8. student odometry (/my_odom) " + "-" * 37)
        try:
            topics = dict(rospy.get_published_topics())
        except Exception:
            topics = {}
        if "/my_odom" not in topics:
            self.res.add(None, "/my_odom present",
                         "not running -- start the Task 4 node to test it")
            return

        my = Collector("my_odom", Odometry)
        ref = self.truth if self.truth else self.odom
        p0_my, p0_ref = None, None
        time.sleep(1.0)
        if my.last is None:
            self.res.add(False, "/my_odom publishing", "no messages")
            return
        p0_my, p0_ref = xy_of(my.last), xy_of(ref.last)

        self.drive(0.10 if self.hw else 0.15, 0.0, 3.0)

        d_my = math.hypot(xy_of(my.last)[0] - p0_my[0],
                          xy_of(my.last)[1] - p0_my[1])
        d_ref = math.hypot(xy_of(ref.last)[0] - p0_ref[0],
                           xy_of(ref.last)[1] - p0_ref[1])
        self.res.add(abs(d_my - d_ref) < max(0.05, 0.15 * d_ref),
                     "/my_odom tracks the reference",
                     "%.3f m vs %.3f m" % (d_my, d_ref))

        self.res.add(my.last.header.frame_id == "odom"
                     and my.last.child_frame_id == "base_link",
                     "/my_odom frame ids",
                     "%s -> %s" % (my.last.header.frame_id,
                                   my.last.child_frame_id))

    # ------------------------------------------------------------------ #
    def run(self):
        print("=" * 72)
        print("AmigoBot interface verification -- %s"
              % ("HARDWARE" if self.hw else "SIMULATION"))
        print("wheel_radius=%.4f m  wheel_separation=%.4f m" % (self.r, self.L))
        if self.do_move:
            print(YELLOW + "The robot WILL move: ~0.5 m forward and one "
                  "in-place turn. Clear the area." + RESET)
        print("=" * 72)

        self.check_topics()
        self.check_tf()
        self.check_sonar_values()
        self.check_wheel_velocities_static()

        if self.do_move:
            if self.truth is not None:
                self.max_tilt = (0.0, 0.0)       # arm the tilt monitor
            self.check_straight()
            self.check_rotation()
            if not self.hw:
                self.check_level()
            self.check_my_odom()
        else:
            print("\n(motion tests skipped: _move:=false)")

        return self.res.summary()


def main():
    rospy.init_node("verify_interface", anonymous=True)
    verifier = Verifier()
    rospy.on_shutdown(lambda: verifier.cmd_pub.publish(Twist()))
    sys.exit(verifier.run())


if __name__ == "__main__":
    try:
        main()
    except rospy.ROSInterruptException:
        pass
