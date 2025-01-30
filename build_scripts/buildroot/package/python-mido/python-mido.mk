################################################################################
#
# python-mido
#
################################################################################

PYTHON_MIDO_VERSION = 1.3.2
PYTHON_MIDO_SOURCE = mido-$(PYTHON_MIDO_VERSION).tar.gz
PYTHON_MIDO_SITE = https://files.pythonhosted.org/packages/9e/a4/f9bfc7016c9fb1e348078a3455ab0d1573bcb5154dc7fc1aba9fcfe38b95
PYTHON_MIDO_SETUP_TYPE = setuptools
PYTHON_MIDO_LICENSE = MIT
PYTHON_MIDO_LICENSE_FILES = LICENSE

$(eval $(python-package))
