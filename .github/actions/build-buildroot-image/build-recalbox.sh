#!/bin/bash
set +x

# "Permission denied" in the github workflow means that your script file does not have the "execute" permission set.
# git update-index --chmod=+x .\.github\actions\build-buildroot-image\build-recalbox.sh

mkdir -p completed_images
cd images

# Create mount directory and mount image file
echo "Make mount directory and mount image"
sudo mkdir -p /mnt/image /mnt/squashfs /tmp/upper /tmp/work /tmp/target
sudo mount -o loop,offset=$((512*2048)) $IMAGE_NAME /mnt/image

# Add files to /boot
echo "Add files to /boot"
sudo cp $GITHUB_WORKSPACE/rpi/configs/recalbox/config.txt /mnt/image/config.txt
sudo cp $GITHUB_WORKSPACE/rpi/configs/cm4.txt /mnt/image/cm4.txt
sudo cp $GITHUB_WORKSPACE/rpi/configs/pi0.txt /mnt/image/pi0.txt
sudo cp $GITHUB_WORKSPACE/rpi/configs/pspi.conf /mnt/image/pspi.conf
sudo cp $GITHUB_WORKSPACE/rpi/configs/recalbox/recalbox-user-config.txt /mnt/image/recalbox-user-config.txt
sudo cp $GITHUB_WORKSPACE/rpi/overlays/* /mnt/image/overlays/
sudo mkdir -p /mnt/image/drivers
sudo cp $GITHUB_WORKSPACE/rpi/drivers/bin/* /mnt/image/drivers/

# Mount squashfs
echo "Mount squashfs"
sudo mount --type="squashfs" --options="loop" --source="/mnt/image/boot/recalbox" --target="/mnt/squashfs"
# Mount overlay
echo "Mount overlay"
sudo mount --type="overlay" --options="lowerdir=/mnt/squashfs,upperdir=/tmp/upper,workdir=/tmp/work" --source="overlay" --target="/tmp/target"

# Add custom.sh to recalbox
echo "Add custom.sh to recalbox"
sudo cp $GITHUB_WORKSPACE/rpi/scripts/recalbox/custom.sh /tmp/target/recalbox/share_init/system/custom.sh
sudo chmod +x /tmp/target/recalbox/share_init/system/custom.sh

# Update S12populateshare to copy custom.sh into system at boot
echo "Update S12populateshare to copy custom.sh into system at boot"
sudo sed -i "`wc -l < /tmp/target/etc/init.d/S12populateshare`i\\# copy pspi custom.sh\\" /tmp/target/etc/init.d/S12populateshare
sudo sed -i "`wc -l < /tmp/target/etc/init.d/S12populateshare`i\\cp "/recalbox/share_init/system/custom.sh" "/recalbox/share/system/custom.sh"\\" /tmp/target/etc/init.d/S12populateshare

# Add driver libraries
echo "Add driver libraries"
sudo cp $GITHUB_WORKSPACE/rpi/libraries/recalbox/* /tmp/target/usr/lib/

# repack squashfs
echo "Repack squashfs"
sudo mksquashfs /tmp/target ./filesystem.squashfs -noappend

# Unmount
echo "Unmount overlay"
sudo umount --type="overlay" /tmp/target
echo "Unmount squashfs"
sudo umount --type="squashfs" /mnt/squashfs

# zero out all space in the original image file
echo "zero out all space in the original image file. an error from dd (no space left on device) is expected here"
sudo dd if=/dev/zero of=/mnt/image/boot/recalbox bs=1M status=progress
sleep 5
sudo rm /mnt/image/boot/recalbox
df -h /mnt/image

# Copy squashfs back to image
echo "Copy squashfs back to image"
sudo cp filesystem.squashfs /mnt/image/boot/recalbox

# Unmount
echo "Unmount image"
sudo umount /mnt/image

# Recompress image
echo "Recompress image"
gzip -9 $IMAGE_NAME
echo "Move image to completed_images & rename"
mv $IMAGE_NAME.gz ../completed_images/$PSPI_IMAGE_NAME