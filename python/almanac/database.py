import warnings
import sdssdb
from almanac.config import config, asdict

# Create a temporary sdssdb profile based on almanac settings
sdssdb.config.update(almanac=asdict(config.sdssdb))

from sdssdb.peewee.sdss5db.catalogdb import database

if not database.set_profile("almanac"):
    warnings.warn("Unable to connect to SDSS database")

from sdssdb.peewee.sdss5db.catalogdb import (SDSS_ID_flat, TwoMassPSC, CatalogToTwoMassPSC)
