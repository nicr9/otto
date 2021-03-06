from distutils.core import setup
from otto import OTTO_VERSION, OTTO_DESC

setup(
    name='otto',
    version=OTTO_VERSION,
    author='Nic Roland',
    author_email='nicroland9@gmail.com',
    packages=['otto'],
    data_files=[('otto_res', ['res/done.wav'])],
    scripts=['bin/otto'],
    description=OTTO_DESC,
    #long_description=open('README.rst').read(),
)
