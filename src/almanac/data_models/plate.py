from typing import Literal
from pydantic import BaseModel, Field, validator

from almanac.data_models.types import *

class PlateTarget(BaseModel):

    """ A target that was observed with plates. """

    # Target information
    sdss_id: Int64 = Field(default=-1)
    target_ids: str = Field(alias="targetids")
    category: Literal[Category] = Field(description="Category of the target", alias="targettype")

    # Positioner and hole identifiers
    hole_type: HoleType = Field(alias="holeType", description="Type of hole")
    planned_hole_type: HoleType = Field(alias="holetype", description="Hole type string")
    obj_type: ObjType = Field(alias="objType", description="Object type")
    assigned: bool = Field(description="Assigned flag")

    # Status flags
    conflicted: bool = Field(description="Conflicted flag")
    ranout: bool = Field(description="Ran out flag")
    outside: bool = Field(description="Outside flag")

    # Position coordinates
    x_focal: float = Field(description="X focal plane coordinate", alias="xfocal")
    y_focal: float = Field(description="Y focal plane coordinate", alias="yfocal")
    xf_default: float = Field(description="Default X focal coordinate")
    yf_default: float = Field(description="Default Y focal coordinate")

    # Target coordinates
    ra: float = Field(description="Right ascension [deg]")
    dec: float = Field(description="Declination [deg]")

    # Wavelength information
    lambda_eff: float = Field(description="Effective wavelength")
    zoffset: float = Field(description="Z offset")

    # Instrument identifiers
    spectrograph_id: int = Field(alias="spectrographId", description="Spectrograph ID")
    fiber_id: int = Field(alias="fiberId", description="Fiber ID")
    planned_fiber_id: int = Field(alias="fiberid", description="Fiber ID")
    throughput: int = Field(description="Throughput value")

    # Plate-specific information
    iplateinput: int = Field(description="Plate input ID")
    pointing: int = Field(description="Pointing number")
    offset: int = Field(description="Offset value")
    block: int = Field(description="Block number")
    iguide: int = Field(description="Guide flag")
    bluefiber: int = Field(description="Blue fiber flag")
    chunk: int = Field(description="Chunk number")
    ifinal: int = Field(description="Final flag")

    # Physical properties
    diameter: float = Field(description="Diameter")
    buffer: float = Field(description="Buffer size")
    priority: int = Field(description="Target priority")

    @validator('hole_type', 'planned_hole_type', 'obj_type', pre=True)
    def enforce_lower_case(cls, v):
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

    class Config:
        validate_by_name = True
        validate_assignment = True
        arbitrary_types_allowed = True
