from setuptools import setup
from otto import OTTO_VERSION, OTTO_DESC

setup(
    name='otto_base',
    version=OTTO_VERSION,
    author='Nic Roland',
    author_email='nicroland9@gmail.com',
    packages=['otto'],
    package_data={'otto': ['wavs/*.wav']},
    zip_safe=False,
    scripts=['bin/otto'],
    description=OTTO_DESC,
    install_requires=[
        'lament',
        'pydialog',
        ],
    license='MIT',
    url = 'https://github.com/nicr9/otto',
    download_url = 'https://github.com/nicr9/otto/tarball/%s' % OTTO_VERSION,
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        'Operating System :: POSIX :: Linux',
        'Programming Language :: Python :: 2.7',
        'Topic :: Software Development',
        'Topic :: Utilities',
        ],
)
