# encoding=utf-8
"""Main library for filtering the active Notepad++ file buffer through an x-to-HTML filter, and launches the resulting temporary file in a viewer

aka: make a PythonScript replacement for PreviewHTML.dll that uses the browser instead of an embedded HTML render engine

* Reading .ini file:
    * done: I have subclassed ConfigParser in order to give me a safe version without interpolation
* Filtering:
    * done: replace %1
    * done: spawn filter command
    * done: send filtered output to default verb
    * done: base the temporary file name on the buffer, so it will have a meaningful name
* Viewing:
    * done: launches default viewer
    * future: :config(section, 'ViewerCommand / ViewerVerb') -- see below
* Configuring:
    * done: dedicated ini file, rather than PreviewHTML.ini
    * done: make sure it can handle %AppData% or the newer config locations
      = actually, use notepad.getPluginConfigDir(), to always be in right location
    * done: if pyscFilteredViewer\pyyscFilteredViewer.ini does not exist, either copy from PreviewHTML\Filters.ini,
          or create a dummy entry, which must be edited.
* debug mode
    * done: If you run pyscFilteredViewer.py, it will run just like PreviewHTML's filter task, unless you run `pyscfv_setDebug(True)`
    * done: If you run pyscFilteredViewerLibrary.py directory, it will turn on debug prints and show the console, but run the same code.

LONG TERM TODO:
    future option: allow it to keep the temporary              :config(DEFAULT, 'KeepFilteredOutput')
    future option: allow destination formats other than HTML   :config(section, 'FilterOutputType')
    future option: allow executing alternate verbs             :config(section, 'ViewerCommand' or 'ViewerVerb')
"""
from Npp import *
import ConfigParser
import os
import tempfile
import subprocess
import string
from time import sleep

__pyscfv_MESSAGE = ''

__pyscfv_DEBUG = False
def pyscfv_setDebug(flag):
    """sets the DEBUG flag either true or false

    DEBUG mode on will do many extra prints to the Notepad++ PythonScript Python-Console

    Running the pyscFilteredViewerLibrary as a 'script' will default to DEBUG on.
    Running any script that imports functions from pyscFilteredViewerLibrary will default to DEBUG off."""
    global __pyscfv_DEBUG
    __pyscfv_DEBUG = flag
    if flag:
        console.show()
        console.clear()
    if __pyscfv_DEBUG or __pyscfv_TRACE: console.write('pyscfv_setDebug({})\n'.format(flag))

__pyscfv_TRACE = False
def pyscfv_setTrace(flag):
    """sets the TRACE flag either true or false

    TRACE mode on will print to the Notepad++ PythonScript Python-Console
    every time it enters a pysc function"""
    global __pyscfv_TRACE
    __pyscfv_TRACE = flag
    if flag:
        console.show()
        console.clear()
    if __pyscfv_TRACE: console.write('pyscfv_setTrace()\n')

__pyscfv_KEEPTEMP = True
def pyscfv_setKeepTemp(flag):
    """sets the KEEPTEMP flag either true or false

    KEEPTEMP mode on will not delete the temporary file when done
    (this will allow hooking into callbacks, and similar )"""
    global __pyscfv_KEEPTEMP
    __pyscfv_KEEPTEMP = flag
    if __pyscfv_TRACE: console.write('pyscfv_setKeepTemp()\n')

def pyscfv_cleanTempDir():
    """cleans out the tempdir()/pyscFilteredViewer subdir, creating it if it doesn't already exist"""
    if __pyscfv_TRACE: console.write('pyscfv_cleanTempDir()\n')
    folder = os.path.normpath( os.path.join( tempfile.gettempdir(), 'pyscFilteredViewer' ) )
    if not os.path.exists(folder):
        os.mkdir(folder)
    for f in os.listdir(folder):
        full = os.path.normpath( os.path.join( folder, f ) )
        if os.path.isfile( full ):
            console.write("DEBUG: deleting '{}'\n".format(full))
            os.unlink(full)

class SafeRawConfigParser(ConfigParser.RawConfigParser):
    """"SafeRawConfigParser will give the 'safe' version of .set() method to the RawConfigParser, without the %-interpolations of ConfigParser or SafeConfigParser"""
    def set(self, section, option, value):
        """wrapper around RawConfigParser.set: generate a TypeError if not string or unicode object"""

        if type(value) is not str and type(value) is not unicode:
            raise TypeError('value={} {} is neither a string or unicode string'.format(value, type(value)))

        return ConfigParser.RawConfigParser.set(self, section, option, value)

class pyscFilteredViewer_Exception(Exception):
    """Errors in this class are unique to the pyscFilteredViewer"""
    def __init__(self, message, *args):
        # call the base class constructor -- ie, raise the real exception
        super(pyscFilteredViewer_Exception,self).__init__(message, *args)

        # also want a popup
        notepad.messageBox( message, 'pyscFilteredViewer fatal error', MESSAGEBOXFLAGS.OK | MESSAGEBOXFLAGS.ICONERROR)

def pyscfv_EditConfig():
    """open the config ini for editing in Notepad++"""
    if __pyscfv_TRACE: console.write('pyscfv_EditConfig()\n')
    cfgfile = pyscfv_establishConfigFile()
    notepad.open( cfgfile )

def pyscfv_warningMessage(message, title, doEditConfig=False):
    """This is a non-fatal error message.  It is printed to the PythonScript console, and a message box is created"""
    if __pyscfv_TRACE: console.write('pyscfv_warningMessage()\n')
    console.writeError( "\n\n{}\n{}\n\n{}\n".format(title, '-'*40, message) )
    notepad.messageBox( message, title, MESSAGEBOXFLAGS.OK | MESSAGEBOXFLAGS.ICONWARNING)
    if doEditConfig:
        pyscfv_EditConfig()

def pyscfv_readFiltersIni():
    """This reads the PreviewHTML-style filters.ini file, and returns the ConfigParser object"""
    if __pyscfv_TRACE: console.write('pyscfv_readFilteresIni()\n')
    config = SafeRawConfigParser()    # https://docs.python.org/2/library/configparser.html
    cfgfile = pyscfv_establishConfigFile()
    if __pyscfv_DEBUG: console.write('cfgfile="{}"\n'.format(cfgfile))
    config.read(cfgfile)

    return config

def pyscfv_parseConfig(config):
    """This takes the ConfigParser object and extracts the data into a dictionary

    Also might make a reverse map for extensions and for languages
    """
    if __pyscfv_TRACE: console.write('pyscfv_parseConfig()\n')

    deep = dict(config=None, languages={}, extensions={})

    deep['config'] = { s:dict(config.items(s)) for s in config.sections() }       # https://stackoverflow.com/a/28990982/5508606


    ext_sections  = {}  # dictionary of extension => section pairs
    for s in config.sections():
        lang = config.get(s, 'language')
        deep['languages'][lang] = s
        x = config.get(s, 'extension')
        for ext in x.split():           # split on whitespace
            deep['extensions'][ext] = s
            # I had tried replacing this `for ext` loop with `deep['extensions'] = { ext:s for ext in x.split() }`,
            # but that overwrites deep['extensions'] with every section, so I only got the last section's-worth

    if __pyscfv_DEBUG:
        console.write('config     = {}\n'.format(deep['config']))
        console.write('languages  = {}\n'.format(deep['languages']))
        console.write('extensions = {}\n'.format(deep['extensions']))
        console.write('deep = {}\n'.format(deep))

    return deep

def pyscfv_pickSectionBasedOnActiveFile(cfgDict, edit_config_on_fail = False):
    """pick the appropriate configuration section, based on the cfgDict's reverse-maps, and the currently-active file in Notepad++"""
    if __pyscfv_DEBUG or __pyscfv_TRACE: console.write('pyscfv_pickSectionBasedOnActiveFile()\n')
    # this is basically MakeChoiceBasedOnLanguage.py
    fileName = notepad.getCurrentFilename()                 # filename of the current buffer
    fileLangEnum = notepad.getCurrentLang()                 # gets the LANGTYPE enum for the current buffer
    fileLangName = notepad.getLanguageName(fileLangEnum)    # converts LANGTYPE to the official string for the selected language
    if __pyscfv_DEBUG: console.write('\tfile = "{}"\n\tlanguage = "{}"\n\tlanguage name = "{}"\n'.format( fileName, fileLangEnum, fileLangName ))
    if fileLangEnum is LANGTYPE.USER:                       # UDL will have fileLangName = "udf - UdlLanguageName"
        fileLangName = (fileLangName.split(' - '))[1]       # grab the specific UdlLanguageName
        if __pyscfv_DEBUG: console.write('\tUDL = "{}"\n'.format( fileLangName ) )

    if fileLangName in cfgDict['languages']:
        return cfgDict['languages'][fileLangName]           # this is the section for the active file

    # since a matching filter wasn't found based on the file's language,
    # resort to extension parsing:
    fileExt  = (os.path.splitext(fileName))[1]              # the 1th element should be the extension, if there is one
    if __pyscfv_DEBUG: console.write('\tfilename extension = "{}"\n'.format( fileExt ) )
    if fileExt in cfgDict['extensions']:
        return cfgDict['extensions'][fileExt]               # this is the section for the active file

    errtitle = 'pyscFilteredViewer: no config found'
    errmsg = 'Could not find an appropriate configuration section for' + '\n\n'
    errmsg = errmsg + '"{}"'.format(fileName) + '\n\n'
    errmsg = errmsg + 'in the pyscFilteredViewer configuration file.' + '\n\n'
    errmsg = errmsg + 'Need a [SECTION] that contains at least one of\n'
    errmsg = errmsg + '    Language={}\n'.format(fileLangName)
    errmsg = errmsg + '    Extension={}\n'.format(fileExt)
    errmsg = errmsg + '    Command={}\n'.format(r'c:\some\path\to\filter "%1"')
    if edit_config_on_fail:
        pyscfv_warningMessage(errmsg, errtitle, edit_config_on_fail)
    else:
        global __pyscfv_MESSAGE
        __pyscfv_MESSAGE = errmsg + '\n\n' + 'Running the pyscfvEditConfig script will open the config file for you'
    return

def pyscfv_errorCheckSection(cDict, section):
    """Error checks "section"; if it does not have a 'command' setting, generate a warning and return None"""
    if __pyscfv_TRACE: console.write('pyscfv_errorCheckSection()\n')

    # if it exists, return the section
    if 'command' in cDict['config'][section]:
        return section

    # otherwise generate the error
    errtitle = 'pyscFilteredViewer: no Command found in config'
    errmsg = 'Please ensure that your pyscFilteredViewer config file contains the Command option: it should look like' + '\n\n'
    errmsg = errmsg + '    [{}]\n'.format(section)
    for o in cDict['config'][section]:
        errmsg = errmsg + '    {}={}\n'.format(o.capitalize(), cDict['config'][section][o])
    errmsg = errmsg + r'    Command={} "%1"\n'.format(r'c:\path\to\filter')
    pyscfv_warningMessage(errmsg, errtitle, True)

    # ... and return None
    return None


def pyscfv_diplayFilteredOutput(cDict, section, ext='html', skipLaunch=False):
    """Filters the activce file, and launches the appropriate viewer for the filter-output.

    1. runs the filter defined in the given section on the active file buffer into a temporary file
    2. opens the temporary file in the appropriate viewer (for now, the default OPEN action defined in windows file associations)
    3. returns the temporary file name (so it can be deleted later)
    """

    if __pyscfv_DEBUG or __pyscfv_TRACE: console.write("displayFilteredOutput(): cDict = {}\n".format(repr(cDict)))

    # ensure there is a selected section
    if section is None:
        tempFile = __pyscfv_message_as_html(__pyscfv_MESSAGE, 'editConfig')
        pyscfv_launch_default_app(tempFile)
        return tempFile
        #was: raise pyscFilteredViewer_Exception('There is no appropriate section found.  Programmer should have exited earlier in the flow')


    # ensure it has a filter command
    if pyscfv_errorCheckSection(cDict, section) is None:
        return  # already gave the warning, so don't need to raise another exception

    # 1 filter the source file to a temporary file
    sourceFile = notepad.getCurrentFilename()                 # filename of the current buffer
    tempFile = pyscfv_filter_file( cDict['config'][section]['command'], sourceFile )

    # 2 launch default viewer for the temporary file
    if not skipLaunch: pyscfv_launch_default_app(tempFile)

    # 3 return filename so it can be deleted later
    return tempFile

def __pyscfv_message_as_html(msg, src_fname):
    """Outputs the message to a named temporary file"""
    if __pyscfv_TRACE: console.write('pyscfv_filter_file()\n')

    dst_path = os.path.normpath( os.path.join( tempfile.gettempdir(), 'pyscFilteredViewer', '.'.join(('{:08X}'.format(0xFFFFFFFF), os.path.basename(src_fname), 'FILTERED', 'html')) ) )
    parent = os.path.dirname(dst_path)
    if not os.path.exists(parent):
        os.mkdir(parent)

    f = open(dst_path, mode='wt')
    f.writelines(['<!DOCTYPE html>\n<meta charset="UTF-8">\n<html>\n<xmp>\n',msg,'</xmp>\n</html>'])
    f.close()
    if __pyscfv_DEBUG: console.write('"{}": file = {} bytes\n'.format(f.name, os.path.getsize(f.name)))

    return f.name

def pyscfv_filter_file(cmd, src_fname):
    """run the filter command on the given file"""
    if __pyscfv_TRACE: console.write('pyscfv_filter_file()\n')

    import zlib
    c32 = zlib.crc32(src_fname)
    if __pyscfv_DEBUG: console.write('crc(src) = {:08X}\n'.format( c32 ) )

    #ext = 'html'
    #f = tempfile.NamedTemporaryFile(mode='wt', suffix='.'+ext, delete=False)
    dst_path = os.path.normpath( os.path.join( tempfile.gettempdir(), 'pyscFilteredViewer', '.'.join(('{:08X}'.format(c32), os.path.basename(src_fname), 'FILTERED', 'html')) ) )
    parent = os.path.dirname(dst_path)
    if not os.path.exists(parent):
        os.mkdir(parent)

    f = open(dst_path, mode='wt')


    # replace %1 with the source file name
    command = cmd.replace('%1', os.path.normpath(src_fname))

    # this is experimenting with the cwd, so I don't need a `cd {} &&` prefix before command
    #retval = subprocess.call( 'pwd && echo "{}"'.format(command) , stdout=f, cwd=os.path.normpath(tempfile.gettempdir()), shell=True )
    retval = subprocess.call( command , stdout=f, cwd=os.path.normpath(tempfile.gettempdir()), shell=True )
    if __pyscfv_DEBUG: console.write("after subprocess.call = {}\n". format(retval))
    f.close()
    if __pyscfv_DEBUG: console.write('"{}": file = {} bytes\n'.format(f.name, os.path.getsize(f.name)))

    return f.name

def pyscfv_launch_default_app(fname):
    """uses os.startfile() to launch the file with the default windows association"""
    if __pyscfv_TRACE: console.write('pyscfv_launch_default_app()\n')

    # os.startfile()    # https://docs.python.org/2/library/os.html#os.startfile
    if os.path.exists(fname): os.startfile(fname)

def pyscfv_establishConfigFile():
    """Establishes a valid Config File, and returns the name to it

    Checks for existence of appropriate config directories.
    If it doesn't exist, create it (or exception-out).
    If created the directory, but PreviewHTML config already exists, copy the PreviewHTML\Filters.ini to pyscFilteredViewer.ini
    If the file finally exists, return the path to the caller.
    """
    if __pyscfv_DEBUG or __pyscfv_TRACE: console.write('pyscfv_establishConfigFile()\n')

    pcd = notepad.getPluginConfigDir()
    if __pyscfv_DEBUG: console.write("Main plugin config directory:\n\t{}\n".format(pcd))

    # check for main config path
    if not os.path.exists(pcd):
        raise pyscFilteredViewer_Exception('No plugins/config directory at\n\t{}\n'.format(pcd))

    # check for appropriate subdir, and instantiate if not there
    #   (also, if PreviewHTML existed, copy over it's Filters.ini to start things off)
    pcdfv = pcd + r'\pyscFilteredViewer'
    if __pyscfv_DEBUG: console.write("this app's config subdirectory:\n\t{}\n".format(pcdfv))
    if not os.path.exists(pcdfv):
        os.mkdir(pcdfv) # create it
        if __pyscfv_DEBUG: console.write("\tdidn't exist, so created it\n")
        if os.path.exists(pcd+r'\PreviewHTML\Filters.ini'):
            # populate it from PreviewHTML\Filters.ini, if that old plugin exists
            if __pyscfv_DEBUG: console.write("\tbut PreviewHTML\\Filters.ini does, so start from there...\n")
            from shutil import copyfile
            copyfile(pcd+r'\PreviewHTML\Filters.ini', pcdfv+r'\pyscFilteredViewer.ini')

    # make sure ini file exists, and create if it's not there
    pyscfvini = pcdfv+r'\pyscFilteredViewer.ini'
    if __pyscfv_DEBUG: console.write("this app's config file:\n\t{}\n".format(pyscfvini))
    if not os.path.exists(pyscfvini):
        # create a new dummy
        if __pyscfv_DEBUG: console.write("TODO = create new dummy ini file\n")
        bat = os.path.normpath( os.path.join(os.path.dirname(os.path.abspath(__file__)), 'ExampleConverterCommand.bat'))
        if not os.path.exists(bat):
            pyscFilteredViewer_Exception( 'Could not find example file-converter, which should have been bundled with pyscFilteredViewer, at "{}"\n'.format(bat) )
        with open(pyscfvini, 'wt', 0) as f:
            f.write('''; pyscFilteredViewer Config File (compatible with PreviewHTML Filters.ini file)
; Everything after ; are comments, and will help you read/understand the ini file
[IniFile]                                          ;   => this is the name of the section; it must be unique.  Typically, based on the language
Extension=.ini .cfg                                ;   => space-separated list of filename extensions, including the period.
Language=INI                                       ;   => this is the name of the language (from Notepad++'s perspective): for a UDL, use your "UserName" from the UDL dialog
; the 'Command=' line below is the filter command;
;   the first part of the command should be the full path to the command
;       if it has spaces in the path, it MUST have quotes around it
;       if it does not have spaces in the path, it still MAY have quotes around it
;   %1 is the name of the active file/buffer; it is in quotes "%1" because the path might contain spaces, and windows needs the quotes to know it's a single filename
;   the command must result in the HTML being dumped to STDOUT
Command="{}" "%1"
; this example command just wraps the text of the INI file in HTML XMP tags, so the browser will render it as plaintext inside an HTML file'''.format(bat))

    # final check for ini file existing
    if not os.path.exists(pyscfvini):
        raise pyscFilteredViewer_Exception('Could not create config file:\n\t{}\n'.format(pyscfvini))
    elif __pyscfv_DEBUG:
        console.write("Verified config file exists!\n")

    # finally done!
    return pyscfvini


def pyscfv_FilteredViewer():
    """Configures and runs the filter for one-shot useage"""
    if __pyscfv_TRACE: console.write('pyscfv_FilteredViewer()\n')

    configObj  = pyscfv_readFiltersIni()
    configDict = pyscfv_parseConfig(configObj)
    section    = pyscfv_pickSectionBasedOnActiveFile(configDict, True)
    if section is None: return
    tmpfile    = pyscfv_diplayFilteredOutput(configDict, section)
    if tmpfile is None: return
    if os.path.exists(tmpfile) and not(__pyscfv_KEEPTEMP):
        sleep(3)                # give it time to load
        os.unlink(tmpfile)
    return

def pyscfv_Register_FilterOnSave():
    """Register the pyscfv_FilterOnSave function for the FILESAVED event"""
    if __pyscfv_DEBUG or __pyscfv_TRACE: console.write('pyscfv_Register_FilterOnSave()\n')
    pyscfv_Callback_FilterOnSave.configDict = pyscfv_parseConfig( pyscfv_readFiltersIni() )

    # run it once making sure to launch the application,
    # but the callback version will not relaunch (so refreshes in the browser are user's responsibility)
    section    = pyscfv_pickSectionBasedOnActiveFile(pyscfv_Callback_FilterOnSave.configDict, True)
    if section is None: return pyscfv_UnRegister_FilterOnSave()
    tmpfile    = pyscfv_diplayFilteredOutput(pyscfv_Callback_FilterOnSave.configDict, section, skipLaunch=False)
    if __pyscfv_DEBUG: console.write('\tsection={}\n\ttmpfile={}\n'.format(section, tmpfile))

    pyscfv_Callback_FilterOnSave.tmpfiles = [tmpfile]

    # register the callback
    notepad.callback(pyscfv_Callback_FilterOnSave, [NOTIFICATION.FILESAVED])

    if __pyscfv_DEBUG: console.write('Tempfiles at end of Register FilterOnSave = {}\n'.format(pyscfv_Callback_FilterOnSave.tmpfiles))

    # notify the UI that it's registered
    pyscfv_OverrideStatusBar(True)

def pyscfv_OverrideStatusBar(filterIsOn):
    """if filterIsOn, override status bar to indicate filter, otherwise return to default status bar"""
    if __pyscfv_DEBUG or __pyscfv_TRACE: console.write('pyscfv_OverrideStatusBar()\n')
    fileLangDesc = notepad.getLanguageDesc(notepad.getCurrentLang())    # converts LANGTYPE to the official string for the selected language
    if filterIsOn:
        strStatusBar =  u'{} {}'.format( u'\u00A0⇉📺⇉\u00A0', fileLangDesc )                         # ⇉📺⇉ TYPE
    else:
        strStatusBar =  u'{}'.format( fileLangDesc )                                                # TYPE
    notepad.setStatusBar(STATUSBARSECTION.DOCTYPE, strStatusBar.encode('utf8'))

def pyscfv_UnRegister_FilterOnSave():
    """UnRegisters the pyscfv_FilterOnSave function for the FILESAVED event"""
    if __pyscfv_DEBUG or __pyscfv_TRACE: console.write('pyscfv_UnRegister_FilterOnSave()\n')
    pyscfv_Callback_FilterOnSave.configDict = None
    notepad.clearCallbacks(pyscfv_Callback_FilterOnSave)

    pyscfv_Callback_FilterOnSave.tmpfiles = []

    # notify the UI that it's unregistered
    pyscfv_OverrideStatusBar(False)

def pyscfv_Toggle_FilterOnSave():
    """Toggles whether or not the FilterOnSave function is active (registered)"""
    if __pyscfv_DEBUG or __pyscfv_TRACE: console.write('pyscfv_Toggle_FilterOnSave()\n')
    if not hasattr(pyscfv_Callback_FilterOnSave, 'configDict'):
        if __pyscfv_DEBUG: console.write('TOGGLE: DNE: so register'+'\n')
        pyscfv_Register_FilterOnSave()
    elif pyscfv_Callback_FilterOnSave.configDict is None:
        if __pyscfv_DEBUG: console.write('TOGGLE: None: so register'+'\n')
        pyscfv_Register_FilterOnSave()
    else:
        if __pyscfv_DEBUG: console.write('TOGGLE: Found: so unregister'+'\n')
        pyscfv_UnRegister_FilterOnSave()

def pyscfv_Callback_FilterOnSave(kwargs):
    """This is the callback for when you want to filter on save events"""
    if __pyscfv_DEBUG or __pyscfv_TRACE: console.write('pyscfv_Callback_FilterOnSave()\n')

    # error check
    if pyscfv_Callback_FilterOnSave.configDict is None:
        raise pyscFilteredViewer_Exception('FilterOnSave Callback was not properly registered')

    # debug
    if __pyscfv_DEBUG: console.write('Existing Tempfiles before Callback FilterOnSave = {}\n'.format(pyscfv_Callback_FilterOnSave.tmpfiles))

    # grab section for current file
    section    = pyscfv_pickSectionBasedOnActiveFile(pyscfv_Callback_FilterOnSave.configDict, False)
    # was: if section is None: return pyscfv_UnRegister_FilterOnSave()

    # re-filter the file once without displaying (logic for displaying was easier later)
    tmpfile = pyscfv_diplayFilteredOutput(pyscfv_Callback_FilterOnSave.configDict, section, skipLaunch=True)

    # by updating without launching (above), then I can use the returned tmpfile to determine whether or not to launch (here)
    if not tmpfile in pyscfv_Callback_FilterOnSave.tmpfiles:
        pyscfv_launch_default_app(tmpfile)
        pyscfv_Callback_FilterOnSave.tmpfiles.append(tmpfile)

    if __pyscfv_DEBUG: console.write('Tempfiles at end of Callback FilterOnSave = {}\n'.format(pyscfv_Callback_FilterOnSave.tmpfiles))

    # notify the UI that it's registered
    pyscfv_OverrideStatusBar(True)

    return

# when i first load the library, clean out the tempdir
pyscfv_cleanTempDir()

# ##### GET RID OF THE LIBRARY-AS-SCRIPT BEHAVIOR!!!
# if it's launched in main-mode, rather than imported, use the debug single filter
#if __name__=='__main__':
#    pyscfv_setDebug(True)
#    pyscfv_FilteredViewer()

# if I need a debug version of one of the helper scripts (ie, I made changes to pyscFilteredViewerLibrary.py during development)
############################################
## load or reload (in case it's changed)
#if 'pyscFilteredViewerLibrary' in globals():
#    reload(pyscFilteredViewerLibrary)
#else:
#    import pyscFilteredViewerLibrary
############################################