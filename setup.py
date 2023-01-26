#!/usr/bin/env python

"""The setup script."""

from setuptools import setup, find_packages

with open('README.rst') as readme_file:
    readme = readme_file.read()

with open('HISTORY.rst') as history_file:
    history = history_file.read()

requirements = ['Click>=7.0', 'aionostr']

test_requirements = [ ]

setup(
    author="Dave St.Germain",
    author_email='dave@st.germa.in',
    python_requires='>=3.9',
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Natural Language :: English',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
    ],
    description="A Python nostr bot framework",
    entry_points={
        'console_scripts': [
            'nostr-bot=nostr_bot.cli:main',
        ],
    },
    install_requires=requirements,
    license="BSD license",
    long_description=readme + '\n\n' + history,
    include_package_data=True,
    keywords='nostr_bot',
    name='nostr_bot',
    packages=find_packages(include=['nostr_bot', 'nostr_bot.*']),
    test_suite='tests',
    tests_require=test_requirements,
    url='https://github.com/davestgermain/nostr_bot',
    version='0.2.0',
    zip_safe=False,
)
