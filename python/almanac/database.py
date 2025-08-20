import logging
import sdssdb
from sdssdb.peewee.sdss5db.catalogdb import database

from time import time
from almanac.config import logger, config, asdict

# Create a temporary sdssdb profile based on almanac settings
t = -time()
sdssdb.config.update(almanac=asdict(config.sdssdb))
is_database_available = database.set_profile("almanac")
t += time()

if not is_database_available:
    logger.warning(f"Unable to connect to SDSS database after {t:.1f} seconds")
elif t > config.database_connect_time_warning:
    logger.warning(
        f"Took {t:.1f} s to connect to SDSS database.\n"
        f"You can suppress this warning with the `database_connect_time_warning` configuration."
    )

from sdssdb.peewee.sdss5db.catalogdb import (SDSS_ID_flat, TwoMassPSC, CatalogToTwoMassPSC)
