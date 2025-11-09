@echo off
setlocal EnableDelayedExpansion

:mainmenu
cls
echo ==========================
echo        DUCK RPG
echo ==========================
echo.
echo 1. Start Adventure
echo 2. Quit
echo.
set /p choice=Choose: 
if "%choice%"=="1" goto intro
if "%choice%"=="2" exit
goto mainmenu

:intro
cls
echo In a world overrun by evil ducks...
echo Only YOU can stop the feathery menace.
set /a hero_hp=100
pause
goto battle1

:battle1
call :fight "Angry Duck" 50 8
if "!hero_dead!"=="1" goto gameover
set "frag1=unlock"
goto battle2

:battle2
call :fight "Duck Mage" 100 12
if "!hero_dead!"=="1" goto gameover
set "frag2=the"
goto battle3

:battle3
call :fight "Mother Goose" 420 69
if "!hero_dead!"=="1" goto gameover
set "frag3=goose"
goto victory

:victory
cls
echo You defeated all the evil ducks!
echo The pond is safe again, hero.
set "full=%frag1%%frag2%%frag3%"
set "self=%~f0"
set "hash="
for /f "skip=1 tokens=1" %%H in ('certutil -hashfile "%self%" SHA256') do (
    call set "hash=%%H"
    goto result
)

:result
call result.bat !full! !hash!
exit /b

:gameover
echo You were defeated by the ducks...
echo Try again, brave one.
exit /b
goto mainmenu

:fight

set "enemy_name=%~1"
set /a enemy_hp=%~2
set /a enemy_atk=%~3
set hero_dead=0

:combat
cls
echo ==========================
echo Battle: !enemy_name!
echo ==========================
echo Your HP: !hero_hp!
echo !enemy_name! HP: !enemy_hp!
echo.
echo 1. Attack
echo 2. Heal (+10 HP)
echo 3. Run
set /p act=Action: 

if "!act!"=="1" (
    set /a enemy_hp-=10
    echo You hit !enemy_name! for 10!
) else if "!act!"=="2" (
    set /a hero_hp+=10
    echo You healed 10 HP!
) else if "!act!"=="3" (
    echo You cannot run from ducks! 
) else (
    echo Invalid.
)

if !enemy_hp! LEQ 0 (
    echo.
    echo You defeated !enemy_name!
    goto :eof
)

set /a dmg=%random% %% %enemy_atk% + 5
set /a hero_hp-=dmg
echo.
echo !enemy_name! hits you for !dmg! damage!

if !hero_hp! LEQ 0 (
    set "hero_dead=1"
    endlocal & set "hero_dead=1"
    goto :eof
)

pause
goto combat

:battle0
call :fight "Tiny Duck" 1 1
if "!hero_dead!"=="1" goto gameover
set "frag3=duck"
goto victory
