"""Given code for Lab 6: copy these imports and main() into your node file.

It starts ROS, puts the terminal in keyboard mode, runs your node, and makes
sure that a zero command is published when the node exits (Ctrl-C or an
error). You write the TeleopNode class and its stop() method.
"""

import rclpy
from rclpy.signals import SignalHandlerOptions

from husky_teleop.keyboard import Keyboard


def main():
    rclpy.init(signal_handler_options=SignalHandlerOptions.NO)
    with Keyboard() as kb:
        node = TeleopNode(kb)      # your class
        try:
            rclpy.spin(node)
        except KeyboardInterrupt:
            pass
        finally:
            node.stop()            # your method: publish a zero command
            node.destroy_node()
            rclpy.shutdown()
