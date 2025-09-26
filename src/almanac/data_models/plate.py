from typing import Literal
from pydantic import BaseModel, Field, validator, model_validator, computed_field

from almanac.data_models.types import *

class PlateTarget(BaseModel):

    """ A target that was observed with plates. """

    # Target information
    sdss_id: Int64 = Field(default=-1)
    target_ids: str = Field(alias="targetids")
    category: Literal[Category] = Field(description="Category of the target", alias="targettype")

    # Positioner and hole identifiers
    observatory: Literal[Observatory] = Field(description="Observatory") # necessary for fiber mapping fixes
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
    plugged_mjd: int = Field(description="MJD when this plate was plugged") # necessary for fiber mapping fixes
    fix_fiber_flag: int = Field(default=0, description="Whether this fiber mapping was fixed in software")

    # Physical properties
    diameter: float = Field(description="Diameter")
    buffer: float = Field(description="Buffer size")
    priority: int = Field(description="Target priority")

    @computed_field
    def twomass_designation(self) -> str:
        """ Convert a target ID to a standardized designation format. """
        # The target_ids seem to be styled '2MASS-J...'
        target_id = self.target_ids.strip()
        target_id = target_id[5:] if target_id.startswith("2MASS") else target_id
        target_id = str(target_id.lstrip("-Jdb_"))
        return target_id


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


    @model_validator(mode="after")
    def fix_fiber_mappings(self):
        # Dates from /uufs/chpc.utah.edu/common/home/sdss09/software/apogee/Linux/apogee/trunk/data/cal/apogee-n.par
        # Mapping logic from https://github.com/sdss/apogee_drp/blob/4ab6a04e448b279f2514550802b6732693e9847a/python/apogee_drp/utils/plugmap.py#L210-L238
        # Check against fix_fiber_flag to avoid recursively fixing things.
        if self.observatory == "apo" and self.fix_fiber_flag == 0:
            if 56764 <= self.plugged_mjd <= 56773 and self.fiber_id >= 0:
                self.fix_fiber_flag = 1
                sub_id = (self.fiber_id - 1) % 30
                bundle_id = (self.fiber_id - sub_id) // 30
                self.fiber_id = (9 - bundle_id) * 30 + sub_id + 1
            if 58034 <= self.plugged_mjd <= 58046 and self.hole_type == "object" and self.spectrograph_id == 2:
                self.fix_fiber_flag = 2
                # Note that the DRP code has this in a way where it ONLY changes
                # fibers 31, 37, 45, and 54, but their expressions are written in
                # a way that you would think they are meant to be ranges.
                # TODO: I've checked with Holtz
                offset_ranges = [
                    (31, 36, +23),
                    (37, 44, +8),
                    (45, 52, -8),
                    (54, 59, -23),

                    # and missing fibers from unpopulated 2 of MTP:
                    (53, 53, -1),
                    (60, 60, -1)
                ]
                for lower, upper, offset in offset_ranges:
                    if (lower <= self.fiber_id) & (self.fiber_id <= upper):
                        self.fiber_id += offset
                        break

        return self
