from pydantic import BaseModel, Field
from typing import List
from almanac.data_models.target import Target

class FPSTarget(Target):

    """A target that was observed with the SDSS-V Fiber Positioning System."""

    positioner_id: int = Field(alias='positionerId')
    hole_id: str = Field(alias='holeId')
    fiber_type: str = Field(alias='fiberType')
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
    decollided: bool

    # Position coordinates
    xwok: float = Field(default=float('NaN'))
    ywok: float = Field(default=float('NaN'))
    zwok: float = Field(default=float('NaN'))
    x_focal: float = Field(alias='xFocal')
    y_focal: float = Field(alias='yFocal')

    # Angles
    alpha: float
    beta: float

    # Catalog coordinates
    ra_cat: float = Field(alias="racat", description="Right Ascension [deg] from catalog")
    dec_cat: float = Field(alias="deccat", description="Declination [deg] from catalog")
    pmra: float = Field(description="Proper motion in RA [mas/yr]")
    pmdec: float = Field(description="Proper motion in Dec [mas/yr]")
    parallax: float = Field(description="Parallax [mas]")

    # Observed coordinates
    ra: float
    dec: float
    ra_observed: float = Field(default=float('NaN'))
    dec_observed: float = Field(default=float('NaN'))
    alt_observed: float = Field(default=float('NaN'))
    az_observed: float = Field(default=float('NaN'))

    # Wavelength information
    lambda_design: float = Field(default=0.0)
    lambda_eff: float = Field(default=0.0)
    coord_epoch: float = Field(default=0.0)

    # Instrument identifiers
    spectrograph_id: int = Field(alias='spectrographId')
    fiber_id: int = Field(alias='fiberId')

    # Magnitudes
    mag: List[float]
    optical_prov: str
    bp_mag: float
    gaia_g_mag: float
    rp_mag: float
    h_mag: float

    # Target information
    catalogid: int
    carton_to_target_pk: int
    cadence: str
    firstcarton: str
    program: str
    category: str

    # Target flags
    sdssv_boss_target0: int
    sdssv_apogee_target0: int

    # Position deltas
    delta_ra: float
    delta_dec: float

    # Target of opportunity
    too: bool = Field(default=False, description="Target of opportunity")
    too_id: int = Field(default=-1)
    too_program: str = Field(default="")

    # Identifiers
    sdss_id: int = Field(default=-1)

    class Config:
        # Allow population by field name or alias
        validate_by_name = True
        # Validate assignment to attributes
        validate_assignment = True
