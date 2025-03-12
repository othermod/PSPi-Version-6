#!/bin/sh
#
# SPDX-License-Identifier: MIT
#

controlfolder="/mnt/SDCARD/Apps/PortMaster/PortMaster"

source /mnt/SDCARD/System/etc/ex_config

ESUDO=""
ESUDOKILL="-1" # for 351Elec and EmuELEC use "-1" (numeric one) or "-k" 
export SDL_GAMECONTROLLERCONFIG_FILE="/$controlfolder/gamecontrollerdb.txt"
# export SDL_GAMECONTROLLERCONFIG=$(grep "Deeplay" "/usr/lib/gamecontrollerdb.txt")

## TODO: Change to PortMaster/tty when Johnnyonflame merges the changes in,
CUR_TTY=/dev/tty0

source $controlfolder/control.txt
[ -f "${controlfolder}/mod_${CFW_NAME}.txt" ] && source "${controlfolder}/mod_${CFW_NAME}.txt"

cd "$controlfolder"

exec > >(tee "$controlfolder/log.txt") 2>&1

export TERM=linux
chmod 666 $CUR_TTY
printf "\033c" > $CUR_TTY

source "$controlfolder/utils/pmsplash.txt"

"$controlfolder/trimui/update.txt"

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
    $ESUDO mv -f "$file_name" "$controlfolder/libs"
    PortMasterDialog "message" "- SUCCESS: $(basename $file_name)"
  done

  for file_name in "$controlfolder/autoinstall"/*.zip
  do
    if [[ "$(basename $file_name)" == "PortMaster.zip" ]]; then
      continue
    fi

    if [[ $(PortMasterDialogResult "install" "$file_name") == "OKAY" ]]; then
      $ESUDO rm -f "$file_name"
      PortMasterDialog "message" "- SUCCESS: $(basename $file_name)"
    else
      PortMasterDialog "message" "- FAILURE: $(basename $file_name)"
    fi
  done

  if [ -f "$controlfolder/autoinstall/PortMaster.zip" ]; then
    file_name="$controlfolder/autoinstall/PortMaster.zip"

    if [[ $(PortMasterDialogResult "install" "$file_name") == "OKAY" ]]; then
      $ESUDO rm -f "$file_name"
      PortMasterDialog "message" "- SUCCESS: $(basename $file_name)"
    else
      PortMasterDialog "message" "- FAILURE: $(basename $file_name)"
    fi
  fi

  touch "$controlfolder/.trimui-refresh"

  PortMasterDialog "messages_end"
  if [ -z "$GW" ]; then
    PortMasterDialogMessageBox "Finished running autoinstall.\n\nNo internet connection present so exiting."
    PortMasterDialogExit
    exit 0
  else
    PortMasterDialogMessageBox "Finished running autoinstall."
    PortMasterDialogExit
  fi
fi

export PYSDL2_DLL_PATH="/usr/trimui/lib"

echo "Starting PortMaster." > $CUR_TTY

chmod -R +x .

rm -f "$controlfolder/.pugwash-reboot"
printf "\033c" > $CUR_TTY

while true; do
  ./pugwash --debug

  if [ ! -f "$controlfolder/.pugwash-reboot" ]; then
    break;
  fi

  rm -f "$controlfolder/.pugwash-reboot"
done

if [ -f "$controlfolder/.trimui-refresh" ]; then
  rm -f "$controlfolder/.trimui-refresh"
  # HULK SMASH

  "$controlfolder"/trimui/image_smash.txt
fi

unset LD_LIBRARY_PATH
unset SDL_GAMECONTROLLERCONFIG
