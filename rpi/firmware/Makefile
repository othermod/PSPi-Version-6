CC       = gcc
CFLAGS   = -Wall -Wextra -Wshadow -O2
TARGET   = update_firmware
SRC      = update_firmware.c
BINDIR   = bin

all: cross

cross: $(BINDIR)/$(TARGET)-armhf $(BINDIR)/$(TARGET)-arm64

$(BINDIR)/$(TARGET)-armhf: $(SRC) | $(BINDIR)
	arm-linux-gnueabihf-gcc $(CFLAGS) -static -o $@ $<

$(BINDIR)/$(TARGET)-arm64: $(SRC) | $(BINDIR)
	aarch64-linux-gnu-gcc $(CFLAGS) -static -o $@ $<

$(BINDIR):
	mkdir -p $@

native: $(BINDIR)/$(TARGET)

$(BINDIR)/$(TARGET): $(SRC) | $(BINDIR)
	$(CC) $(CFLAGS) -o $@ $<

clean:
	rm -rf $(BINDIR)

.PHONY: all native cross clean
