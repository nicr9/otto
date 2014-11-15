from distutils.core import setup
from otto import OTTO_VERSION

setup(
    name='otto',
    version=OTTO_VERSION,
    author='Nic Roland',
    author_email='nicroland9@gmail.com',
    packages=['otto'],
    data_files=[('otto_res', ['res/config.json', 'res/done.wav'])],
    scripts=['bin/otto'],
    description='Automate your workflow with ease.',
    #long_description=open('README.rst').read(),
)
