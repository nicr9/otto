from distutils.core import setup

setup(
    name='otto',
    version='0.1.0',
    author='Nic Roland',
    author_email='nicroland9@gmail.com',
    packages=['otto'],
    scripts=['bin/otto'],
    description='For automating your workflow',
    long_description=open('README.rst').read(),
)
