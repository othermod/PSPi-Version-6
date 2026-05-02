DTBO_FILES = pspi-audio-cm4-kernel6+.dtbo \
             pspi-audio-cm4-kernel5-.dtbo \
             pspi-audio-zero-kernel6+.dtbo \
             pspi-audio-zero-kernel5-.dtbo

DTS_FILES = $(DTBO_FILES:.dtbo=.dts)

.PHONY: all clean

all: $(DTBO_FILES)

%.dtbo: %.dts
	dtc -I dts -O dtb -o $@ $<

clean:
	rm -f $(DTBO_FILES)
