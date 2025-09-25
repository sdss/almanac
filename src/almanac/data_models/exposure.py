import os
import numpy as np
from astropy.table import Table
from datetime import datetime
from functools import partial, cached_property
from pydantic import BaseModel, Field, computed_field, validator
from typing import Optional, Tuple, Literal

from almanac import utils
from almanac.config import config
from almanac.apogee import (get_headers, match_planned_to_plugged)

from almanac.data_models.types import *
from almanac.data_models.target import Target
from almanac.data_models.fps import FPSTarget
from almanac.data_models.plate import PlateTarget

from almanac.qa import lookup_bad_exposures


class Exposure(BaseModel):

    #> Basic Information
    mjd: int = Field(description="MJD of the exposure", ge=57_600)
    exposure: int = Field(description="Exposure number", gt=0)
    observatory: Observatory = Field(description="Observatory name")
    prefix: Prefix = Field(description="Raw exposure basename prefix")

    #> Exposure Information
    name: Optional[str] = Field(
        default="",
        description=(
            "The `name` field in the exposure header often refers to the plugged"
            "plate name, which describes which targets were observed."
        )
    )
    n_read: int = Field(default=0, alias="nread", ge=0)
    image_type: ImageType = Field(default=None, alias="imagetyp")
    date_obs: datetime = Field(alias="date-obs")
    observer_comment: Optional[str] = Field(default="")

    #> Identifiers
    map_id: int = Field(default=-1, alias="mapid")
    cart_id: int = Field(default=-1, alias="cartid")
    plate_id: int = Field(default=-1, alias="plateid")
    field_id: int = Field(default=-1, alias="fieldid")
    design_id: int = Field(default=-1, alias="designid")
    config_id: int = Field(default=-1, alias="configid")

    #> Observing Conditions
    seeing: float = Field(default=float('NaN'))

    #> Instrument State
    focus: float = Field(default=float('NaN'))
    collpist: float = Field(default=float('NaN'))
    colpitch: float = Field(default=float('NaN'))
    dithpix: float = Field(default=float('NaN'))
    lamp_quartz: bool = Field(default=False, alias="lampqrtz")
    lamp_thar: bool = Field(default=False, alias="lampthar")
    lamp_une: bool = Field(default=False, alias="lampune")

    _targets: Optional[Tuple[Target]] = None

    @computed_field(description="Whether this exposure is from the FPS era")
    def fps(self) -> bool:
        return (self.mjd >= 59550)

    @computed_field
    @property
    def plugged_mjd(self) -> int:
        try:
            return int(self.name.split("-")[1])
        except:
            return -1

    @computed_field
    @property
    def plugged_iteration(self) -> str:
        try:
            return self.name.split("-")[2]
        except:
            return ""

    @computed_field
    @property
    def chip_flags(self) -> int:
        return int(np.sum(2**np.where(list(map(os.path.exists, self.paths)))[0]))

    @computed_field
    @property
    def flagged_bad(self) -> bool:
        return (self.observatory, self.mjd, self.exposure) in lookup_bad_exposures

    # TODO: we may want to change this to be way more descriptive, particularly
    #       when we start doing QA to make sure exposures look like they should
    @property
    def qa_metadata(self) -> Optional[dict]:
        print("Warning: The `qa_metadata` property will change in the future")
        return lookup_bad_exposures.get((self.observatory, self.mjd, self.exposure), None)

    class Config:
        validate_by_name = True
        validate_assignment = True

    def __repr__(self):
        return f"{self.__repr_name__()}(exposure={self.exposure}, observatory={self.observatory}, mjd={self.mjd})"

    # Validations

    @validator('cart_id', pre=True)
    def validate_cart_id(cls, v):
        if isinstance(v, str) and v.strip().upper() == 'FPS':
            return 0
        return empty_string_to_int(v, -1)

    @validator('map_id', 'plate_id', 'field_id', 'design_id', 'config_id', pre=True)
    def validate_identifiers(cls, v):
        return empty_string_to_int(v, -999)

    @validator('seeing', 'focus', 'collpist', 'colpitch', 'dithpix', pre=True)
    def validate_floats(cls, v):
        try:
            return float(v)
        except:
            return float('NaN')

    @validator('lamp_quartz', 'lamp_thar', 'lamp_une', pre=True)
    def validate_lamps(cls, v):
        return {'F': False, 'T': True}.get(str(v).strip().upper(), False)

    @computed_field
    @property
    def paths(self) -> Tuple[str]:
        return tuple(map(partial(get_exposure_path, self.observatory, self.mjd, self.prefix, self.exposure), "abc"))

    @property
    def plate_hole_path(self):
        return (
            f"{config.platelist_dir}/"
            f"{str(self.plate_id)[:-2].zfill(4)}XX/"
            f"{self.plate_id:0>6.0f}/"
            f"plateHoles-{self.plate_id:0>6.0f}.par"
        )

    @property
    def plug_map_path(self):
        return (
            f"{config.mapper_dir}/"
            f"{self.observatory}/"
            f"{self.plugged_mjd}/"
            f"plPlugMapM-{self.plate_id}-{self.plugged_mjd}-{self.plugged_iteration}.par"
        )

    @property
    def config_summary_path(self):
        directory = (
            f"{config.sdsscore_dir}/"
            f"{self.observatory}/"
            f"summary_files/"
            f"{str(self.config_id)[:-3].zfill(3)}XXX/"
            f"{str(self.config_id)[:-2].zfill(4)}XX/"
        )
        # fall back to confSummary if confSummaryFS does not exist
        for flavor in ("FS", ""):
            path = f"{directory}/confSummary{flavor}-{self.config_id}.par"
            if os.path.exists(path):
                return path

        raise FileNotFoundError(f"Could not find confSummary file for config {self.config_id} in {directory}")

    @classmethod
    def from_keys(
        cls,
        mjd: int,
        observatory: str,
        exposure: int,
        prefix: Optional[Prefix] = None,
        chip: Optional[Chip] = None
    ) -> "Exposure":
        """
        Create an Exposure instance from basic identifying keys.

        :param mjd:
            MJD of the exposure.

        :param observatory:
            Observatory name (e.g., 'apo', 'lco').

        :param exposure:
            Exposure number.

        :param prefix: [optional]
            Prefix for the exposure file (e.g., 'apR', 'asR'). If not provided,
            defaults to 'apR' for APO and 'asR' for LCO.

        :param chip: [optional]
            Chip identifier ('a', 'b', or 'c'). If not provided, will check
            all chips in order.

        :returns:
            An instance of the Exposure class populated with data extracted from
            the file headers.
        """

        if prefix is None:
            prefix = dict(apo="apR", lco="asR").get(observatory, "apR")

        for chip in (chip or "abc"):
            path = get_exposure_path(observatory, mjd, prefix, exposure, chip)
            if os.path.exists(path):
                headers = get_headers(path)
                return cls(
                    observatory=observatory,
                    mjd=mjd,
                    exposure=exposure,
                    prefix=prefix,
                    **headers
                )
        raise FileNotFoundError(f"No exposure files found for {observatory} {mjd} {exposure} {prefix}")

    @classmethod
    def from_path(cls, path: str) -> "Exposure":
        """
        Create an Exposure instance from a given file path.

        :param path:
            Full path to the exposure file.

        :returns:
            An instance of the Exposure class populated with data extracted from
            the file path and headers.
        """
        *_, observatory, mjd, basename = path.split("/")
        prefix, chip, cumulative_exposure = basename.split("-")
        exposure = int(cumulative_exposure.split(".")[0]) - mjd_to_exposure_prefix(mjd)
        headers = get_headers(path)
        return cls(
            observatory=observatory,
            mjd=mjd,
            exposure=exposure,
            prefix=prefix,
            **headers
        )

    @cached_property
    def headers(self) -> dict:
        for path in self.paths:
            if os.path.exists(path):
                return get_headers(path)
        raise FileNotFoundError(f"No exposure files found for {self.observatory} {self.mjd} {self.exposure} {self.prefix}")

    @cached_property
    def targets(self) -> Tuple[Target]:
        if self._targets is None:
            factory = FPSTarget if self.fps else PlateTarget

            if self.fps and self.config_id > 0:
                targets = Table.read(
                    self.config_summary_path,
                    format="yanny",
                    tablename="FIBERMAP"
                )
            elif not self.fps and self.plate_id > 0:
                planned, plugged, targets = match_planned_to_plugged(
                    self.plate_hole_path,
                    self.plug_map_path
                )
            else:
                targets = []
            self._targets = tuple([factory(**r) for r in targets])
        return self._targets


def empty_string_to_int(v, default) -> int:
    if isinstance(v, str) and v.strip() == '':
        return default
    elif v is None:
        return default
    return int(v)

def get_exposure_path(observatory, mjd, prefix, exposure, chip):
    return (
        f"{config.apogee_dir}/"
        f"{observatory}/"
        f"{mjd}/"
        f"{prefix}-{chip}-{mjd_to_exposure_prefix(mjd) + exposure:08d}.apz"
    )

mjd_to_exposure_prefix = lambda mjd: (int(mjd) - 55_562) * 10_000
