from distutils.core import setup

setup(
    name='otto',
    version='0.1.0',
    author='Nic Roland',
    author_email='nicroland9@gmail.com',
    packages=['otto'],
    data_files=[('otto_res', ['res/config.json', 'res/done.wav'])],
    scripts=['bin/otto'],
    description='For automating your workflow',
    long_description=open('README.rst').read(),
)
