from distutils.core import setup

setup(
    name='otto',
    version='v0.5',
    author='Nic Roland',
    author_email='nicroland9@gmail.com',
    packages=['otto'],
    data_files=[('otto_res', ['res/config.json', 'res/done.wav'])],
    scripts=['bin/otto'],
    description='Automate your workflow with ease.',
    #long_description=open('README.rst').read(),
)
