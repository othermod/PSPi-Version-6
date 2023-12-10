PREFIX=/usr/local
BINDIR=$(PREFIX)/bin

OBJS=osd.o gamepad.o main.o mouse.o
BIN=osd gamepad main mouse

CFLAGS+=-Wall -O3 -g -I./common
LDFLAGS+=-L/opt/vc/lib/ -lbcm_host -lm -L./lib -lraspidmx -lasound -lrt

INCLUDES+=-I/opt/vc/include/ -I/opt/vc/include/interface/vcos/pthreads -I/opt/vc/include/interface/vmcs_host/linux

all: $(BIN)

%.o: %.c
	$(CC) $(CFLAGS) $(INCLUDES) -c $< -o $@

osd: osd.o
	$(CC) -o $@ osd.o $(LDFLAGS)

gamepad: gamepad.o
	$(CC) -o $@ gamepad.o $(LDFLAGS)

main: main.o
	$(CC) -o $@ main.o $(LDFLAGS)

mouse: mouse.o
	$(CC) -o $@ mouse.o $(LDFLAGS)

install: $(BIN)
	@echo "Installing binaries to $(BINDIR)"
	@mkdir -p $(BINDIR)
	@cp $(BIN) $(BINDIR)
	@echo "Installation complete."

uninstall:
	@echo "Uninstalling binaries from $(BINDIR)"
	@cd $(BINDIR) && rm -fv $(BIN)
	@echo "Uninstallation complete."

clean:
	rm -f $(OBJS) $(BIN)
