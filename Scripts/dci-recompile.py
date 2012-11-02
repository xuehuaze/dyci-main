#!/usr/bin/env python
import hashlib
import os
import time
import shutil

import random
from subprocess import Popen
import subprocess
from sys import stderr, stdout
from clangParams import parseClangCompileParams
import sys

#----------------------------------------------------------------------------------
def removeDynamicLibsFromDirectory(dir):
    if dir[-1] == os.sep: dir = dir[:-1]
    try:
        files = os.listdir(dir)
    except:
        print 'Directory %s does not exists' % dir
        return
    for file in files:
        if file.endswith(".dylib") or file.endswith("resource"): 
            path = dir + os.sep + file
            if os.path.isdir(path):
                continue
            else:
                os.unlink(path)
#----------------------------------------------------------------------------------
def copyResource(source, dci):
    try:
       fileHandle = open( dci + '/bundle', 'r' )
    except IOError as e:
       stderr.write("Error when tried to copy resource :( Cannot find file at " + dci + '/bundle')
       exit(1)

    bundlePath = fileHandle.read()
    fileHandle.close()

    shutil.copy(source, bundlePath)
    stdout.write("File " + source + " was successfully copied to application")

    try:
       fileHandle = open( dci + '/resource', 'w' )
       fileHandle.write(source)
    except IOError as e:
       stderr.write("Error when tried to write to file " + dci + '/resource')
       exit(1)

    fileHandle.close()

    exit(0);    

#----------------------------------------------------------------------------------


DCI_ROOT_DIR = os.path.expanduser('~/.dci')

args = sys.argv

filename = ''
try:
    filename = args[1]
except:
    stderr.write("Incorrect usage. Path to .m file should be used as the parameter")
    exit(1)

# In case of resources..
if filename[-4:] == ".png" or filename[-4:] == ".jpg" or filename[-5:] == ".jpeg": copyResource(filename, DCI_ROOT_DIR)

# In case of header files
# In some cases you need be able to recompile M file, when you are in header
if filename[-2:] == ".h": filename = os.path.splitext(filename)[0] + ".m"

# loading it's params from the file
indexFileLocation = DCI_ROOT_DIR + '/index/' + hashlib.md5(filename).hexdigest()


params = []
try:
    params = [line.strip() for line in open(indexFileLocation)]
except:
    stderr.write("Couldn't load index file '%s' (%s). Use default compilation instead" % (indexFileLocation, filename))
    exit(1)

# searching params by filename

if not params:
    stderr.write("Could not find saved params for file %s. File need to be compiled first " % filename)
    exit(1)


# Switching to the specified working directory
workingDir = params[len(params)-1]
os.chdir(workingDir)
params = params[:-1]


# Searching where is Xcode with it's Clang located
process = Popen(["xcode-select","-print-path"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE)
xcodeLocation, err = process.communicate()
xcodeLocation = xcodeLocation.rstrip(os.linesep)

compileString = [xcodeLocation + '/Toolchains/XcodeDefault.xctoolchain/usr/bin/clang-real'] \
                + params

#Compiling file again
process = Popen(compileString,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE)
output, err = process.communicate()

# emulating output / err
stdout.write(output)
stderr.write(err)

if process.returncode != 0:
    exit(process.returncode)

#Compilation was successful... performing linking
clangParams = parseClangCompileParams(params)

#removing old library
removeDynamicLibsFromDirectory(DCI_ROOT_DIR)

#creating new random name wor the dynamic library
libraryName = "dci%s.dylib" % random.randint(0, 10000000)

# {'class':className,
#        'object':objectCompilation,
#        'arch':arch,
#        'isysroot':isysroot,
#        'LParams':Lparams,
#        'FParams':Fparams,
#        'minOSParam':minOSParam
#}

#Running linker, that will create dynamic library for us
linkArgs = \
[xcodeLocation + "/Toolchains/XcodeDefault.xctoolchain/usr/bin/clang-real"] \
+ ["-arch"] + [clangParams['arch']]\
+ ["-dynamiclib"]\
+ ["-isysroot"] + [clangParams['isysroot']]\
+ clangParams['LParams']\
+ clangParams['FParams']\
+ [clangParams['object']]\
+ ["-install_name"] + ["/usr/local/lib/" + libraryName]\
+ ['-Xlinker']\
+ ['-objc_abi_version']\
+ ['-Xlinker']\
+ ["2"]\
+ ["-ObjC"]\
+ ["-undefined"]\
+ ["dynamic_lookup"]\
+ ["-fobjc-arc"]\
+ ["-fobjc-link-runtime"]\
+ ["-Xlinker"]\
+ ["-no_implicit_dylibs"]\
+ [clangParams['minOSParam']]\
+ ["-single_module"]\
+ ["-compatibility_version"]\
+ ["5"]\
+ ["-current_version"]\
+ ["5"]\
+ ["-o"]\
+ [DCI_ROOT_DIR + "/" + libraryName]
#       + ['-v']

#print "Linker arks \n%s" % ' '.join(linkArgs)

linkerProcess = Popen(linkArgs,
                      stdout=subprocess.PIPE,
                      stderr=subprocess.PIPE)
output, err = linkerProcess.communicate()

# emulating output / err
stdout.write(output)
stderr.write(err)

exit(linkerProcess.returncode)




