################################################################################
#
# moonraker
#
################################################################################

MOONRAKER_VERSION = v0.9.3
MOONRAKER_SITE = https://github.com/Arksine/moonraker.git
MOONRAKER_SITE_METHOD = git

MOONRAKER_LICENSE = GPL-3.0
MOONRAKER_LICENSE_FILES = LICENSE

MOONRAKER_DEPENDENCIES = \
	python3 \
	python-dbus-next \
	python-tornado \
	python-serial \
	python-pillow \
	python-distro \
	python-inotify-simple \
	python-pynacl \
	python-paho-mqtt \
	python-zeroconf \
	python-jinja2 \
	python-dbus-fast \
	python-apprise \
	python-ldap3 \
	python-periphery \
	python-importlib-metadata \
	python-streaming-form-data \
	python-preprocess-cancellation \
	python-uvloop \
	python-pre-commit \
	python-libnacl

define MOONRAKER_INSTALL_TARGET_CMDS
	mkdir -p $(TARGET_DIR)/opt/moonraker/
	cp -r $(@D)/moonraker $(@D)/docs $(@D)/LICENSE $(@D)/README.md $(TARGET_DIR)/opt/moonraker/
	printf "%s-%s-%s\n" "$(MOONRAKER_VERSION)" "Buildroot" "$(PKG)" > $(TARGET_DIR)/opt/moonraker/moonraker/.version
endef

$(eval $(generic-package))