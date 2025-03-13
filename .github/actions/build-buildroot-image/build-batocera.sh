#!/bin/bash
set +x

# "Permission denied" in the github workflow means that your script file does not have the "execute" permission set.
# git update-index --chmod=+x .\.github\actions\build-buildroot-image\build-batocera.sh

mkdir -p completed_images
cd images

# Create mount directory and mount image file
echo "Make mount directory and mount image"
sudo mkdir -p /mnt/image /tmp/squashfs /tmp/upper /tmp/work /tmp/target
sudo mount -o loop,offset=$((512*2048)) $IMAGE_NAME /mnt/image

# Add files to /boot
echo "Add files to /boot"
sudo cp $GITHUB_WORKSPACE/rpi/configs/batocera/config.txt /mnt/image/config.txt
sudo cp $GITHUB_WORKSPACE/rpi/configs/cm4.txt /mnt/image/cm4.txt
sudo cp $GITHUB_WORKSPACE/rpi/configs/pi0.txt /mnt/image/pi0.txt
sudo cp $GITHUB_WORKSPACE/rpi/configs/pspi.conf /mnt/image/pspi.conf
sudo cp $GITHUB_WORKSPACE/rpi/overlays/* /mnt/image/overlays/
sudo mkdir -p /mnt/image/drivers
sudo cp $GITHUB_WORKSPACE/rpi/drivers/bin/* /mnt/image/drivers/

# Mount squashfs
echo "Mount squashfs"
sudo mount --type="squashfs" --options="loop" --source="/mnt/image/boot/batocera" --target="/tmp/squashfs"
# Mount overlay
echo "Mount overlay"
sudo mount --type="overlay" --options="lowerdir=/tmp/squashfs,upperdir=/tmp/upper,workdir=/tmp/work" --source="overlay" --target="/tmp/target"

# Get batocera version
echo "Get batocera version"
BATOCERA_VERSION=$(cat /tmp/target/usr/share/batocera/batocera.version | awk '{print $1}')

if [ "$BATOCERA_VERSION" -lt 40 ]; then
    echo "Batocera version is less than 40"
    sudo cp $GITHUB_WORKSPACE/rpi/configs/batocera/config_39.txt /mnt/image/config.txt
fi

# Add custom.sh
echo "Add custom.sh"
sudo cp $GITHUB_WORKSPACE/rpi/scripts/batocera/custom.sh /tmp/target/usr/share/batocera/datainit/system/custom.sh
sudo chmod +x /tmp/target/usr/share/batocera/datainit/system/custom.sh

# Update S12populateshare to copy custom.sh into system at boot
echo "Update S12populateshare to copy custom.sh into system at boot"
sudo sed -i '/bios\/ps2/i\            system\/custom.sh \\' /tmp/target/etc/init.d/S12populateshare

# Add driver libraries
echo "Add driver libraries"
sudo cp $GITHUB_WORKSPACE/rpi/libraries/batocera/* /tmp/target/usr/lib/

# Add Multimedia keys for volume control
# echo "Add Multimedia keys for volume control"

# sudo cp $GITHUB_WORKSPACE/rpi/configs/batocera/multimedia_keys.conf /tmp/target/usr/share/batocera/datainit/system/configs/multimedia_keys.conf
sudo cp $GITHUB_WORKSPACE/rpi/configs/batocera/es_last_input.cfg /tmp/target/usr/share/batocera/datainit/system/configs/emulationstation/es_last_input.cfg

# Update S12populateshare to copy files into system at boot
echo "Update S12populateshare to copy files into system at boot"
# sudo sed -i '/bios\/ps2/i\            system\/configs\/multimedia_keys.conf \\' /tmp/target/etc/init.d/S12populateshare
sudo sed -i '/bios\/ps2/i\            system\/.local \\' /tmp/target/etc/init.d/S12populateshare
sudo sed -i '/bios\/ps2/i\            system\/configs\/emulationstation\es_last_input.cfg \\' /tmp/target/etc/init.d/S12populateshare

# Add PortMaster
echo "Add PortMaster"
sudo mkdir -p /tmp/target/usr/share/batocera/datainit/system/.local/share/PortMaster
sudo cp -r $GITHUB_WORKSPACE/rpi/configs/batocera/portmaster/PortMaster/* /tmp/target/usr/share/batocera/datainit/system/.local/share/PortMaster/
sudo cp $GITHUB_WORKSPACE/rpi/configs/batocera/portmaster/PortMaster.sh /tmp/target/usr/share/batocera/datainit/roms/ports/PortMaster.sh

# repack squashfs
echo "Repack squashfs"
sudo mksquashfs /tmp/target ./filesystem.squashfs -noappend -comp zstd

# Unmount
echo "Unmount overlay"
sudo umount --type="overlay" /tmp/target
echo "Unmount squashfs"
sudo umount --type="squashfs" /tmp/squashfs

# zero out all space in the original image file
echo "zero out all space in the original image file. an error from dd (no space left on device) is expected here"
sudo dd if=/dev/zero of=/mnt/image/boot/batocera bs=1M status=progress
sleep 5
sudo rm /mnt/image/boot/batocera
df -h /mnt/image

# Copy squashfs back to image
echo "Copy squashfs back to image"
sudo cp filesystem.squashfs /mnt/image/boot/batocera

# unmount
echo "Unmount image"
sudo umount /mnt/image

# Compress image
echo "Compress image"
gzip -9 $IMAGE_NAME
echo "Move image to completed_images & rename"
mv $IMAGE_NAME.gz ../completed_images/$PSPI_IMAGE_NAME

# Split image using 7zip if over 2GB
FILE_SIZE=$(stat -c%s "../completed_images/$PSPI_IMAGE_NAME")
if [ $FILE_SIZE -gt $((2000*1024*1024)) ]; then
    echo "Image is larger than 2GB. Compressing with 7zip..."
    cd ../completed_images
    7z a "$PSPI_IMAGE_NAME.7z" "$PSPI_IMAGE_NAME" -v1500M
    rm "$PSPI_IMAGE_NAME"
fi

# output images in folder
ls -lh ../completed_images