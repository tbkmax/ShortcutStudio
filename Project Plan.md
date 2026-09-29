This is the app that focus on windows OS, that aims to create the shortcut of .exe from `source folder` to a `target folder`.
In python, using pyqt6

for the GUI, it should follow what written in DESIGN.md

## Basic

use SQLite database to store the info

in every part of .exe's name also in database make sure it support Chinese(T/S), Japanese files name

should have GUI

for that GUI, will have: Start New, Edit

which in `source folder` it will have a lot of folder, that we want to go in to every folder and find out the .exe files and let user choose which one, every folder we only need to choose one

in subfolder it might exist multiple .exe files, and need to let user choose which one, and while choosing in GUI it should let user be able to click to choose which one and it should have name and icon that exe use both display in GUI

when that subfolder only have one .exe just do it automatically 

in `target folder` is expect to have shortcut of .exe from `source folder's subfolder, also with the icon .exe have in the subfolder, and shortcut's name should be that sub folder's name

## the workflow of Start New:

let user choose `source folder` and `target folder` (in GUI way of choose)

go though each subfolder in `source folder` (display the process even it is auto)

when that done show in green

if that is multiple .exe files change page to have clear place to let user choose which one (which include .exe and its icons)

after choosing back to that progress pages

(repeat before finish all of subfolder)

## Edit

skip Edit now



