#!/bin/bash
set +x

# "Permission denied" in the github workflow means that your script file does not have the "execute" permission set.
# git update-index --chmod=+x .\.github\actions\build-buildroot-image\build-lakka.sh

mkdir -p completed_images
cd images

# Create mount directory and mount image file
echo "Make mount directory and mount image"
devicePath=$(sudo losetup -f)
sudo losetup -Pf $IMAGE_NAME
sudo losetup -l
sudo mkdir -p /mnt/image /mnt/squashfs /tmp/upper /tmp/work /tmp/target
sudo mount -o loop,offset=$((512*8192)) $devicePath /mnt/image

# Add files to /boot
echo "Add files to /boot"
sudo cp $GITHUB_WORKSPACE/rpi/configs/lakka/config.txt /mnt/image/config.txt
sudo cp $GITHUB_WORKSPACE/rpi/configs/cm4.txt /mnt/image/cm4.txt
sudo cp $GITHUB_WORKSPACE/rpi/configs/pi0.txt /mnt/image/pi0.txt
sudo cp $GITHUB_WORKSPACE/rpi/configs/lakka/distroconfig.txt /mnt/image/distroconfig.txt
sudo cp $GITHUB_WORKSPACE/rpi/overlays/* /mnt/image/overlays/
sudo mkdir -p /mnt/image/drivers
sudo cp $GITHUB_WORKSPACE/rpi/drivers/bin/* /mnt/image/drivers/

# Mount squashfs
echo "Mount squashfs"
sudo mount --type="squashfs" --options="loop" --source="/mnt/image/SYSTEM" --target="/mnt/squashfs"
# Mount overlay
echo "Mount overlay"
sudo mount --type="overlay" --options="lowerdir=/mnt/squashfs,upperdir=/tmp/upper,workdir=/tmp/work" --source="overlay" --target="/tmp/target"

# Add autostart.sh
echo "Add autostart.sh"
sudo cp $GITHUB_WORKSPACE/rpi/scripts/lakka/autostart.sh /tmp/target/usr/config/autostart.sh
sudo chmod +x /tmp/target/usr/config/autostart.sh

# Add joypad autoconfig
echo "Add joypad autoconfig"
sudo cp $GITHUB_WORKSPACE/rpi/configs/lakka/PSPi-Controller.cfg /tmp/target/etc/retroarch-joypad-autoconfig/udev/PSPi-Controller.cfg

# Repack squashfs
echo "Repack squashfs"
sudo mksquashfs /tmp/target ./filesystem.squashfs -noappend

# Unmount
echo "Unmount overlay"
sudo umount --type="overlay" /tmp/target
echo "Unmount squashfs"
sudo umount --type="squashfs" /mnt/squashfs

# zero out all space in the original image file
echo "zero out all space in the original image file. an error from dd (no space left on device) is expected here"
sudo dd if=/dev/zero of=/mnt/image/SYSTEM bs=1M status=progress
sleep 5
sudo rm /mnt/image/SYSTEM
df -h /mnt/image

# Copy squashfs back to image
echo "Copy squashfs back to image"
sudo cp filesystem.squashfs /mnt/image/SYSTEM

# unmount
echo "Unmount image"
sudo umount /mnt/image
sudo losetup -d $devicePath

# Recompress image
echo "Recompress image"
gzip -9 $IMAGE_NAME

# Move image to completed_images and rename
echo "Move image to completed_images and rename"
mv $IMAGE_NAME.gz ../completed_images/$PSPI_IMAGE_NAME