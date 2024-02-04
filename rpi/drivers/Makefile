CC = gcc
CFLAGS = -O3 -lrt

# Define the targets for your programs
PROGRAMS = osd main mouse

# Define all as the first target
all: lib $(PROGRAMS)

# Compile the lib part
lib:
	$(MAKE) -C lib

# Individual program targets
osd:
	$(CC) -o bin/osd osd.c $(CFLAGS) -I./common -L./lib -lbcm_host -lraspidmx -lasound

main:
	$(CC) -o bin/main main.c $(CFLAGS)

mouse:
	$(CC) -o bin/mouse mouse.c $(CFLAGS)

# Clean target for cleaning up
clean:
	rm -f common/*.o
	rm -f lib/*.a
	$(MAKE) -C lib clean
	rm -f bin/$(PROGRAMS)

.PHONY: all lib clean
