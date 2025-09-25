from enum import Enum
from typing import List, Literal, Optional, get_args
from pydantic import BaseModel, Field, validator

from almanac.data_models.target import Target
from almanac.data_models.types import *

_TargetType_args = get_args(TargetType)

class PluggedHole(BaseModel):

    """Frozen data class representing a plugged hole."""

    class Config:
        frozen = True

    obj_id: List[int] = Field(alias="objId", min_items=5, max_items=5, description="Object IDs (5 elements)")
    hole_type: HoleType = Field(alias="holeType", description="Type of hole")
    ra: float = Field(description="Right ascension in degrees")
    dec: float = Field(description="Declination in degrees")
    mag: List[float] = Field(min_items=5, max_items=5, description="Magnitudes (5 elements)")
    star_l: float = Field(alias="starL", description="Star likelihood")
    exp_l: float = Field(alias="expL", description="Exponential likelihood")
    de_vauc_l: float = Field(alias="deVaucL", description="de Vaucouleurs likelihood")
    obj_type: ObjType = Field(alias="objType", description="Object type")
    x_focal: float = Field(alias="xFocal", description="X focal plane coordinate")
    y_focal: float = Field(alias="yFocal", description="Y focal plane coordinate")
    spectrograph_id: int = Field(alias="spectrographId", description="Spectrograph ID")
    fiber_id: int = Field(alias="fiberId", description="Fiber ID")
    throughput: int = Field(description="Throughput value")
    prim_target: int = Field(alias="primTarget", description="Primary target flag")
    sec_target: int = Field(alias="secTarget", description="Secondary target flag")


class PlateHole(BaseModel):

    """Frozen data class representing a planned plate hole."""

    class Config:
        frozen = True

    # Basic target information
    planned_hole_type: HoleType = Field(alias="holetype", description="Hole type string")
    target_type: TargetType = Field(alias="targettype", description="Target type string")
    source_type: str = Field(alias="sourcetype", description="Source type string") # TODO
    target_ra: float = Field(description="Target right ascension")
    target_dec: float = Field(description="Target declination")
    target_ids: str = Field(alias="targetids")

    # Plate and fiber information
    iplateinput: int = Field(description="Plate input ID")
    pointing: int = Field(description="Pointing number")
    offset: int = Field(description="Offset value")
    planned_fiber_id: int = Field(alias="fiberid", description="Fiber ID")
    block: int = Field(description="Block number")
    iguide: int = Field(description="Guide flag")

    # Focal plane coordinates
    xf_default: float = Field(description="Default X focal coordinate")
    yf_default: float = Field(description="Default Y focal coordinate")
    xfocal: float = Field(description="X focal plane coordinate")
    yfocal: float = Field(description="Y focal plane coordinate")

    # Spectroscopic parameters
    lambda_eff: float = Field(description="Effective wavelength")
    zoffset: float = Field(description="Z offset")
    bluefiber: int = Field(description="Blue fiber flag")
    chunk: int = Field(description="Chunk number")
    ifinal: int = Field(description="Final flag")

    # File information
    origfile: str = Field(description="Original file identifier")
    fileindx: int = Field(description="File index")

    # Physical properties
    diameter: float = Field(description="Diameter")
    buffer: float = Field(description="Buffer size")
    priority: int = Field(description="Target priority")

    # Status flags
    assigned: int = Field(description="Assigned flag")
    conflicted: int = Field(description="Conflicted flag")
    ranout: int = Field(description="Ran out flag")
    outside: int = Field(description="Outside flag")

    # MaNGA specific
    mangaid: Optional[str] = Field(default="", description="MaNGA ID")
    ifudesign: Optional[int] = Field(default=-999, description="IFU design ID")
    ifudesignsize: Optional[int] = Field(default=-999, description="IFU design size")
    bundle_size: Optional[int] = Field(default=-999, description="Bundle size")
    fiber_size: Optional[float] = Field(default=-999.0, description="Fiber size")
    ifuid: Optional[int] = Field(default=-999, description="IFU ID")

    # Photometric data
    tmass_j: float = Field(description="2MASS J magnitude")
    tmass_h: float = Field(description="2MASS H magnitude")
    tmass_k: float = Field(description="2MASS K magnitude")
    gsc_vmag: float = Field(description="GSC V magnitude")
    tyc_bmag: float = Field(description="Tycho B magnitude")
    tyc_vmag: float = Field(description="Tycho V magnitude")

    # Array photometry
    mfd_mag: List[float] = Field(min_items=6, max_items=6, description="MFD magnitudes (6 elements)")
    usnob_mag: List[float] = Field(min_items=5, max_items=5, description="USNO-B magnitudes (5 elements)")

    # Spectral parameters
    sp_param_source: str = Field(description="Spectral parameter source")
    sp_params: List[float] = Field(min_items=4, max_items=4, description="Spectral parameters (4 elements)")
    sp_param_err: List[float] = Field(min_items=4, max_items=4, description="Spectral parameter errors (4 elements)")

    # Target selection flags
    marvels_target1: int = Field(description="MARVELS target flag 1")
    marvels_target2: int = Field(description="MARVELS target flag 2")
    boss_target1: int = Field(description="BOSS target flag 1")
    boss_target2: int = Field(description="BOSS target flag 2")
    ancillary_target1: int = Field(description="Ancillary target flag 1")
    ancillary_target2: int = Field(description="Ancillary target flag 2")
    segue2_target1: int = Field(description="SEGUE-2 target flag 1")
    segue2_target2: int = Field(description="SEGUE-2 target flag 2")
    segueb_target1: int = Field(description="SEGUE-B target flag 1")
    segueb_target2: int = Field(description="SEGUE-B target flag 2")
    apogee_target1: int = Field(description="APOGEE target flag 1")
    apogee_target2: int = Field(description="APOGEE target flag 2")
    #apogee2_target1: int = Field(description="APOGEE-2 target flag 1")
    #apogee2_target2: int = Field(description="APOGEE-2 target flag 2")
    #apogee2_target3: int = Field(description="APOGEE-2 target flag 3")
    manga_target1: int = Field(description="MaNGA target flag 1")
    manga_target2: int = Field(description="MaNGA target flag 2")
    #manga_target3: int = Field(description="MaNGA target flag 3")
    #eboss_target0: int = Field(description="eBOSS target flag 0")
    #eboss_target1: int = Field(description="eBOSS target flag 1")
    #eboss_target2: int = Field(description="eBOSS target flag 2")
    #eboss_target_id: int = Field(description="eBOSS target ID")

    # SDSS imaging data
    run: int = Field(description="SDSS run number")
    rerun: str = Field(description="SDSS rerun")
    camcol: int = Field(description="SDSS camera column")
    field: int = Field(description="SDSS field number")
    id: int = Field(description="Object ID")

    # Photometric measurements (all 5-element arrays for ugriz bands)
    psfflux: List[float] = Field(min_items=5, max_items=5, description="PSF flux (5 bands)")
    psfflux_ivar: List[float] = Field(min_items=5, max_items=5, description="PSF flux inverse variance (5 bands)")
    fiberflux: List[float] = Field(min_items=5, max_items=5, description="Fiber flux (5 bands)")
    fiberflux_ivar: List[float] = Field(min_items=5, max_items=5, description="Fiber flux inverse variance (5 bands)")
    fiber2flux: List[float] = Field(min_items=5, max_items=5, description="Fiber2 flux (5 bands)")
    fiber2flux_ivar: List[float] = Field(min_items=5, max_items=5, description="Fiber2 flux inverse variance (5 bands)")
    psfmag: List[float] = Field(min_items=5, max_items=5, description="PSF magnitude (5 bands)")
    fibermag: List[float] = Field(min_items=5, max_items=5, description="Fiber magnitude (5 bands)")
    fiber2mag: List[float] = Field(min_items=5, max_items=5, description="Fiber2 magnitude (5 bands)")
    planned_mag: List[float] = Field(min_items=5, max_items=5, description="Magnitude (5 bands)")

    # Astrometric data
    epoch: float = Field(description="Epoch of observation")
    pmra: float = Field(description="Proper motion in RA")
    pmdec: float = Field(description="Proper motion in Dec")

    @validator('target_type', pre=True)
    def validate_target_type(cls, v):
        # Handle situations where they give 'SKY' instead of 'sky', etc
        if v not in _TargetType_args and v.lower() in _TargetType_args:
            return v.lower()
        return v



class PlateTarget(PlateHole, PluggedHole, Target):

    """ An astronomical target that was observed with plates. """

    pass
