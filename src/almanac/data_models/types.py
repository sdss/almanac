import numpy as np
from typing import Literal
from typing_extensions import Annotated
from pydantic import BeforeValidator

def validate_np_int64(v):
    if v is None:
        return np.int64(-1)
    if not isinstance(v, np.int64):
        return np.int64(v)
    return v

def validate_int(v):
    if v is None:
        return -1
    return int(v)

def validate_float(v):
    if v is None:
        return float('nan')
    try:
        return float(v)
    except (ValueError, TypeError):
        return float('nan')

def validate_str(v):
    if isinstance(v, bytes):
        return v.decode('utf-8')
    if v is None:
        return ""
    return str(v)

def validate_bool(v):
    if v is None:
        return False
    return bool(v)

Int64 = Annotated[np.int64, BeforeValidator(validate_np_int64)]
Int = Annotated[int, BeforeValidator(validate_int)]
Float = Annotated[float, BeforeValidator(validate_float)]
Str = Annotated[str, BeforeValidator(validate_str)]
Bool = Annotated[bool, BeforeValidator(validate_bool)]


Observatory = Annotated[Literal["apo", "lco"], BeforeValidator(validate_str)]
Prefix = Annotated[Literal["apR", "asR"], BeforeValidator(validate_str)]
Chip = Annotated[Literal["a", "b", "c"], BeforeValidator(validate_str)]

ImageType = Annotated[
    Literal[
        "blackbody",
        "dark",
        "object",
        "domeflat",
        "arclamp",
        "twilightflat",
        "internalflat",
        "quartzflat",
        "missing"
    ],
    BeforeValidator(validate_str)
]
Category = Annotated[
    Literal[
        "",
        "bonus",
        "science",
        "sky_apogee",
        "sky_boss",
        "standard_apogee",
        "standard_boss",
        "open_fiber",
        "unplugged",
    ],
    BeforeValidator(validate_str)
]

HoleType = Annotated[
    Literal[
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
    ],
    BeforeValidator(validate_str)
]

ObjType = Annotated[
    Literal[
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
    ],
    BeforeValidator(validate_str)
]
