from setuptools import setup, find_packages
from net.aircable import __version__

setup(
    name='aircable-library-op',
    version=__version__,
    description='AIRcable libraries for BlueZ Development',
    author='Manuel Francisco Naranjo',
    author_email='manuel@aircable.net',
    url='https://github.com/OpenProximity/aircable-library',
    packages=find_packages(),
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Framework :: Django',
    ],
    include_package_data=True,
    zip_safe=False,
    install_requires = ['dbus', 'gobject', 'json']
)
