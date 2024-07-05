# Descent 1/2 For PortMaster
The MS-DOS games by Parallax Software ported with DXX-Rebirth.

## Installation
Unzip to ports folder e.g. `/roms/ports/`. Ready to play with shareware and demo files. To upgrade to full game, purchase on Steam/GOG and then add .hog and .pig files to `descent/data` and `descent2/data`.

Filelist for full versions:  
├── descent/data  
│   ├── missions/    
│   │ └── bonuscontent   
│   └── descent.hog  
│   └── descent.pig  
│   └── chaos.hog (multiplayer, optional)  
│   └── chaos.msn (multiplayer, optional)  
├── descent2/data  
│   ├── missions/    
│   │ └── bonuscontent   
│   └── alien1.pig  
│   └── alien2.pig  
│   └── descent2.ham  
│   └── descent2.hog  
│   └── descent2.s11  
│   └── descent2.s22  
│   └── fire.pig  
│   └── groupa.pig  
│   └── ice.pig  
│   └── water.pig  
│   └── intro-h.mvl (optional)  
│   └── other-h.mvl (optional)  
│   └── robots-h.mvl (optional)  
│   └── d2x-h.mvl (optional)  

Descent I & II: Definitive Edition came with some extra content not available on GOG or Steam. These include Levels of the World (Descent 1), 29 Bonus Levels by Parallax Software (Descent 1), and the Descent 2: Vertigo expansion pack. 
This extra content can be placed in the data/missions folder for both Descent and Descent 2. If done correctly you'll see a new submenu when selecting New Game.

## Configuration
Ini files `d1x.ini` and `d2x.ini` are configurable. The port features keyboard emulation and native SDL joystick controls.

You may rename `Player.plr` and `Player.plx` in the conf folder for a different multiplayer display name. If you do so, please modify the `d1x.ini` or `d2x.ini` file to reflect this change.

Cheats can be found and modified in `cheats.txt`. To turn a cheat on, change the 0 to 1. To turn it off, change 1 to 0.

Add-Ons (.dxa files) such as different soundtracks from various soundcards and game versions, can be found at the project's [GitHub Repo](https://github.com/JeodC/Portmaster-Descent)

## Default Gameplay Controls

| Button | Action |
|--|--| 
|A|Primary Fire|
|B|Deploy Bomb|
|X|Secondary Fire|
|Y|Fire Flare|
|L1|Reverse|
|L2|Cycle Secondary Weapon|
|L3|Not Set|
|R1|Accelerate|
|R2|Scroll Primary Weapon|
|R3|Not Set|
|D-PAD UP|Look Up|
|D-PAD DOWN|Look Down|
|D-PAD LEFT|Turn Left|
|D-PAD RIGHT|Turn Right|
|LEFT ANALOG|Look Around|
|RIGHT ANALOG|Slide Up/Down & Bank Left/Right|
|SELECT|Back / Escape|
|START|Start / Accept / Enter|
|START + LEFT|Activate Cheats|

## Level Select Controls

| Button | Action |
|--|--| 
|B|0|
|Y|1|
|X|2|
|L1|3|
|L2|4|
|R1|5|
|R2|6|
|SELECT+  B|7|
|SELECT + X|8|
|SELECT + Y|9|
|D-PAD Left|Backspace|

## Secret Levels
Level 10 -> -> Secret Level 1  
Level 21 -> -> Secret Level 2  
Level 23 -> -> Secret Level 3  

## Thanks
Cebion  
romadu  
Tekkenfede  
krishenriksen  
Testers and Devs from the PortMaster Discord  
Parallax Software  
[DXX-Rebirth](https://www.dxx-rebirth.com) Team  
