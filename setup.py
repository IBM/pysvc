##############################################################################
# Copyright 2019 IBM Corp.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
##############################################################################

import pysvc
from setuptools import setup, find_packages

install_requires = ['munch', 'paramiko']

setup(
    name='pysvc',
    version=pysvc.version,
    description="IBM Spectrum Virtualize Python Client",
    long_description="CLI Python Client for IBM Spectrum "
                     "Virtualize Family Storage.",
    author="Peng Wang",
    author_email="wangpww@cn.ibm.com",
    maintainer="Peng Wang",
    keywords=["IBM", "Spectrum Virtualize Family Storage"],
    requires=install_requires,
    install_requires=install_requires,
    tests_require=['nose', 'mock'],
    license="Apache License, Version 2.0",
    include_package_data=True,
    packages=find_packages(),
    provides=['pysvc'],
    url="https://github.com/IBM/pysvc",
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'Intended Audience :: System Administrators',
        'Environment :: Console',
        'License :: OSI Approved :: Apache Software License',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3.7',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ])
