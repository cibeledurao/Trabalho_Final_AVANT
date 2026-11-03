import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch_ros.actions import Node

def generate_launch_description():
    pkg_share = get_package_share_directory('faulty_or_not')
    params_file = os.path.join(pkg_share, 'config', 'params.yaml')

    return LaunchDescription([
        Node(
            package='faulty_or_not',
            executable='mission_node',
            name='mission_node',
            output='screen',
            parameters=[params_file]
        ),
        Node(
            package='faulty_or_not',
            executable='navigation_node',
            name='navigation_node',
            output='screen',
            parameters=[params_file],
            sigterm_timeout='30',
            sigkill_timeout='30'
        ),
        Node(
            package='faulty_or_not',
            executable='vision_node',
            name='vision_node',
            output='screen',
            parameters=[params_file]
        ),
    ])
