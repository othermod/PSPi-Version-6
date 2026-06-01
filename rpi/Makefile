.PHONY: 32 64 clean

BUILDS := battery firmware gamepad osd rtc wifi
DTBO   := audio lcd pcie

32:
	@for dir in $(BUILDS); do $(MAKE) -C $$dir 32 || exit 1; done
	@for dir in $(DTBO); do $(MAKE) -C $$dir || exit 1; done

64:
	@for dir in $(BUILDS); do $(MAKE) -C $$dir 64 || exit 1; done
	@for dir in $(DTBO); do $(MAKE) -C $$dir || exit 1; done

clean:
	@for dir in $(BUILDS); do $(MAKE) -C $$dir clean || exit 1; done
	@for dir in $(DTBO); do $(MAKE) -C $$dir clean || exit 1; done