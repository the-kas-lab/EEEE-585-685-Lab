"""A simple kinematic model of our Husky A200 for Lab 6.

This is not a physics simulator. It stands in for the robot's velocity
controller: it listens on the same topic, has the same command timeout and
(approximately) the same velocity and acceleration limits, integrates the
motion, and publishes odometry and TF. twist_mux runs in front of it with the
real robot's configuration (see config/twist_mux.yaml).
"""

import math

import rclpy
from geometry_msgs.msg import Point, TransformStamped, Twist
from nav_msgs.msg import Odometry
from rclpy.node import Node
from rclpy.qos import DurabilityPolicy, QoSProfile
from tf2_ros import TransformBroadcaster
from visualization_msgs.msg import Marker, MarkerArray


def _ramp(current, target, max_step):
    if target > current:
        return min(target, current + max_step)
    return max(target, current - max_step)


class HuskySim(Node):

    def __init__(self):
        super().__init__('husky_sim')
        p = self.declare_parameter
        self.timeout = p('cmd_vel_timeout', 0.5).value
        self.v_max = p('max_linear_velocity', 1.0).value
        self.w_max = p('max_angular_velocity', 2.0).value
        self.a_max = p('max_linear_acceleration', 3.0).value
        self.alpha_max = p('max_angular_acceleration', 6.0).value
        self.odom_frame = p('odom_frame', 'odom').value
        self.base_frame = p('base_frame', 'base_link').value
        self.stop_mark = p('stop_mark_x', 3.0).value
        rate = p('rate', 50.0).value

        self.cmd_v = 0.0
        self.cmd_w = 0.0
        self.cmd_time = None
        self.v = 0.0
        self.w = 0.0
        self.x = 0.0
        self.y = 0.0
        self.th = 0.0
        self.last = self.get_clock().now()

        self.create_subscription(Twist, 'platform/cmd_vel_unstamped', self.on_cmd, 10)
        self.odom_pub = self.create_publisher(Odometry, 'platform/odom', 10)
        self.tf = TransformBroadcaster(self)
        latched = QoSProfile(depth=1, durability=DurabilityPolicy.TRANSIENT_LOCAL)
        self.floor_pub = self.create_publisher(MarkerArray, '/lab6/floor', latched)
        self.publish_floor()
        self.create_timer(1.0 / rate, self.step)
        self.get_logger().info('Simulated Husky ready')

    def on_cmd(self, msg):
        self.cmd_v = max(-self.v_max, min(self.v_max, msg.linear.x))
        self.cmd_w = max(-self.w_max, min(self.w_max, msg.angular.z))
        self.cmd_time = self.get_clock().now()

    def step(self):
        now = self.get_clock().now()
        dt = (now - self.last).nanoseconds * 1e-9
        self.last = now
        if dt <= 0.0 or dt > 0.5:
            return

        target_v, target_w = 0.0, 0.0
        if self.cmd_time is not None:
            age = (now - self.cmd_time).nanoseconds * 1e-9
            if age <= self.timeout:
                target_v, target_w = self.cmd_v, self.cmd_w

        self.v = _ramp(self.v, target_v, self.a_max * dt)
        self.w = _ramp(self.w, target_w, self.alpha_max * dt)
        self.th += self.w * dt
        self.x += self.v * math.cos(self.th) * dt
        self.y += self.v * math.sin(self.th) * dt

        stamp = now.to_msg()
        qz, qw = math.sin(self.th / 2.0), math.cos(self.th / 2.0)

        odom = Odometry()
        odom.header.stamp = stamp
        odom.header.frame_id = self.odom_frame
        odom.child_frame_id = self.base_frame
        odom.pose.pose.position.x = self.x
        odom.pose.pose.position.y = self.y
        odom.pose.pose.orientation.z = qz
        odom.pose.pose.orientation.w = qw
        odom.twist.twist.linear.x = self.v
        odom.twist.twist.angular.z = self.w
        self.odom_pub.publish(odom)

        tf = TransformStamped()
        tf.header.stamp = stamp
        tf.header.frame_id = self.odom_frame
        tf.child_frame_id = self.base_frame
        tf.transform.translation.x = self.x
        tf.transform.translation.y = self.y
        tf.transform.rotation.z = qz
        tf.transform.rotation.w = qw
        self.tf.sendTransform(tf)

    def publish_floor(self):
        """Taped line along x with the stopping mark, as on the lab floor."""
        def marker(mid, mtype, rgb, scale):
            m = Marker()
            m.header.frame_id = self.odom_frame
            m.ns = 'floor'
            m.id = mid
            m.type = mtype
            m.action = Marker.ADD
            m.pose.orientation.w = 1.0
            m.scale.x, m.scale.y, m.scale.z = scale
            m.color.r, m.color.g, m.color.b = rgb
            m.color.a = 1.0
            return m

        line = marker(0, Marker.LINE_STRIP, (1.0, 1.0, 1.0), (0.04, 0.0, 0.0))
        line.points = [Point(x=0.0), Point(x=self.stop_mark + 1.5)]
        mark = marker(1, Marker.LINE_STRIP, (1.0, 0.1, 0.1), (0.06, 0.0, 0.0))
        mark.points = [Point(x=self.stop_mark, y=-0.5), Point(x=self.stop_mark, y=0.5)]
        label = marker(2, Marker.TEXT_VIEW_FACING, (1.0, 0.1, 0.1), (0.0, 0.0, 0.2))
        label.pose.position.x = self.stop_mark
        label.pose.position.y = 0.7
        label.text = f'stop mark ({self.stop_mark:.1f} m)'
        self.floor_pub.publish(MarkerArray(markers=[line, mark, label]))


def main():
    rclpy.init()
    node = HuskySim()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.try_shutdown()


if __name__ == '__main__':
    main()
