from typing import Literal
from pydantic import BaseModel, Field

from almanac.data_models.types import *

class FPSTarget(BaseModel):

    """A target that was observed with the SDSS-V Fiber Positioning System."""

    # Target information
    catalogid: int
    category: Literal[Category] = Field(description="Category of the target")
    cadence: str = Field(description="Cadence identifier")
    firstcarton: str = Field(description="Main carton from which this carton was drawn")
    program: str = Field(description="Program for 'firstcarton'")

    # Positioner and hole identifiers
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

    # Status flags
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

    # Target coordinates
    ra: float = Field(alias="racat", description="Right Ascension [deg]")
    dec: float = Field(alias="deccat", description="Declination [deg]")
    alt: float = Field(description="Altitude of the fiber on the sky [deg]", default=float('NaN'), alias="alt_observed")
    az: float = Field(description="Azimuth of the fiber on the sky [deg]", default=float('NaN'), alias="az_observed")

    # Wavelength information
    lambda_design: float = Field(default=0.0)
    lambda_eff: float = Field(default=0.0)
    coord_epoch: float = Field(default=0.0)

    # Instrument identifiers
    spectrograph_id: int = Field(description="Spectrograph identifier", alias='spectrographId')
    fiber_id: int = Field(description="Fiber identifier", alias='fiberId')

    # Position deltas
    delta_ra: float = Field(description="The amount in RA this fiber has been offset", default=float('NaN'))
    delta_dec: float = Field(description="The amount in Dec this fiber has been offset", default=float('NaN'))

    # Target of opportunity
    too: bool = Field(default=False, description="Target of opportunity")
    too_id: int = Field(default=-1)
    too_program: str = Field(default="")

    class Config:
        validate_by_name = True
        validate_assignment = True
