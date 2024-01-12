import os

from setuptools import setup, find_packages


def read(f_name):
    return open(os.path.join(os.path.dirname(__file__), f_name)).read()


setup(
    name='nwg-clipman',
    version='0.2.0',
    description='nwg-shell clipboard manager',
    packages=find_packages(),
    include_package_data=True,
    package_data={
        "": ["langs/*"]
    },
    url='https://github.com/nwg-piotr/nwg-clipman',
    license='MIT',
    author='Piotr Miller',
    author_email='nwg.piotr@gmail.com',
    python_requires='>=3.6.0',
    install_requires=[],
    entry_points={
        'gui_scripts': [
            'nwg-clipman = nwg_clipman.main:main'
        ]
    }
)
