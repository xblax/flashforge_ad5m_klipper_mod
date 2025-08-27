################################################################################
#
# fluidd
#
################################################################################

FLUIDD_VERSION = v1.34.3
FLUIDD_SITE = https://github.com/fluidd-core/fluidd/releases/download/$(FLUIDD_VERSION)
FLUIDD_SOURCE = fluidd.zip

define FLUIDD_EXTRACT_CMDS 
	$(UNZIP) $(FLUIDD_DL_DIR)/$(FLUIDD_SOURCE) -d $(@D)/
endef

define FLUIDD_INSTALL_TARGET_CMDS
	mkdir -p $(TARGET_DIR)/opt/fluidd
	cp -a $(@D)/* $(TARGET_DIR)/opt/fluidd/
endef

$(eval $(generic-package))

