@echo off
rem This is an example converter command for pyscFilteredViewer
rem It takes a filename as its command-line argument, and spits out HTML to STDOUT
rem This is just an example, it's not super useful:
rem It will just wrap the text of the input file with HTML tags
echo ^<!DOCTYPE html^>                         2>&1
echo ^<meta charset="UTF-8"^>                  2>&1
echo ^<html^>                                  2>&1
echo ^<h1^>%~1^<^/h1^>                         2>&1
echo ^<xmp^>                                   2>&1
type "%~1"                                     2>&1
echo.                                          2>&1
echo ^<^/xmp^>                                 2>&1
echo ^<^/html^>                                2>&1
rem the 2>&1 redirection makes sure that you see error messages