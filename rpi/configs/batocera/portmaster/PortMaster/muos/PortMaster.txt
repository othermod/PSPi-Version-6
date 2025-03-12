#!/bin/bash
#
# SPDX-License-Identifier: MIT
#

controlfolder="/mnt/mmc/MUOS/PortMaster"

if [ ! -z "$(df | grep '/mnt/sdcard')" ]; then
  directory="mnt/sdcard"
else
  directory="mnt/mmc"
fi

OLD_PATH="$PATH"
export PATH="/opt/python/bin:$PATH"
export LD_LIBRARY_PATH="/opt/python/lib:$LD_LIBRARY_PATH"
ESUDO=""
ESUDOKILL="-1" # for 351Elec and EmuELEC use "-1" (numeric one) or "-k" 
export SDL_GAMECONTROLLERCONFIG_FILE="/usr/lib/gamecontrollerdb.txt"
# export SDL_GAMECONTROLLERCONFIG=$(grep "Deeplay" "/usr/lib/gamecontrollerdb.txt")

source "$controlfolder/device_info.txt"
[ -f "${controlfolder}/mod_${CFW_NAME}.txt" ] && source "${controlfolder}/mod_${CFW_NAME}.txt"

## TODO: Change to PortMaster/tty when Johnnyonflame merges the changes in,
CUR_TTY=/dev/tty0

cd "$controlfolder"

exec > >(tee "$controlfolder/log.txt") 2>&1

source "$controlfolder/utils/pmsplash.txt"

## Autoinstallation Code
# This will automatically install zips found within the PortMaster/autoinstall directory using harbourmaster
AUTOINSTALL=$(find "$controlfolder/autoinstall" -type f \( -name "*.zip" -o -name "*.squashfs" \))
if [ -n "$AUTOINSTALL" ]; then
  source "$controlfolder/PortMasterDialog.txt"

  GW=$(PortMasterIPCheck)
  PortMasterDialogInit "no-check"

  PortMasterDialog "messages_begin"

  PortMasterDialog "message" "Auto-installation"

  # Install the latest runtimes.zip
  if [ -f "$controlfolder/autoinstall/runtimes.zip" ]; then
    PortMasterDialog "message" "- Installing runtimes.zip, this could take a minute or two."
    $ESUDO unzip -o "$controlfolder/autoinstall/runtimes.zip" -d "$controlfolder/libs"
    $ESUDO rm -f "$controlfolder/autoinstall/runtimes.zip"
    PortMasterDialog "message" "- SUCCESS: runtimes.zip"
  fi

  for file_name in "$controlfolder/autoinstall"/*.squashfs
  do
    if [ ! -f "$file_name" ]; then
      continue
    fi

    $ESUDO mv -f "$file_name" "$controlfolder/libs"
    PortMasterDialog "message" "- SUCCESS: $(basename $file_name)"
  done

  for file_name in "$controlfolder/autoinstall"/*.zip
  do
    if [ ! -f "$file_name" ]; then
      continue
    fi

    if [[ "$(basename $file_name)" == "PortMaster.zip" ]]; then
      continue
    fi

    if [[ $(PortMasterDialogResult "install" "$file_name") == "OKAY" ]]; then
      $ESUDO rm -f "$file_name"
      PortMasterDialog "message" "- SUCCESS: $(basename $file_name)"
    else
      PortMasterDialog "message" "- FAILURE: $(basename $file_name)"
    fi

    touch "$controlfolder/.muos-refresh"
  done

  if [ -f "$controlfolder/autoinstall/PortMaster.zip" ]; then
    if [ ! -f "$file_name" ]; then
      continue
    fi

    file_name="$controlfolder/autoinstall/PortMaster.zip"

    if [[ $(PortMasterDialogResult "install" "$file_name") == "OKAY" ]]; then
      $ESUDO rm -f "$file_name"
      PortMasterDialog "message" "- SUCCESS: $(basename $file_name)"
    else
      PortMasterDialog "message" "- FAILURE: $(basename $file_name)"
    fi
  fi

  PortMasterDialog "messages_end"
  if [ -z "$GW" ]; then
    PortMasterDialogMessageBox "Finished running autoinstall.\n\nNo internet connection present so exiting."
    PortMasterDialogExit

    rm -f "${controlfolder}/.muos-refresh"
    # HULK SMASH
    ${controlfolder}/muos/image_smash.txt

    exit 0
  else
    PortMasterDialogMessageBox "Finished running autoinstall."
    PortMasterDialogExit
  fi
fi


export TERM=linux
# $ESUDO chmod 666 $CUR_TTY
# printf "\033c" > $CUR_TTY

# # Do it twice, it's just as nice!
# cat /dev/zero > /dev/fb0 2>/dev/null
# cat /dev/zero > /dev/fb0 2>/dev/null

echo "Starting PortMaster." > $CUR_TTY

$ESUDO chmod -R +x .

export PYSDL2_DLL_PATH="/usr/lib"
$ESUDO rm -f "${controlfolder}/.pugwash-reboot"
while true; do
  $ESUDO ./pugwash

  # Do it twice, it's just as nice!
  cat /dev/zero > /dev/fb0 2>/dev/null
  cat /dev/zero > /dev/fb0 2>/dev/null
  if [ ! -f "${controlfolder}/.pugwash-reboot" ]; then
    break;
  fi

  $ESUDO rm -f "${controlfolder}/.pugwash-reboot"
done

unset LD_LIBRARY_PATH
unset SDL_GAMECONTROLLERCONFIG
PATH="$OLD_PATH"

if [ -f "${controlfolder}/.muos-refresh" ]; then
  rm -f "${controlfolder}/.muos-refresh"
  # HULK SMASH
  ${controlfolder}/muos/image_smash.txt
fi
