import numpy as np
from typing import Literal
from typing_extensions import Annotated
from pydantic import BeforeValidator

def validate_np_int64(v):
    if not isinstance(v, np.int64):
        return np.int64(v)
    return v

Int64 = Annotated[np.int64, BeforeValidator(validate_np_int64)]


Observatory = Literal["apo", "lco"]
Prefix = Literal["apR", "asR"]
Chip = Literal["a", "b", "c"]

ImageType = Literal[
    "blackbody",
    "dark",
    "object",
    "domeflat",
    "arclamp",
    "twilightflat",
    "internalflat",
    "quartzflat",
    "missing"
]
Category = Literal[
    "",
    "science",
    "sky_apogee",
    "sky_boss",
    "standard_apogee",
    "standard_boss",
    "open_fiber",
    "unplugged",
]

HoleType = Literal[
    "object",
    "coherent_sky",
    "guide",
    "light_trap",
    "alignment",
    "quality",
    "manga",
    "manga_single",
    "manga_alignment",
    "acquisition_center",
    "acquisition_offaxis",
    "apogee",
    "center",
    "trap",
    "boss",
    "apogee_shared",
    "apogee_south",
    "bosshalf",
    "boss_shared",
    "fps",
    "unplugged",
]

ObjType = Literal[
    "galaxy",
    "qso",
    "star_bhb",
    "star_carbon",
    "star_brown_dwarf",
    "star_sub_dwarf",
    "star_caty_var",
    "star_red_dwarf",
    "star_white_dwarf",
    "redden_std",
    "spectrophoto_std",
    "hot_std",
    "rosat_a",
    "rosat_b",
    "rosat_c",
    "rosat_d",
    "serendipity_blue",
    "serendipity_first",
    "serendipity_red",
    "serendipity_distant",
    "serendipity_manual",
    "qa",
    "sky",
    "na",
]
