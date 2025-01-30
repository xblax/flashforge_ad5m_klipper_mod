################################################################################
#
# python-ff-ad5m-audio
#
################################################################################

PYTHON_FF_AD5M_AUDIO_VERSION = 0.4
PYTHON_FF_AD5M_AUDIO_SOURCE = ff-ad5m-audio-$(PYTHON_FF_AD5M_AUDIO_VERSION).tar.gz
PYTHON_FF_AD5M_AUDIO_SITE = https://files.pythonhosted.org/packages/54/0c/0d02ce982b032efd797069682b1689644ab1e701de3a413d7a01fb2ae462
PYTHON_FF_AD5M_AUDIO_SETUP_TYPE = setuptools
PYTHON_FF_AD5M_AUDIO_LICENSE = CC-4.0-BY-NC
PYTHON_FF_AD5M_AUDIO_LICENSE_FILES = LICENSE

$(eval $(python-package))
