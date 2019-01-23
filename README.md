# ⇉📺⇉ pyscFilteredViewer
Runs files through filter to their default associated action with OnSave event (or on request) [for Notepad++ using PythonScript]

## Table of Contents

* [TOP](#pyscfilteredviewer)
* [Inspiration / Justification](#inspiration--justification)
* [Installation](#installation)
  * [Installation Prerequisites](#installation-prerequsisites)
  * [Installation Procedure](#installation-procedure)
  * [Scripts](#scripts)
* [Configuration](#configuration)
* [One-time Filtering](#one-time-filtering)
* [Filter On Save](#filter-on-save)
* [Future Features](#future-features)

## Inspiration / Justification
This was inspired by the [PreviewHTML](http://fossil.2of4.net/npp_preview) plugin for Notepad++, which was designed to embed an HTML-previewer in Notepad++.  But the more-useful-to-me feature was that you could apply a filter program to the current file, and it would filter into HTML, which would then be rendered in the PreviewHTML window.  Unfortunately, PreviewHTML hasn't been updated to work with 64-bit Notepad++ (though the developer has been working on it on and off for more than a year, as of Jan 2019), and I'd really like to transition to 64bit as my main editor.

Since I primarily care about the filter-to-a-viewer format, and would be willing to use an external viewer (like my default web browser), I realized I could implement the pass-the-current-file-through-a-filter feature using PythonScript, and then launch the filtered HTML file in the user's default web browser.

I have kept the configuration file compatbile with PreviewHTML's `filters.ini` -- and, in fact, if you already have that plugin installed, **pyscFilteredViewer** will copy the PreviewHTML `filters.ini` configuration file for its own use

## Installation

### Installation Prerequsisites

* [Notepad++](https://notepad-plus-plus.org/) -- text editor with plugin capability
* [PythonScript](https://github.com/bruderstein/PythonScript/) -- a plugin for Notepad++ which can be used to automate tasks inside Notepad++ using Python 2.7

### Installation Procedure

1. Download the [latest release](https://github.com/pryrt/pyscFilteredViewer/releases/latest).
2. Unzip into the appropriate PythonScript scripts location:
    * under Notepad++ 7.5.9 and earlier,
        * "machine scripts" (visible to all users) would be installed under the `notepad++.exe` install-directory, in `plugins\PythonScript\scripts\ `
        * "user scripts" (visible to the current user) would be installed under `%AppData%\Notepad++\plugins\config\PythonScript\scripts `
    * Notepad 7.6.0 and 7.6.1 were in a state of flux, and I do not recommended trying to install these scripts under those Notepad++ versions.
    * under Notepad++ 7.6.2:
        * "machine scripts": the `notepad++.exe` install-directory
        * "user scripts": `%AppData%\Notepad++\plugins\config\PythonScript\scripts ` and/or `%ProgramData%\notepad++\plugins\config\PythonScript\scripts `
    * either of these should create a `pyscFilteredViewer\ ` subdirectory, with appropriate scripts (described in [**Scripts**](#scripts), below)
3. If you had Notepad++ open, close and reload Notepad++ .
    * This will cause Notepad++ and PythonScript to see the new scripts
    * You can see them in the **Plugins > PythonScript > Scripts** menu
4. Run **Plugins > PythonScript > Scripts > pyscFilteredViewer > pyscfvEditConfig ** to configure this utility: see [**Configuration**](#configuration) (below) for configuration details

### Scripts

* `pyscFilteredViewerLibrary.py` -- this is the main library, which all the other scripts will use.  Not intended for being run directly as a PythonScript script (though it will actually behave similarly to `pyscFilteredViewer.py` if run standalone, except will turn on copious debug information)
* `pyscfvEditConfig.py` -- running this script will load the `psycFilteredViewer.ini` file, and allow you to edit it (see [**Configuration**](#configuration), below)
* `pyscFilteredViewer.py` -- running this script will do a one-time filter of the active file (see [**One-time Filtering**](#one-time-filtering), below)
* `pyscfvToggleFilterOnSave.py` -- running this script will toggle between running the filter any time the file is saved and not running it (equivalent to choosing the correct version of pyscfvRegisterFilterOnSave or pyscfvUnRegisterFilterOnSave) (see [**Filter On Save**](#filter-on-save), below)
* `pyscfvRegisterFilterOnSave.py` -- this will set up Notepad++ to run the filter any time any file is saved (see [**Filter On Save**](#filter-on-save), below)
* `pyscfvUnRegisterFilterOnSave.py` -- this will stop Notepad++ from running the filter any time any file is saved (see [**Filter On Save**](#filter-on-save), below)

## Configuration

The first time you run any of the scripts (though I recommend `pyscfvEditConfig` as the first), it will create a configuration file called `pyscFilteredViewer.ini`.  (If it finds a PreviewHTML `filters.ini` file, it will copy that to the new location and name.)

The configuration file is used to set the filter-command on a per-file-type basis (where a file-type is based on either the **Language** that Notepad++ has set for the file, or the file extension).  Each file-type needs its own section in the config file.

The default configuration file looks something like:

    ; pyscFilteredViewer Config File (compatible with PreviewHTML Filters.ini file)
    ;Lines starting with ; are comments -- you need to uncomment them, or create a new section with the similar uncommented format as the example below:
    ;[IniFile]                                          ;   => this is the name of the section; it must be unique.  Typically, based on the language
    ;Extension=.ini .cfg                                ;   => space-separated list of filename extensions, including the period.
    ;Language=INI                                       ;   => this is the name of the language (from Notepad++'s perspective): for a UDL, use your "UserName" from the UDL dialog
    ;Command=C:\usr\local\scripts\preview-ini.bat "%1"  ;   => this is the filter command; %1 is the name of the active file/buffer; the command must result in the HTML being dumped to STDOUT

* **[SECTION]**: each section in the config file is a logical grouping, which will define the filter command for a given file-type. The section name chosen is irrelevant, as long as it is unique.  It is recommended that it be similar to the **Language** setting
    * example ⇒ `[IniFile]`
* **Extension**: this setting is a space-separated list of filename extensions (including the period/dot)
    * example ⇒ `Extension=.ini .cfg`
* **Language**: this is the name of the "language" of the file (Notepad++ calls the file-type "Language", since it's often a programming language, like "Python" or "Perl")
    * If you want this to work for a User Defined Language (UDL), use whatever name you saved it as from the **Language > Define Your Language** dialog, **Save As...** button
    * example ⇒ `Language=INI` -- this assumes Notepad++ calls the language for .ini files "INI" (it does in my versions)
* **Command**: this is the command to use to filter the file into HTML.
    * To reference the filename of the source file (ie, the file that's in Notepad++), use `%1`.  Since the file's path and or name may have a space, it is highly recommended to always enclose it in quotes, as `"%1"`
    * The path to the command (executable, batch file, or anything else "runnable" from a Windows perspective) should be spelled out, as it is likely not in your PATH
    * example ⇒ `Command=C:\usr\local\scripts\preview-ini.bat "%1"`

**NOTE**: you technically only need one of either **Language** or **Extension**, since one is usually enough to define a file-type.  But if both are defined, pyscFilteredViewer will first try to match on **Language**, and then on **Extension**.

### Configuring Keyboard Shortcut(s)

If you want to be able to use one or more of these scripts with a keyboard shortcut, use the **Plugins > PythonScript > Configuration...** dialog to add the script(s) to the **Menu items** list, then **Settings > Shortcut Mapper > Plugin Commands**, filter for **Python**, and edit the keyboard shortcut for the appropriate script(s).

Once you are ready to replace PreviewHTML with `pyscFilteredViewer`, I highly recommend mapping the PreviewHTML shortcut (`Ctrl+H`) to `pyscfvToggleFilterOnSave` (see [**Filter On Save**](#filter-on-save), below).

## One-time Filtering

This will take the active file, filter it as defined in the **Configuration**, and the resulting filtered file will be displayed in your default browser.  With one-time filtering, it will immediately delete the temporary HTML file -- so if you try to hit RELOAD or REFRESH in your browser or viewer, it won't find the file.  To reload the file, you will need to close the old version in your viewer, and re-run the one-time filter from Notepad++.

## Filter On Save

If you want to keep updating the filtered file (usually HTML) every time you change the source, you need to "register" the FilterOnSave action, using the `pyscfvRegisterFilterOnSave` script.  This will register a "hook" such that every time Notepad++ saves a file, it will run the filter.  If the filter hasn't been run on this file yet, it will launch the filtered file in the appropriate viewer.  If the filter had been run on this file before, then **you** will have to move to the viewer (usually, the web browser) and refresh the appropriate page (or find a browser or viewer that can watch for changes in the file, and automatically refresh itself).

Once you are done (or want to be able to edit and save files without having the filter run every time), you can use `pyscfvUnRegisterFilterOnSave` to un-register / un-hook the filter from the file-save event.

As an easier interface (and the one I recommend), you can use the `pyscfvToggleFilterOnSave` script to automatically determine whether it should enable or disable the FilterOnSave.  Using this script to toggle filtering to the temporary file is the most like the PreviewHTML behavior, and it's the script I have associated with PreviewHTML's `Ctrl+H` keyboard shortcut.

As a bonus feature, to help you keep track of whether or not the filter is on, the Status Bar will be edited to show `⇉📺⇉` before the Language name when the live filter is active, and will remove that prefix when the filtering is turned off.

* The manual refresh in the viewer/browser is a known compromise in the switch from PreviewHTML to pyscFilteredViewer: there may be a way to cause your viewer (browser) to reload/refresh the appropriate file, but it wasn't immediately obvious.  As a workaround, you may be able to define your filter to include the `<meta refresh>` tag in the resulting HTML, which might work for a local file to cause refresh as often as you want; I do not guarantee that this workaround work for you.

* If there is enough demand, it would be possible to add other hooks (and accompanying scripts to register or unregister the hooks) I may add another possible hook to register, which might be something like the time-based FilterOnTimer or the buffer-edited

## Future Features

Some day, there may be:

* ability to configure an alternate viewer -- either by specifying a Windows "verb" other than the default, or by giving a path to the program that should be used to view the file

* ability to filter to something other than HTML -- it's almost there... it just defaults the name to .html; if I make the filtered-extension configurable, then everything else should just come out nicely in the wash

Feel free to make [feature suggestions and bug reports](https://github.com/pryrt/pyscFilteredViewer/issues).  I do not guarantee they will make it in, but if I can think of a way to do it (or if you help with the development), there's a good chance I'll incorporate it.
