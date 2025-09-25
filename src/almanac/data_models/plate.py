from enum import Enum
from typing import List, Literal, Optional
from pydantic import BaseModel, Field, validator

from almanac.data_models.target import Target
from almanac.data_models.types import *

class PluggedHole(BaseModel):

    """Frozen data class representing a plugged hole."""

    class Config:
        frozen = True

    obj_id: List[int] = Field(alias="objId", min_items=5, max_items=5, description="Object IDs (5 elements)")
    hole_type: HoleType = Field(alias="holeType", description="Type of hole")
    obj_type: ObjType = Field(alias="objType", description="Object type")

    ra: float = Field(description="Right ascension in degrees")
    dec: float = Field(description="Declination in degrees")

    x_focal: float = Field(alias="xFocal", description="X focal plane coordinate")
    y_focal: float = Field(alias="yFocal", description="Y focal plane coordinate")

    fiber_id: int = Field(alias="fiberId", description="Fiber ID")
    spectrograph_id: int = Field(alias="spectrographId", description="Spectrograph ID")
    throughput: int = Field(description="Throughput value")



class PlateHole(BaseModel):

    """Frozen data class representing a planned plate hole."""

    class Config:
        frozen = True

    category: Literal[Category] = Field(description="Category of the target", alias="targettype")

    # Basic target information
    planned_hole_type: HoleType = Field(alias="holetype", description="Hole type string")
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
    x_focal: float = Field(description="X focal plane coordinate", alias="xfocal")
    y_focal: float = Field(description="Y focal plane coordinate", alias="yfocal")

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


class PlateTarget(PlateHole, PluggedHole, Target):

    """ An astronomical target that was observed with plates. """

    @validator('hole_type', 'planned_hole_type', pre=True)
    def validate_hole_type(cls, v):
        return v.lower()

    @validator('category', pre=True)
    def validate_category(cls, v):
        # Make consistent across FPS and plate era.
        translate_from_plate_to_fps = {
            "sky": "sky_apogee",
            "standard": "standard_apogee",
            "na": ""
        }
        return translate_from_plate_to_fps.get(v.lower(), v)
