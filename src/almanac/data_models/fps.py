from pydantic import BaseModel, Field
from typing import List, Literal
from almanac.data_models.target import Target
from almanac.data_models.types import *

class FPSTarget(Target):

    """A target that was observed with the SDSS-V Fiber Positioning System."""

    positioner_id: int = Field(alias='positionerId', description="Positioner identifier")
    hole_id: str = Field(alias='holeId', description="Hole ID in which the positioner is sitting")
    fiber_type: str = Field(alias='fiberType', description="Type of fiber")
    assigned: bool = Field(
        description=(
            "Target is assigned to this fiber in `robostrategy`. If False, no "
            "target assigned for this fiber (likely BOSS instead), and no "
            "targeting information available"
        )
    )
    on_target: bool = Field(description="Fiber placed on target")
    disabled: bool = Field(default=False, description="Fiber is disabled")
    valid: bool = Field(description="Converted on-sky coordinates to robot (α,β)")
    decollided: bool = Field(description="Positioner had to be moved to decollide it")

    # Position coordinates
    x_wok: float = Field(description="x-coordinate in the wok frame", default=float('NaN'), alias="xwok")
    y_wok: float = Field(description="y-coordinate in the wok frame", default=float('NaN'), alias="ywok")
    z_wok: float = Field(description="z-coordinate in the wok frame", default=float('NaN'), alias="zwok")
    x_focal: float = Field(description="x-coordinate in the focal plane", alias='xFocal')
    y_focal: float = Field(description="y-coordinate in the focal plane", alias='yFocal')

    # Angles
    alpha: float = Field(description="Alpha angle of the positioner arm")
    beta: float = Field(description="Beta angle of the positioner arm")

    # Catalog coordinates
    ra_cat: float = Field(alias="racat", description="Right Ascension [deg] from catalog")
    dec_cat: float = Field(alias="deccat", description="Declination [deg] from catalog")
    pmra: float = Field(description="Proper motion in RA [mas/yr]")
    pmdec: float = Field(description="Proper motion in Dec [mas/yr]")
    parallax: float = Field(description="Parallax [mas]")

    # Observed coordinates
    ra: float = Field(description="Calculated Right Ascension [deg] of the fiber on the sky")
    dec: float = Field(description="Calculated Declination [deg] of the fiber on the sky")
    ra_observed: float = Field(default=float('NaN'))
    dec_observed: float = Field(default=float('NaN'))
    alt_observed: float = Field(description="Altitude of the fiber on the sky [deg]", default=float('NaN'))
    az_observed: float = Field(description="Azimuth of the fiber on the sky [deg]", default=float('NaN'))

    # Wavelength information
    lambda_design: float = Field(default=0.0)
    lambda_eff: float = Field(default=0.0)
    coord_epoch: float = Field(default=0.0)

    # Instrument identifiers
    spectrograph_id: int = Field(description="Spectrograph identifier", alias='spectrographId')
    fiber_id: int = Field(description="Fiber identifier", alias='fiberId')

    # Magnitudes
    gaia_g_mag: float = Field( description="Gaia G magnitude", default=float('NaN'))
    gaia_bp_mag: float = Field(alias='bp_mag', description="Gaia BP magnitude", default=float('NaN'))
    gaia_rp_mag: float = Field(description="Gaia RP magnitude", default=float('NaN'))
    h_mag: float = Field(description="H-band magnitude", default=float('NaN'))

    # Target information
    catalogid: int
    cadence: str = Field(description="Cadence identifier")
    firstcarton: str = Field(description="Main carton from which this carton was drawn")
    program: str = Field(description="Program for 'firstcarton'")
    category: Literal[Category] = Field(description="Category of the target")

    # Position deltas
    delta_ra: float = Field(description="The amount in RA this fiber has been offset", default=float('NaN'))
    delta_dec: float = Field(description="The amount in Dec this fiber has been offset", default=float('NaN'))

    # Target of opportunity
    too: bool = Field(default=False, description="Target of opportunity")
    too_id: int = Field(default=-1)
    too_program: str = Field(default="")

    # Identifiers
    sdss_id: int = Field(default=-1)

    class Config:
        validate_by_name = True
        validate_assignment = True
