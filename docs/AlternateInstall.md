# ⇉📺⇉ pyscFilteredViewer

The main [README INSTALL](../README.md#INSTALL) instructions should cover installing pyscFilteredViewer under a normal installation of Notepad++ and PythonScript, such that the pyscFilteredViewer scripts go in the `%AppData%\Notepad++\plugins\config\PythonScript\scripts\pyscFilteredViewer\ ` directory.

# Alternate Install Locations

If you have a "portable" version of Notepad++, where the `doLocalConf.xml` file is in the same directory as `notepad++.exe`, then PythonScript will _not_ look in the `%AppData%` hierarchy for scripts.  Instead, it will look in `<notepad++.exe directory>\plugins\config\PythonScript\scripts\ `, so you will want to unzip the pyscFilteredViewer scripts into `<notepad++.exe directory>\plugins\config\PythonScript\scripts\pyscFilteredViewer\ `.

## User Scripts vs Machine Scripts
A note on "user scripts" vs "machine scripts": PythonScript hsa two locations for its scripts, which it calls "user scripts" and "machine scripts".  The user scripts are intented to be unique per user of a computer, whereas the machine scripts are common to all users of that computer.  The above instructions will put the scripts into the "user scripts" section.

In the main **Plugins > PythonScript > Scripts** menu, you won't see any difference between the two locations.  If you go to **Plugins > PythonScript > Configuration...**, however, the dialog will only show you one or the other, depending on the radio-button selection at the top.

If you want the scripts to go in the "machine scripts" location, so that they are available to all users with an installed copy of Notepad++ (usually in the `%ProgramFiles%` or `%ProgramFiles(x86)%` hierarchy) then unzip into `<notepad++.exe directory>\plugins\PythonScript\scripts\pyscFilteredViewer\ ` (note that this version doesn't have the `\config\` in the path).
