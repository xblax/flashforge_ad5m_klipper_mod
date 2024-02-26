CC = arm-buildroot-linux-gnueabihf-gcc
CFLAGS = -Wall -g -O3 -shared -fPIC -flto -fwhole-program -fno-use-linker-plugin
LDFLAGS = -shared

SRC_FILES = $(wildcard *.c)

TARGET = c_helper.so

$(TARGET): $(SRC_FILES)
	$(CC) $(CFLAGS) $(LDFLAGS) -o $@ $^

.PHONY: clean

clean:
	rm -f $(TARGET)
