import hashlib
import os
import shutil
import subprocess
import tarfile
import urllib
import zipfile
from waflib import Logs
from waflib.extras.preparation import PreparationContext
from waflib.extras.build_status import BuildStatus
from waflib.extras.filesystem_utils import removeSubdir
from waflib.extras.mirror import MirroredTarFile, MirroredZipFile

__downloadUrl = 'https://capnproto.org/%s'
__posixFile = 'capnproto-c++-0.5.2.tar.gz'
__posixSha256Checksum = '\x23\x14\x5a\x01\x27\xc2\xb1\x62\x9c\x4b\x72\xe6\x00\x0e\x04\x99\x16\x40\xe5\x51\x94\x7f\xa3\x9f\xd0\x67\x10\xd6\x4b\xd9\x42\xa8'
__ntFile = 'capnproto-c++-win32-0.5.2.zip'
__ntSha256Checksum = '\xeb\xf0\x24\xe4\xb6\x39\x0d\xbe\xeb\x7a\xba\xf8\x0a\x54\x5f\xfb\x3a\x6a\x49\xb4\x84\x33\x9b\xea\x8f\xdb\xc3\x4f\xb0\x51\xba\x30'
__srcDir = 'src'

def options(optCtx):
    optCtx.load('dep_resolver')

def prepare(prepCtx):
    prepCtx.options.dep_base_dir = prepCtx.srcnode.find_dir('..').abspath()
    prepCtx.load('dep_resolver')
    status = BuildStatus.init(prepCtx.path.abspath())
    if status.isSuccess():
	prepCtx.msg('Preparation already complete', 'skipping')
	return
    if os.name == 'posix':
	file = MirroredTarFile(
		__posixSha256Checksum,
		__downloadUrl % __posixFile,
		os.path.join(prepCtx.path.abspath(), __posixFile))
    elif os.name == 'nt':
	file = MirroredZipFile(
		__ntSha256Checksum,
		__downloadUrl % __ntFile,
		os.path.join(prepCtx.path.abspath(), __ntFile))
    else:
	prepCtx.fatal('Unsupported OS %s' % os.name)
    prepCtx.msg('Synchronising', file.getSrcUrl())
    if file.sync(10):
	prepCtx.msg('Saved to', file.getTgtPath())
    else:
	prepCtx.fatal('Synchronisation failed')
    extractDir = 'capnproto-c++-0.5.2'
    removeSubdir(prepCtx.path.abspath(), __srcDir, extractDir, 'bin', 'lib', 'include')
    prepCtx.start_msg('Extracting files to')
    file.extract(prepCtx.path.abspath())
    os.rename(extractDir, __srcDir)
    prepCtx.end_msg(os.path.join(prepCtx.path.abspath(), __srcDir))

def configure(confCtx):
    confCtx.load('dep_resolver')
    status = BuildStatus.init(confCtx.path.abspath())
    if status.isSuccess():
	confCtx.msg('Configuration already complete', 'skipping')
	return
    srcPath = os.path.join(confCtx.path.abspath(), __srcDir)
    os.chdir(srcPath)
    if os.name == 'posix':
	returnCode = subprocess.call([
		'sh',
		os.path.join(srcPath, 'configure'),
		'--prefix=%s' % confCtx.srcnode.abspath()])
	if returnCode != 0:
	    confCtx.fatal('Protobuf configure failed: %d' % returnCode)
    elif os.name == 'nt':
	# Nothing to do, just use the provided VS solution
	return
    else:
	confCtx.fatal('Unsupported OS %s' % os.name)

def build(buildCtx):
    status = BuildStatus.load(buildCtx.path.abspath())
    if status.isSuccess():
	Logs.pprint('NORMAL', 'Build already complete                   :', sep='')
	Logs.pprint('GREEN', 'skipping')
	return
    srcPath = os.path.join(buildCtx.path.abspath(), __srcDir)
    os.chdir(srcPath)
    if os.name == 'posix':
	returnCode = subprocess.call([
		'make',
		'install'])
    elif os.name == 'nt':
	returnCode = subprocess.call([
		'devenv.com',
		os.path.join(srcPath, 'vsprojects', 'capnp.sln')])
    else:
	confCtx.fatal('Unsupported OS %s' % os.name)
    if returnCode != 0:
	buildCtx.fatal('Protobuf build failed: %d' % returnCode)
    status.setSuccess()
