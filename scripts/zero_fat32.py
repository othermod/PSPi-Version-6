#!/usr/bin/env python3
"""Zero all free clusters in a FAT32 partition inside a disk image."""
import struct
import sys

CHUNK = 64 * 1024 * 1024  # 64 MB write buffer


ZEROS = b"\x00" * CHUNK


def zero_free_clusters(image_path: str, partition_offset: int) -> None:
    with open(image_path, "r+b") as f:
        f.seek(partition_offset)
        bpb = f.read(90)

        # Refuse non-FAT32: the FAT-size field below is FAT32-only; on
        # FAT12/16 it is zero and the computed data region would be wrong,
        # so this would zero live data. Type string is at offset 82 on FAT32
        # (offset 54 on FAT12/16 -- the case this must catch).
        fs_type = bpb[82:90].rstrip(b" ")
        fat_size_16 = struct.unpack_from("<H", bpb, 22)[0]
        if fs_type != b"FAT32" or fat_size_16 != 0:
            sys.exit(f"Not a FAT32 partition at offset {partition_offset} "
                     f"(type={fs_type!r}); refusing to write")

        bytes_per_sector   = struct.unpack_from("<H", bpb, 11)[0]
        sectors_per_cluster = struct.unpack_from("<B", bpb, 13)[0]
        reserved_sectors   = struct.unpack_from("<H", bpb, 14)[0]
        num_fats           = struct.unpack_from("<B", bpb, 16)[0]
        sectors_per_fat    = struct.unpack_from("<I", bpb, 36)[0]

        cluster_size = bytes_per_sector * sectors_per_cluster
        fat_start    = partition_offset + reserved_sectors * bytes_per_sector
        data_start   = fat_start + num_fats * sectors_per_fat * bytes_per_sector

        f.seek(fat_start)
        fat = f.read(sectors_per_fat * bytes_per_sector)
        num_clusters = len(fat) // 4

        # Collect contiguous free-cluster runs for efficient bulk writes
        run_start = None
        runs = []
        for c in range(2, num_clusters):
            entry = struct.unpack_from("<I", fat, c * 4)[0] & 0x0FFFFFFF
            if entry == 0:
                if run_start is None:
                    run_start = c
            else:
                if run_start is not None:
                    runs.append((run_start, c - 1))
                    run_start = None
        if run_start is not None:
            runs.append((run_start, num_clusters - 1))

        total_clusters = sum(e - s + 1 for s, e in runs)
        zeroed = 0

        for (start, end) in runs:
            offset = data_start + (start - 2) * cluster_size
            remaining = (end - start + 1) * cluster_size
            f.seek(offset)
            while remaining > 0:
                block = min(remaining, CHUNK)
                f.write(ZEROS if block == CHUNK else ZEROS[:block])
                remaining -= block
                zeroed += block

        total_mb = total_clusters * cluster_size // (1024 * 1024)
        print(f"  Zeroed {len(runs)} free run(s), "
              f"{total_clusters} clusters, {total_mb} MB")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print(f"Usage: {sys.argv[0]} <image> <partition_offset_bytes>")
        sys.exit(1)
    zero_free_clusters(sys.argv[1], int(sys.argv[2]))
