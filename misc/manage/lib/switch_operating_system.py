import logging
from enum import Enum

LOGGER = logging.getLogger()


class CfgTypes(str, Enum):
    bios = 'global'
    bmc = 'frr'
    both = "both"

