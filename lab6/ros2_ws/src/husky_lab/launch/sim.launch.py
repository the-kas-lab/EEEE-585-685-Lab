"""Simulated Husky for Lab 6: twist_mux (robot's config) + kinematic model + RViz."""

import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.conditions import IfCondition
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node

NAMESPACE = 'a200_0252'


def generate_launch_description():
    share = get_package_share_directory('husky_lab')
    with open(os.path.join(share, 'urdf', 'husky.urdf')) as f:
        urdf = f.read()

    rviz = LaunchConfiguration('rviz')

    return LaunchDescription([
        DeclareLaunchArgument('rviz', default_value='true',
                              description='Start RViz (set false when there is no display)'),
        Node(
            package='twist_mux', executable='twist_mux', name='twist_mux',
            namespace=NAMESPACE,
            parameters=[os.path.join(share, 'config', 'twist_mux.yaml')],
            remappings=[('cmd_vel_out', 'platform/cmd_vel_unstamped')],
        ),
        Node(
            package='husky_lab', executable='husky_sim', name='platform_velocity_controller',
            namespace=NAMESPACE,
            parameters=[os.path.join(share, 'config', 'husky_sim.yaml')],
            output='screen',
        ),
        Node(
            package='robot_state_publisher', executable='robot_state_publisher',
            parameters=[{'robot_description': urdf}],
        ),
        Node(
            package='rviz2', executable='rviz2',
            arguments=['-d', os.path.join(share, 'rviz', 'husky.rviz')],
            condition=IfCondition(rviz),
        ),
    ])
