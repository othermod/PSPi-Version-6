OBJS=gamepad.o
BIN=gamepad

CFLAGS+=-Wall -O3 -g -I./common
LDFLAGS+=-L/opt/vc/lib/ -lbcm_host -lm -L./lib -lraspidmx -lasound -lrt

INCLUDES+=-I/opt/vc/include/ -I/opt/vc/include/interface/vcos/pthreads -I/opt/vc/include/interface/vmcs_host/linux

all: $(BIN)

%.o: %.c
	@rm -f $@
	$(CC) $(CFLAGS) $(INCLUDES) -g -c $< -o $@ -Wno-deprecated-declarations

$(BIN): $(OBJS)
	$(CC) -o $@ -Wl,--whole-archive $(OBJS) $(LDFLAGS) -Wl,--no-whole-archive -rdynamic

install: $(BIN)
	cp $(BIN) /usr/local/bin/

clean:
	@rm -f $(OBJS)
	@rm -f $(BIN)
