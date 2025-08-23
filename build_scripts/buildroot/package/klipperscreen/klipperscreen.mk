################################################################################
#
# klipperscreen
#
################################################################################

KLIPPERSCREEN_VERSION = 6b6f63b6639e5b85a2b3f4b0b0cd7677ac9cda3d
KLIPPERSCREEN_SITE = https://github.com/KlipperScreen/KlipperScreen.git
KLIPPERSCREEN_SITE_METHOD = git
KLIPPERSCREEN_LICENSE = AGPL-3.0-only
KLIPPERSCREEN_LICENSE_FILES = LICENSE

KLIPPERSCREEN_DEPENDENCIES = \
	libevdev \
	python-jinja2 \
	python-requests \
	python-mpv \
	python-gobject \
	python-pycairo \
	python-websocket-client \
	python-psutil

ifeq ($(BR2_PACKAGE_PYTHON_SDBUS_NETWORKMANAGER),y)
KLIPPERSCREEN_DEPENDENCIES += python-sdbus-networkmanager
else
KLIPPERSCREEN_DEPENDENCIES += iwd dbus
endif

define KLIPPERSCREEN_INSTALL_TARGET_CMDS
	mkdir -p $(TARGET_DIR)/opt/klipperscreen
	cp -a $(@D)/* $(TARGET_DIR)/opt/klipperscreen/
	printf "%s-%s-%s\n" \
      "$(KLIPPER_VERSION)" "Buildroot" "$(PKG)" \
      > $(TARGET_DIR)/opt/klipperscreen/.version
endef

$(eval $(generic-package))