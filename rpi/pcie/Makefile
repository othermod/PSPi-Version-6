DTBO_FILES = disable-pcie.dtbo

DTS_FILES = $(DTBO_FILES:.dtbo=.dts)

.PHONY: all clean

all: $(DTBO_FILES)

%.dtbo: %.dts
	dtc -I dts -O dtb -o $@ $<

clean:
	rm -f $(DTBO_FILES)
