#!/usr/bin/env python3
# license removed for brevity
import rospy
from sensor_msgs.msg import JointState

joint_publisher = rospy.Publisher('/fake_joint_states', JointState, queue_size=10)
joint = JointState()
joint.name = ["base", "shoulder", "elbow", "wrist", "wrist_twist"]
joint.position = [0, 0, 0, 0, 0]

def move0():
    global joint
    joint.position[0] = 0
    joint.position[1] = 0
    joint.position[2] = 0
    joint.position[3] = 0
    joint.position[4] = 0

    joint_publisher.publish(joint)
    rospy.sleep(1)


if __name__ == '__main__':
    rospy.init_node('Movement')
    try:
        while not rospy.is_shutdown():
            move0()
            
    except rospy.ROSInterruptException:
        pass