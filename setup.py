"""
Fantasy COTY python package configuration.

Conor Rafferty <craffer@umich.edu>
"""

from setuptools import setup

setup(
    name='fantasy_coty',
    version='0.1.1',
    packages=['fantasy_coty'],
    include_package_data=True,
    install_requires=[
        'ff-espn-api'
    ],
)
