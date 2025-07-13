################################################################################
#
# klipper
#
################################################################################

KLIPPER_VERSION = 2b8d7addbdcebfd94b37b9678b9e6742b54e6cae
KLIPPER_SITE = https://github.com/loss-and-quick/klipper.git
KLIPPER_SITE_METHOD = git

KLIPPER_LICENSE = GPL-3.0
KLIPPER_LICENSE_FILES = COPYING

KLIPPER_DEPENDENCIES = \
	python3 \
	python-greenlet \
	python-cffi \
	python-jinja2 \
	python-markupsafe \
	python-serial \
	python-can \
	python-setuptools \
	python-msgspec

ifneq ($(BR2_PACKAGE_KLIPPER_CONFIGS),)
KLIPPER_DEPENDENCIES += host-arm-gnu-toolchain host-python3
KLIPPER_MCU_CONFIGS_LIST = $(call qstrip,$(BR2_PACKAGE_KLIPPER_CONFIGS))
endif

define KLIPPER_BUILD_C_HELPER
	$(RM) -rf $(@D)/klippy/chelper/c_helper.so
	$(TARGET_MAKE_ENV)
    cd $(@D)/klippy/chelper; \
    $(TARGET_CC) $(TARGET_CFLAGS) \
		-Wall -g -O2 -shared -fPIC \
        -flto -fwhole-program -fno-use-linker-plugin \
      -o c_helper.so *.c \
      $(TARGET_LDFLAGS)
endef

define KLIPPER_INSTALL_TARGET_CMDS
    mkdir -p $(TARGET_DIR)/opt/klipper
	cp -a $(@D)/klippy $(@D)/docs $(@D)/config $(TARGET_DIR)/opt/klipper/

	$(INSTALL) -m 0644 $(@D)/README.md $(@D)/COPYING  $(TARGET_DIR)/opt/klipper/

    printf "%s-%s\n" \
      "$(KLIPPER_VERSION)" "Buildroot" \
      > $(TARGET_DIR)/opt/klipper/klippy/.version
endef

define KLIPPER_BUILD_MCU_FIRMWARES
	$(if $(KLIPPER_MCU_CONFIGS_LIST),
		printf "%s-%s\n" \
			"$(KLIPPER_VERSION)" "Buildroot" \
			> $(@D)/klippy/.version
		$(foreach config,$(KLIPPER_MCU_CONFIGS_LIST),
			$(call KLIPPER_BUILD_MCU_FIRMWARE,$(config))
		)
	)
endef

define KLIPPER_BUILD_MCU_FIRMWARE
	rm -rf $(@D)/out
	cp $(1) $(@D)/.config
	$(HOST_MAKE_ENV) $(MAKE) -C $(@D) \
		CROSS_PREFIX=$(HOST_DIR)/bin/arm-none-eabi- \
		olddefconfig
	$(HOST_MAKE_ENV) $(MAKE) -C $(@D) \
		CROSS_PREFIX=$(HOST_DIR)/bin/arm-none-eabi-
	mkdir -p $(TARGET_DIR)/opt/klipper/firmware
	cp -f $(@D)/out/klipper.bin $(TARGET_DIR)/opt/klipper/firmware/$(notdir $(basename $(1))).bin
	cp -f $(@D)/out/klipper.elf $(TARGET_DIR)/opt/klipper/firmware/$(notdir $(basename $(1))).elf
endef

KLIPPER_POST_BUILD_HOOKS += KLIPPER_BUILD_C_HELPER

ifneq ($(KLIPPER_MCU_CONFIGS_LIST),)
KLIPPER_POST_BUILD_HOOKS += KLIPPER_BUILD_MCU_FIRMWARES
endif

$(eval $(generic-package))