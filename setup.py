# -*- coding: utf-8 -*-

from setuptools import setup, find_packages

try:
    long_desc = open('README', 'r').read()
except IOError:
    long_desc = 'This package adds features to Sphinx to make it easier to link to resources on BitBucket.'

requires = ['Sphinx>=0.6', 'docutils>=0.6']

NAME='sphinxcontrib-bitbucket'
VERSION='1.0'

setup(
    name=NAME,
    version=VERSION,
    url = 'http://www.doughellmann.com/projects/%s/' % NAME,
    #download_url = 'http://www.doughellmann.com/downloads/%s-%s.tar.gz' % \
    #                (NAME, VERSION),
    license='BSD',
    author='Doug Hellmann',
    author_email='doug.hellmann@gmail.com',
    description='Sphinx/BitBucket integration',
    long_description=long_desc,
    zip_safe=False,
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Documentation',
        'Topic :: Utilities',
    ],
    platforms='any',
    packages=find_packages(),
    include_package_data=True,
    install_requires=requires,
    namespace_packages=['sphinxcontrib'],
    py_modules = [ 'distribute_setup' ],
)
