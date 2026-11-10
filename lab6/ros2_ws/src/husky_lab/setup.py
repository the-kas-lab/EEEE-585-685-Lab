from glob import glob

from setuptools import setup

package_name = 'husky_lab'

setup(
    name=package_name,
    version='1.0.0',
    packages=[package_name],
    data_files=[
        ('share/ament_index/resource_index/packages', ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        ('share/' + package_name + '/launch', glob('launch/*.launch.py')),
        ('share/' + package_name + '/config', glob('config/*.yaml')),
        ('share/' + package_name + '/urdf', glob('urdf/*.urdf')),
        ('share/' + package_name + '/rviz', glob('rviz/*.rviz')),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='EEEE-585/685 TAs',
    maintainer_email='noreply@rit.edu',
    description='Lab 6: simulated Husky A200',
    license='BSD-3-Clause',
    entry_points={
        'console_scripts': [
            'husky_sim = husky_lab.sim:main',
        ],
    },
)
