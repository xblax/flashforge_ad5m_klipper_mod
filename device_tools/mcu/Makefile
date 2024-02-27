CC = arm-buildroot-linux-gnueabihf-gcc
CFLAGS = -Wall -g -O2 -fPIC -march=armv7-a -mfpu=vfpv4 -mfpu=neon
LDFLAGS = 

SRC_FILES = $(wildcard *.c)

TARGET = boot_eboard_mcu

$(TARGET): $(SRC_FILES)
	$(CC) $(CFLAGS) $(LDFLAGS) -o $@ $^

.PHONY: clean

clean:
	rm -f $(TARGET)
