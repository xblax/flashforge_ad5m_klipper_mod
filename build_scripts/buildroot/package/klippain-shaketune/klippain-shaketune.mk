################################################################################
#
# klippain-shaketune
#
################################################################################

KLIPPAIN_SHAKETUNE_VERSION = c8ef451ec4153af492193ac31ed7eea6a52dbe4e
KLIPPAIN_SHAKETUNE_SITE = https://github.com/Frix-x/klippain-shaketune.git
KLIPPAIN_SHAKETUNE_SITE_METHOD = git
KLIPPAIN_SHAKETUNE_LICENSE = GPL-3.0+
KLIPPAIN_SHAKETUNE_LICENSE_FILES = LICENSE
KLIPPAIN_SHAKETUNE_DEPENDENCIES = \
	python3 \
	klipper \
	python-git \
	python-matplotlib \
	python-numpy \
	python-scipy \
	python-pywavelets \
	python-zstandard \
	openblas

define KLIPPAIN_SHAKETUNE_INSTALL_TARGET_CMDS
	mkdir -p $(TARGET_DIR)/opt/klippain-shaketune
	cp -r $(@D)/{shaketune,docs}  $(TARGET_DIR)/opt/klippain-shaketune/
	cp $(@D)/LICENSE $(TARGET_DIR)/opt/klippain-shaketune/
	ln -frsn $(TARGET_DIR)/opt/klippain-shaketune/shaketune $(TARGET_DIR)/opt/klipper/klippy/extras/shaketune
endef

$(eval $(generic-package))
