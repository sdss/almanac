from enum import Flag, Enum, auto
from pydantic import BaseModel, Field, computed_field
from typing import List, Optional, Tuple
from astropy.table import Table

import os
import numpy as np

from almanac import utils # to initiate yanny reader/writer
from almanac.config import config


class ExposurePathExists(Flag):
    chip_a = auto()
    chip_b = auto()
    chip_c = auto()


class FPSTarget(BaseModel):

    """SDSS-V Fiber Positioning System Target"""
    
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



class Exposure(BaseModel):

    exposure: int
    date_obs: str = Field(alias="date-obs") # TODO: make datetime
    observer_comment: Optional[str] = Field(default="")
    observatory: str 
    mjd: int

    exposure_type: str = Field(alias="exptype")
    image_type: str = Field(alias="imagetyp")
    name: str = Field(default="")

    map_id: str = Field(default=-1, alias="mapid")
    cart_id: int = Field(default=-1, alias="cartid")
    plate_id: int = Field(default=-1, alias="plateid")
    field_id: int = Field(default=-1, alias="fieldid")
    design_id: int = Field(default=-1, alias="designid")
    config_id: int = Field(default=-1, alias="configid")

    seeing: float = Field(default=float('NaN'))
    focus: float = Field(default=float('NaN'))

    n_read: int = Field(default=0, alias="nread")
    lamp_quartz: bool = Field(default=False, alias="lampqrtz")
    lamp_thar: bool = Field(default=False, alias="lampthar")
    lamp_une: bool = Field(default=False, alias="lampune")

    collpist: float = Field(default=float('NaN'))
    colpitch: float = Field(default=float('NaN'))
    dithpix: float = Field(default=float('NaN'))

    prefix: str = Field(default="apR")

    #paths_exist: ExposurePathExists

    _targets: Optional[Tuple[FPSTarget]] = None

    @computed_field
    @property
    def targets(self) -> Tuple[FPSTarget]:
        if self._targets is None:
            t = Table.read(
                self.config_summary_path, 
                format="yanny", 
                tablename="FIBERMAP"
            )
            self._targets = [FPSTarget(**r) for r in t]
        return self._targets
    
    

    @computed_field
    @property
    def plugged_mjd(self) -> int:
        try:
            return self.name.split("-")[1]
        except:
            return -1

    @computed_field
    @property
    def plugged_iteration(self) -> str:
        try:
            return self.name.split("-")[2]
        except:
            return ""
        
    
    @property
    def plate_hole_path(self):
        return (
            f"{config.platelist_dir}/"
            f"{str(plate_id)[:-2].zfill(4)}XX/"
            f"{plate_id:0>6.0f}/"
            f"plateHoles-{plate_id:0>6.0f}.par"
        )

    @property
    def plug_map_path(self):
        return (
            f"{config.mapper_dir}/{self.observatory}/{self.mjd}/"
            f"plPlugMapM-{self.plate_id}-{self.plugged_mjd}-{self.plugged_iteration}.par"
        )

    @property
    def config_summary_path(self):
        c = str(self.config_id)
        directory = (
            f"{config.sdsscore_dir}/"
            f"{self.observatory}/"
            f"summary_files/"
            f"{c[:-3].zfill(3)}XXX/"
            f"{c[:-2].zfill(4)}XX/"
        )

        # fall back to confSummary if confSummaryFS does not exist
        path = f"{directory}/confSummaryFS-{self.config_id}.par"
        if not os.path.exists(path):
            path = f"{directory}/confSummary-{self.config_id}.par"
        return path

    def __repr__(self):
        return f"{self.__repr_name__()}(exposure={self.exposure}, observatory={self.observatory}, mjd={self.mjd})"
        

    class Config:
        validate_by_name = True
        validate_assignment = True

    #    readout_chip_a=False,
    #    readout_chip_b=False,
    #    readout_chip_c=False,
    #    obscmt="",
    #    tcammid="",
    #    tlsdetb="",
    #    path_exists=False,
    #)

