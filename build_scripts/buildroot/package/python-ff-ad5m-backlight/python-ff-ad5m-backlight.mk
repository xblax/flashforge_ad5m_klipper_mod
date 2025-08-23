################################################################################
#
# python-ff-ad5m-backlight
#
################################################################################

PYTHON_FF_AD5M_BACKLIGHT_VERSION = 3cd9a0898e51a18e83976c7cab29037f8364f406
PYTHON_FF_AD5M_BACKLIGHT_SITE = https://github.com/loss-and-quick/flashforge_ad5m_backlight.git
PYTHON_FF_AD5M_BACKLIGHT_SITE_METHOD = git
PYTHON_FF_AD5M_BACKLIGHT_SETUP_TYPE = setuptools
PYTHON_FF_AD5M_BACKLIGHT_LICENSE = GPLv3
PYTHON_FF_AD5M_BACKLIGHT_LICENSE_FILES = LICENSE

$(eval $(python-package))
