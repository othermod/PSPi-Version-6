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

# Macros for different OS service setups
define LAKKA_SETUP
    echo "Lakka OS detected. Performing Lakka-specific service setup...";
    # Lakka-specific commands here
endef

define BATOCERA_SETUP
    echo "Batocera OS detected. Performing Batocera-specific service setup...";
    # Batocera-specific commands here
endef

define SYSTEMD_SETUP
    echo "Systemd detected. Proceeding with standard service installation...";
    sudo cp services/gamepad.service /etc/systemd/system/;
    sudo cp services/main.service /etc/systemd/system/;
    sudo cp services/mouse.service /etc/systemd/system/;
    sudo cp services/osd.service /etc/systemd/system/;
    sudo systemctl daemon-reload;
    sudo systemctl enable main.service;
    sudo systemctl start main.service;
    sudo systemctl enable osd.service;
    sudo systemctl start osd.service;
    read -p "Enable and start the mouse service? [y/N]: " enable_mouse && \
    [ "$$enable_mouse" = "y" ] && sudo systemctl enable mouse.service && sudo systemctl start mouse.service || echo "Skipping mouse service";
    read -p "Enable and start the gamepad service? [y/N]: " enable_gamepad && \
    [ "$$enable_gamepad" = "y" ] && sudo systemctl enable gamepad.service && sudo systemctl start gamepad.service || echo "Skipping gamepad service";
    echo "Services setup complete.";
endef

define UNKNOWN_SETUP
    echo "Unknown or unsupported OS. Manual service setup may be required.";
endef

# Target to install services
.PHONY: install-services
install-services:
    @echo "Detecting operating system..."
    @OS=$$(grep '^ID=' /etc/os-release | cut -d= -f2); \
    case "$$OS" in \
        lakka) \
            $(LAKKA_SETUP) \
            ;; \
        batocera) \
            $(BATOCERA_SETUP) \
            ;; \
        *) \
            if command -v systemctl >/dev/null 2>&1; then \
                $(SYSTEMD_SETUP) \
            else \
                $(UNKNOWN_SETUP) \
            fi \
            ;; \
    esac

clean:
    rm -f $(OBJS) $(BIN)
