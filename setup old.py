#!/usr/bin/env python

from distutils.core import setup

setup(
    name='Mastobot Bundle',
    version='0.0.1',
    description='Python utilities for Mastodn apps',
    author='lgbaixauli',
    author_email='lgbaixauli@gamil,com',
    url='https://github.com/lgbaixauli/mastobot-bundle',
    packages=['bundle'],
    install_requires=[
       'bs4',
   ],
)