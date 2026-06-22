from setuptools import find_packages, setup

package_name = 'dvrk_cares_rqt_plugin'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(where='src'),
    package_dir={'': 'src'},
    data_files=[
        ('share/ament_index/resource_index/packages', ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml', 'plugin.xml']),
        ('share/' + package_name + '/resource', ['resource/MyPlugin.ui']),
    ],
    install_requires=['setuptools'],
    scripts=['scripts/dvrk_cares_rqt_plugin.py'],
    entry_points={
        'console_scripts': [
            'dvrk_cares_rqt_plugin = dvrk_cares_rqt_plugin.scripts.dvrk_cares_rqt_plugin:main',
        ],
    },
    zip_safe=False,
    maintainer='maysara',
    maintainer_email='maysara@todo.todo',
    description='CARES Lab rqt plugin for dVRK assistant controls',
    license='TODO',
    tests_require=['pytest'],
)
