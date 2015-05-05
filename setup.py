from setuptools import setup
from otto import OTTO_VERSION, OTTO_DESC

setup(
    name='otto',
    version=OTTO_VERSION,
    author='Nic Roland',
    author_email='nicroland9@gmail.com',
    packages=['otto'],
    package_data={'otto': ['wavs/*.wav']},
    zip_safe=False,
    scripts=['bin/otto'],
    description=OTTO_DESC,
)
