#!/bin/bash
#
# SPDX-License-Identifier: MIT
#

export XDG_DATA_HOME=${XDG_DATA_HOME:-$HOME/.local/share}

if [ -d "/opt/system/Tools/PortMaster/" ]; then
  controlfolder="/opt/system/Tools/PortMaster"
elif [ -d "/opt/tools/PortMaster/" ]; then
  controlfolder="/opt/tools/PortMaster"
elif [ -d "$XDG_DATA_HOME/PortMaster/" ]; then
  controlfolder="$XDG_DATA_HOME/PortMaster"
elif [ -d "/userdata/roms/ports/PortMaster" ]; then
  controlfolder="/userdata/roms/ports/PortMaster"
else
  controlfolder="/roms/ports/PortMaster"
fi

source $controlfolder/control.txt

get_controls

## TODO: Change to PortMaster/tty when Johnnyonflame merges the changes in,
CUR_TTY=/dev/tty0

cd "$controlfolder"

export TERM=linux
$ESUDO chmod 666 $CUR_TTY
printf "\033c" > $CUR_TTY

echo "Starting PortMaster." > $CUR_TTY

$ESUDO chmod -R +x .

if [[ -e "/storage/.config/.OS_ARCH" ]] || [ "${OS_NAME}" == "JELOS" ] || [ "${OS_NAME}" == "UnofficialOS" ]; then
  toolsfolderloc="/storage/roms/ports"
elif [[ -e "$(which batocera-version)" ]]; then
    toolsfolderloc="/userdata/roms/ports"
else
  isitthera=$(grep "title=" "/usr/share/plymouth/themes/text.plymouth")
  if [[ $isitthera == *"TheRA"* ]]; then
    if [ -d "/opt/tools/PortMaster/" ]; then
      toolsfolderloc="/opt/tools"
    else
      toolsfolderloc="/roms/ports"
    fi
  else
    if [ -d "/opt/system/Tools/PortMaster/" ]; then
      toolsfolderloc="/opt/system/Tools"
    else
      toolsfolderloc="/roms/ports"
    fi
  fi
fi

## Autoinstallation Code
# This will automatically install zips found within the PortMaster/autoinstall directory using harbourmaster
AUTOINSTALL=$(find "${toolsfolderloc}/PortMaster/autoinstall" -type f \( -name "*.zip" -o -name "*.squashfs" \))
if [ -n "$AUTOINSTALL" ]; then
  source "PortMasterDialog.txt"

  GW=$(PortMasterIPCheck)
  PortMasterDialogInit "no-check"

  PortMasterDialog "messages_begin"

  PortMasterDialog "message" "Auto-installation"

  # Install the latest runtimes.zip
  if [ -f "${toolsfolderloc}/PortMaster/autoinstall/runtimes.zip" ]; then
    PortMasterDialog "message" "- Installing runtimes.zip, this could take a minute or two."
    $ESUDO unzip -o "${toolsfolderloc}/PortMaster/autoinstall/runtimes.zip" -d "${toolsfolderloc}/PortMaster/libs"
    $ESUDO rm -f "${toolsfolderloc}/PortMaster/autoinstall/runtimes.zip"
    PortMasterDialog "message" "- SUCCESS: runtimes.zip"
  fi

  for file_name in "${toolsfolderloc}/PortMaster/autoinstall"/*.squashfs
  do
    $ESUDO mv -f "$file_name" "${toolsfolderloc}/PortMaster/libs"
    PortMasterDialog "message" "- SUCCESS: $(basename $file_name)"
  done

  for file_name in "${toolsfolderloc}/PortMaster/autoinstall"/*.zip
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

  if [ -f "${toolsfolderloc}/PortMaster/autoinstall/PortMaster.zip" ]; then
    file_name="${toolsfolderloc}/PortMaster/autoinstall/PortMaster.zip"

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
    exit 0
  else
    PortMasterDialogMessageBox "Finished running autoinstall."
    PortMasterDialogExit
  fi
fi

PORTMASTER_CMDS=${PORTMASTER_CMDS:---debug}

export PYSDL2_DLL_PATH="/usr/lib"
$ESUDO rm -f "${controlfolder}/.pugwash-reboot"
while true; do
  $ESUDO ./pugwash $PORTMASTER_CMDS 2>&1 | $ESUDO tee -a ./log.txt

  if [ ! -f "${controlfolder}/.pugwash-reboot" ]; then
    break;
  fi

  $ESUDO rm -f "${controlfolder}/.pugwash-reboot"
done

unset LD_LIBRARY_PATH
unset SDL_GAMECONTROLLERCONFIG
$ESUDO systemctl restart oga_events &
printf "\033c" > $CUR_TTY

if [ -f "${controlfolder}/.emustation-refresh" ]; then
  $ESUDO rm -f "${controlfolder}/.emustation-refresh"
  $ESUDO systemctl restart emustation
elif [ -f "${controlfolder}/.emulationstation-refresh" ]; then
  $ESUDO rm -f "${controlfolder}/.emulationstation-refresh"
  $ESUDO systemctl restart emulationstation
elif [ -f "${controlfolder}/.batocera-es-refresh" ]; then
  $ESUDO rm -f "${controlfolder}/.batocera-es-refresh"
  batocera-es-swissknife --restart
fi
