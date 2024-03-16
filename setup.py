from setuptools import setup, find_packages

setup(
    name='olympiatools',
    version='0.1.0',
    author='Nex',
    author_email='info@nex.team',
    description='Software Tools for Olympia Project',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    url='https://github.com/nex-team-inc/olympiatools',
    packages=find_packages(),
    install_requires=[
        # List your project's dependencies here.
        # Examples:
        # 'numpy>=1.18.1',
        # 'requests>=2.23.0',
    ],
    classifiers=[
        # Choose your license as you wish (should match "license" above)
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
    ],
    python_requires='>=3.7',
    entry_points={
        'console_scripts': [
            'olympia = olympiatools.cli:main',
        ],
    },
    include_package_data=True,
    package_data={
        # If any package contains *.txt or *.rst files, include them:
        '': ['*.txt', '*.rst'],
    },
)