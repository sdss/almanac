from enum import Enum
from typing import List
from pydantic import BaseModel, Field


class HoleType(Enum):
    """Enumeration for different hole types in the plug map."""
    OBJECT = "OBJECT"
    COHERENT_SKY = "COHERENT_SKY"
    GUIDE = "GUIDE"
    LIGHT_TRAP = "LIGHT_TRAP"
    ALIGNMENT = "ALIGNMENT"
    QUALITY = "QUALITY"
    MANGA = "MANGA"
    MANGA_SINGLE = "MANGA_SINGLE"
    MANGA_ALIGNMENT = "MANGA_ALIGNMENT"
    ACQUISITION_CENTER = "ACQUISITION_CENTER"
    ACQUISITION_OFFAXIS = "ACQUISITION_OFFAXIS"


class ObjType(Enum):
    """Enumeration for different object types."""
    GALAXY = "GALAXY"
    QSO = "QSO"
    STAR_BHB = "STAR_BHB"
    STAR_CARBON = "STAR_CARBON"
    STAR_BROWN_DWARF = "STAR_BROWN_DWARF"
    STAR_SUB_DWARF = "STAR_SUB_DWARF"
    STAR_CATY_VAR = "STAR_CATY_VAR"
    STAR_RED_DWARF = "STAR_RED_DWARF"
    STAR_WHITE_DWARF = "STAR_WHITE_DWARF"
    REDDEN_STD = "REDDEN_STD"
    SPECTROPHOTO_STD = "SPECTROPHOTO_STD"
    HOT_STD = "HOT_STD"
    ROSAT_A = "ROSAT_A"
    ROSAT_B = "ROSAT_B"
    ROSAT_C = "ROSAT_C"
    ROSAT_D = "ROSAT_D"
    SERENDIPITY_BLUE = "SERENDIPITY_BLUE"
    SERENDIPITY_FIRST = "SERENDIPITY_FIRST"
    SERENDIPITY_RED = "SERENDIPITY_RED"
    SERENDIPITY_DISTANT = "SERENDIPITY_DISTANT"
    SERENDIPITY_MANUAL = "SERENDIPITY_MANUAL"
    QA = "QA"
    SKY = "SKY"
    NA = "NA"


class PlugMapObject(BaseModel):
    """
    Frozen data class representing a plug map object.
    
    Corresponds to the PLUGMAPOBJ struct from the C typedef.
    """
    
    class Config:
        frozen = True
        
    obj_id: List[int] = Field(..., min_items=5, max_items=5, description="Object IDs (5 elements)")
    hole_type: HoleType = Field(..., description="Type of hole")
    ra: float = Field(..., description="Right ascension in degrees")
    dec: float = Field(..., description="Declination in degrees")
    mag: List[float] = Field(..., min_items=5, max_items=5, description="Magnitudes (5 elements)")
    star_l: float = Field(..., description="Star likelihood")
    exp_l: float = Field(..., description="Exponential likelihood")
    de_vauc_l: float = Field(..., description="de Vaucouleurs likelihood")
    obj_type: ObjType = Field(..., description="Object type")
    x_focal: float = Field(..., description="X focal plane coordinate")
    y_focal: float = Field(..., description="Y focal plane coordinate")
    spectrograph_id: int = Field(..., description="Spectrograph ID")
    fiber_id: int = Field(..., description="Fiber ID")
    throughput: int = Field(..., description="Throughput value")
    prim_target: int = Field(..., description="Primary target flag")
    sec_target: int = Field(..., description="Secondary target flag")


class PlateHole(BaseModel):
    """
    Frozen data class representing the STRUCT1 typedef.
    
    Contains comprehensive target and observation metadata.
    """
    
    class Config:
        frozen = True
    
    # Basic target information
    holetype: str = Field(..., max_length=16, description="Hole type string")
    targettype: str = Field(..., max_length=9, description="Target type string") 
    sourcetype: str = Field(..., max_length=9, description="Source type string")
    target_ra: float = Field(..., description="Target right ascension")
    target_dec: float = Field(..., description="Target declination")
    
    # Plate and fiber information
    iplateinput: int = Field(..., description="Plate input ID")
    pointing: int = Field(..., description="Pointing number")
    offset: int = Field(..., description="Offset value")
    fiberid: int = Field(..., description="Fiber ID")
    block: int = Field(..., description="Block number")
    iguide: int = Field(..., description="Guide flag")
    
    # Focal plane coordinates
    xf_default: float = Field(..., description="Default X focal coordinate")
    yf_default: float = Field(..., description="Default Y focal coordinate")
    xfocal: float = Field(..., description="X focal plane coordinate")
    yfocal: float = Field(..., description="Y focal plane coordinate")
    
    # Spectroscopic parameters
    lambda_eff: float = Field(..., description="Effective wavelength")
    zoffset: float = Field(..., description="Z offset")
    bluefiber: int = Field(..., description="Blue fiber flag")
    chunk: int = Field(..., description="Chunk number")
    ifinal: int = Field(..., description="Final flag")
    
    # File information
    origfile: str = Field(..., max_length=2, description="Original file identifier")
    fileindx: int = Field(..., description="File index")
    
    # Physical properties
    diameter: float = Field(..., description="Diameter")
    buffer: float = Field(..., description="Buffer size")
    priority: int = Field(..., description="Target priority")
    
    # Status flags
    assigned: int = Field(..., description="Assigned flag")
    conflicted: int = Field(..., description="Conflicted flag") 
    ranout: int = Field(..., description="Ran out flag")
    outside: int = Field(..., description="Outside flag")
    
    # MaNGA specific
    mangaid: str = Field(..., max_length=12, description="MaNGA ID")
    ifudesign: int = Field(..., description="IFU design ID")
    ifudesignsize: int = Field(..., description="IFU design size")
    bundle_size: int = Field(..., description="Bundle size")
    fiber_size: float = Field(..., description="Fiber size")
    ifuid: int = Field(..., description="IFU ID")
    
    # Photometric data
    tmass_j: float = Field(..., description="2MASS J magnitude")
    tmass_h: float = Field(..., description="2MASS H magnitude")
    tmass_k: float = Field(..., description="2MASS K magnitude")
    gsc_vmag: float = Field(..., description="GSC V magnitude")
    tyc_bmag: float = Field(..., description="Tycho B magnitude")
    tyc_vmag: float = Field(..., description="Tycho V magnitude")
    
    # Array photometry
    mfd_mag: List[float] = Field(..., min_items=6, max_items=6, description="MFD magnitudes (6 elements)")
    usnob_mag: List[float] = Field(..., min_items=5, max_items=5, description="USNO-B magnitudes (5 elements)")
    
    # Spectral parameters
    sp_param_source: str = Field(..., max_length=3, description="Spectral parameter source")
    sp_params: List[float] = Field(..., min_items=4, max_items=4, description="Spectral parameters (4 elements)")
    sp_param_err: List[float] = Field(..., min_items=4, max_items=4, description="Spectral parameter errors (4 elements)")
    
    # Target selection flags
    marvels_target1: int = Field(..., description="MARVELS target flag 1")
    marvels_target2: int = Field(..., description="MARVELS target flag 2")
    boss_target1: int = Field(..., description="BOSS target flag 1")
    boss_target2: int = Field(..., description="BOSS target flag 2")
    ancillary_target1: int = Field(..., description="Ancillary target flag 1")
    ancillary_target2: int = Field(..., description="Ancillary target flag 2")
    segue2_target1: int = Field(..., description="SEGUE-2 target flag 1")
    segue2_target2: int = Field(..., description="SEGUE-2 target flag 2")
    segueb_target1: int = Field(..., description="SEGUE-B target flag 1")
    segueb_target2: int = Field(..., description="SEGUE-B target flag 2")
    apogee_target1: int = Field(..., description="APOGEE target flag 1")
    apogee_target2: int = Field(..., description="APOGEE target flag 2")
    apogee2_target1: int = Field(..., description="APOGEE-2 target flag 1")
    apogee2_target2: int = Field(..., description="APOGEE-2 target flag 2")
    apogee2_target3: int = Field(..., description="APOGEE-2 target flag 3")
    manga_target1: int = Field(..., description="MaNGA target flag 1")
    manga_target2: int = Field(..., description="MaNGA target flag 2")
    manga_target3: int = Field(..., description="MaNGA target flag 3")
    eboss_target0: int = Field(..., description="eBOSS target flag 0")
    eboss_target1: int = Field(..., description="eBOSS target flag 1")
    eboss_target2: int = Field(..., description="eBOSS target flag 2")
    eboss_target_id: int = Field(..., description="eBOSS target ID")
    
    # Targeting information
    thing_id_targeting: int = Field(..., description="Thing ID for targeting")
    objid_targeting: int = Field(..., description="Object ID for targeting")
    targetids: str = Field(..., max_length=24, description="Target IDs string")
    
    # SDSS imaging data
    run: int = Field(..., description="SDSS run number")
    rerun: str = Field(..., max_length=6, description="SDSS rerun")
    camcol: int = Field(..., description="SDSS camera column")
    field: int = Field(..., description="SDSS field number")
    id: int = Field(..., description="Object ID")
    
    # Photometric measurements (all 5-element arrays for ugriz bands)
    psfflux: List[float] = Field(..., min_items=5, max_items=5, description="PSF flux (5 bands)")
    psfflux_ivar: List[float] = Field(..., min_items=5, max_items=5, description="PSF flux inverse variance (5 bands)")
    fiberflux: List[float] = Field(..., min_items=5, max_items=5, description="Fiber flux (5 bands)")
    fiberflux_ivar: List[float] = Field(..., min_items=5, max_items=5, description="Fiber flux inverse variance (5 bands)")
    fiber2flux: List[float] = Field(..., min_items=5, max_items=5, description="Fiber2 flux (5 bands)")
    fiber2flux_ivar: List[float] = Field(..., min_items=5, max_items=5, description="Fiber2 flux inverse variance (5 bands)")
    psfmag: List[float] = Field(..., min_items=5, max_items=5, description="PSF magnitude (5 bands)")
    fibermag: List[float] = Field(..., min_items=5, max_items=5, description="Fiber magnitude (5 bands)")
    fiber2mag: List[float] = Field(..., min_items=5, max_items=5, description="Fiber2 magnitude (5 bands)")
    mag: List[float] = Field(..., min_items=5, max_items=5, description="Magnitude (5 bands)")
    
    # Astrometric data
    epoch: float = Field(..., description="Epoch of observation")
    pmra: float = Field(..., description="Proper motion in RA")
    pmdec: float = Field(..., description="Proper motion in Dec")