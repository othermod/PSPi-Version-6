.PHONY: 32 64 clean

32:
	@mkdir -p 32
	arm-linux-gnueabi-gcc -o 32/wifi_monitor wifi_monitor.c -O3 -lrt -static

64:
	@mkdir -p 64
	aarch64-linux-gnu-gcc -o 64/wifi_monitor wifi_monitor.c -O3 -lrt -static

clean:
	rm -rf 32 64
