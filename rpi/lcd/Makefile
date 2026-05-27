DTC = dtc
GCC = gcc

KDIR ?= $(dir $(lastword $(MAKEFILE_LIST)))linux

SRCS = pspi-lcd-overlay.dts

OBJS = $(patsubst %.dts,%.dtbo,$(SRCS))

INCLUDE = -I$(KDIR)/include
CPPFLAGS = -nostdinc -x assembler-with-cpp -undef -D__DTS__ $(INCLUDE)
DTCFLAGS = -@ -Hepapr -I dts -O dtb -Wno-unit_address_vs_reg

.PHONY: all clean

all: $(OBJS)

$(KDIR)/include/dt-bindings/.exists:
	@if [ ! -f $(KDIR)/include/dt-bindings/gpio/gpio.h ]; then \
		git clone --depth 1 --filter=blob:none --sparse \
			https://github.com/torvalds/linux.git $(KDIR); \
		cd $(KDIR) && git sparse-checkout init --cone && \
			git sparse-checkout set include/dt-bindings && \
			git checkout; \
	fi
	@mkdir -p $(@D) && touch $@

%.dtbo: %.dts $(KDIR)/include/dt-bindings/.exists
	$(GCC) $(CPPFLAGS) -E $< | $(DTC) $(DTCFLAGS) -o $@ -

clean:
	rm -f $(OBJS)
	rm -rf $(KDIR)
