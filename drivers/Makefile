PREFIX=/usr/local
BINDIR=$(PREFIX)/bin

OBJS=osd.o gamepad.o main.o mouse.o
BIN=osd gamepad main mouse

CFLAGS+=-Wall -O3 -g -I./common
LDFLAGS+=-L/opt/vc/lib/ -lbcm_host -lm -L./lib -lraspidmx -lasound -lrt

INCLUDES+=-I/opt/vc/include/ -I/opt/vc/include/interface/vcos/pthreads -I/opt/vc/include/interface/vmcs_host/linux

all: $(BIN)

%.o: %.c
	$(CC) $(CFLAGS) $(INCLUDES) -c $< -o $@ -Wno-deprecated-declarations

osd: osd.o
	$(CC) -o $@ -Wl,--whole-archive osd.o $(LDFLAGS) -Wl,--no-whole-archive -rdynamic

gamepad: gamepad.o
	$(CC) -o $@ gamepad.o $(LDFLAGS)

main: main.o
	$(CC) -o $@ main.o $(LDFLAGS)

mouse: mouse.o
	$(CC) -o $@ mouse.o $(LDFLAGS)

install: $(BIN)
	@if [ -w $(BINDIR) ]; then \
	    cp -v $(BIN) $(BINDIR)/; \
	else \
	    echo "Error: Permission denied when writing to $(BINDIR)."; \
	    echo "Please run 'sudo make install' to install with administrative privileges."; \
	    exit 1; \
	fi

uninstall:
	@cd $(BINDIR) && rm -fv $(BIN)

.PHONY: install-services
install-services:
	@echo "Stopping existing services (if running)..."
	-sudo systemctl stop gamepad.service
	-sudo systemctl stop main.service
	-sudo systemctl stop mouse.service
	-sudo systemctl stop osd.service

	@echo "Building and installing binaries..."
	$(MAKE)
	sudo $(MAKE) install

	@echo "Installing service files..."
	SERVICE_DIR=/services
	sudo cp services/gamepad.service /etc/systemd/system/
	sudo cp services/main.service /etc/systemd/system/
	sudo cp services/mouse.service /etc/systemd/system/
	sudo cp services/osd.service /etc/systemd/system/

	@echo "Reloading systemd daemon..."
	sudo systemctl daemon-reload

	@echo "Enabling and starting main and osd services..."
	sudo systemctl enable main.service
	sudo systemctl start main.service
	sudo systemctl enable osd.service
	sudo systemctl start osd.service

	@read -p "Enable and start the mouse service? [y/N]: " enable_mouse && \
	[ "$$enable_mouse" = "y" ] && sudo systemctl enable mouse.service && sudo systemctl start mouse.service || echo "Skipping mouse service"

	@read -p "Enable and start the gamepad service? [y/N]: " enable_gamepad && \
	[ "$$enable_gamepad" = "y" ] && sudo systemctl enable gamepad.service && sudo systemctl start gamepad.service || echo "Skipping gamepad service"

	@echo "Services setup complete."

clean:
	rm -f $(OBJS) $(BIN)
