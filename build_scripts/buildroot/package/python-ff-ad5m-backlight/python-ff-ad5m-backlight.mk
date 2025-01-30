################################################################################
#
# python-ff-ad5m-backlight
#
################################################################################

PYTHON_FF_AD5M_BACKLIGHT_VERSION = 0.1
PYTHON_FF_AD5M_BACKLIGHT_SOURCE = ff-ad5m-backlight-$(PYTHON_FF_AD5M_BACKLIGHT_VERSION).tar.gz
PYTHON_FF_AD5M_BACKLIGHT_SITE = https://files.pythonhosted.org/packages/80/aa/c90577ff17f49daa7ddabf2c35829d81f6f6b391c79518ff06dfbd404637
PYTHON_FF_AD5M_BACKLIGHT_SETUP_TYPE = setuptools
PYTHON_FF_AD5M_BACKLIGHT_LICENSE = GPLv3
PYTHON_FF_AD5M_BACKLIGHT_LICENSE_FILES = LICENSE

$(eval $(python-package))
