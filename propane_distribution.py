# coding=utf-8
import os, re, subprocess, time
from datetime import datetime, date as sysdate
from distutils.command.sdist import sdist as _sdist
from distutils.core import Command

__author__ = 'Tyler Butler <tyler@tylerbutler.com>'

# Inspired by https://github.com/warner/python-ecdsa/blob/0ed702a9d4057ecf33eea969b8cf280eaccd89a1/setup.py#L34

class version_class(object):
    def __init__(self, version_string='0.0.1', date=None, time=None):
        self.version = version_string
        if time is None:
            time = datetime.utcnow()
        if date is None:
            date = time.date
        self.time = time
        self.date = date

    @property
    def string(self):
        return self.version

    def __unicode__(self):
        return self.version

    __str__ = __unicode__
    __repr__ = __unicode__

VERSION_FILENAME = '_version.py'
VERSION_PY = """# coding=utf-8
import time
from datetime import date
from propane_distribution import version_class

# This file is originally generated from Git information by running 'setup.py
# version'. Distribution tarballs contain a pre-generated copy of this file.

__version__ = '{version}'
__date__ = date({year}, {month}, {day})
__time__ = time.gmtime({time})

version = version_class(__version__, __date__, __time__)
"""

GIT_RUN_FAIL_MSG = "unable to run git, leaving %s alone"

def update_version_py(git_tag_prefix='v', version_path=None):
    if version_path is None:
        version_path = os.path.join(os.getcwd(), VERSION_FILENAME)
    else:
        version_path = os.path.join(version_path)

    if not os.path.isdir(".git"):
        print "This does not appear to be a Git repository."
        return
    try:
        p = subprocess.Popen(["git", "describe", "--tags", "--dirty", "--always"],
                             stdout=subprocess.PIPE)
    except EnvironmentError:
        print GIT_RUN_FAIL_MSG % version_path
        return
    stdout = p.communicate()[0]
    if p.returncode != 0:
        print GIT_RUN_FAIL_MSG % version_path
        return
    if stdout.startswith(git_tag_prefix):
        ver = stdout[len(git_tag_prefix):].strip()
    else:
        ver = stdout.strip()
    with open(version_path, 'wb') as f:
        today = sysdate.today()
        #time = calendar.timegm()
        f.write(VERSION_PY.format(version=ver,
                                  year=today.year,
                                  month=today.month,
                                  day=today.day,
                                  time=time.time()))
    print "set %s to '%s'" % (version_path, ver)


def get_version(version_path=None):
    if version_path is None:
        version_path = os.path.join(os.getcwd(), VERSION_FILENAME)
    else:
        version_path = os.path.join(version_path)

    try:
        f = open(version_path)
    except EnvironmentError:
        return None
    for line in f.readlines():
        mo = re.match("__version__ = '([^']+)'", line)
        if mo:
            ver = mo.group(1)
            return ver
    return None


def get_version_path(distcmd):
    if len(distcmd.distribution.package_data) == 1:
        version_path = os.path.join(os.getcwd(), distcmd.distribution.package_data.keys()[0], VERSION_FILENAME)
    else:
        for tmp_path in distcmd.distribution.package_data.keys():
            test_path = os.path.join(os.getcwd(), tmp_path, VERSION_FILENAME)
            if os.path.exists(test_path):
                version_path = test_path
                break
            else:
                version_path = os.path.join(os.getcwd(), distcmd.distribution.package_data.keys()[0], VERSION_FILENAME)
    return version_path


class Version(Command):
    description = "update %s from Git repo" % VERSION_FILENAME
    user_options = [('version-path=', 'f',
                     "path to version file to update [default: %s]" % VERSION_FILENAME),
                    ('tag-prefix', 't',
                     "git tag prefix to use [default: 'v']")]
    boolean_options = []

    def initialize_options(self):
        self.version_path = None
        self.tag_prefix = 'v'

    def finalize_options(self):
        if self.version_path is None:
            self.version_path = get_version_path(self)
        print self.version_path

    def run(self):
        update_version_py(git_tag_prefix=self.tag_prefix, version_path=self.version_path)
        print "Version is now", get_version(version_path=self.version_path)


class sdist(_sdist):
    def initialize_options(self):
        _sdist.initialize_options(self)

    def finalize_options(self):
        _sdist.finalize_options(self)
        self.version_path = get_version_path(self)

    def run(self):
        update_version_py(version_path=self.version_path)
        # unless we update this, the sdist command will keep using the old
        # version
        self.distribution.metadata.version = get_version(self.version_path)
        return _sdist.run(self)

cmdclassdict = {
    'version': Version,
    'sdist': sdist
}


def get_install_requirements():
    requirements = []
    with open('requirements.txt') as file_:
        temp = file_.readlines()
        temp = [i[:-1] for i in temp]

        for line in temp:
            if line is None or line == '' or line.startswith(('#', '-e')):
                continue
            else:
                requirements.append(line)
        return requirements


def get_readme():
    with open('README.md') as file_:
        return file_.read()
