The Direction of this project is in About.txt
every page design should follow doc/DESIGN.md

#### 1: Auto Manager
- [ ] create a Auto manager that can set any things that planning to done automatically 
- [ ] Add a tab call Auto, which anythings relate to auto should be possible to set in this page
- [ ] This feature is turn off by default

#### 1.auto_check.new_added_game_folder
- [ ] adding auto check all feature, this should use watchdog for it
- [ ] for preventing process the games that still download or big file transferring but issues, use two way to prevent it
- [ ] first: whole new folder size didn't change interval, check_interval should be possible to set 3 to 15 seconds in Auto tab, default is 7 seconds
- [ ] second: File Lock Check, also use python to try to open or change folder name (choose safest way) to check if windows will give PermissionError, which if it didn't than ok
- [ ] so the process for new game folder: detect new game folder coming in -> check with first until pass -> check with second until it pass -> do the check all (open select window on if require user to select)
- [ ] be sure to prevent the error that stuck in the 2 and 3 step for too long which consuming the resources unnessory 
- [ ] This should only works on "new added game folder" 

#### 1.auto_check.game_folder_deleting_by_user_completely
- [ ] This should only works on "a game folder deleting by user completely"
- [ ] user might just transfer a game from A source to another marked B source, which might trigger both add new game and delete a game, also make sure nothing will went wrong

#### 2: Rename
- [ ] decide a better name for this project
- [ ] design a new icon using svg
- [ ] This software is also planning to change to a game launcher, something like Local game database: read About.txt for more information

#### 3: Add CI process for building release

