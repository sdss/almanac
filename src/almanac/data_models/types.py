from typing import Literal

Observatory = Literal["apo", "lco"]
Prefix = Literal["apR", "asR"]
Chip = Literal["a", "b", "c"]

ImageType = Literal["Dark", "Object", "DomeFlat", "ArcLamp", "InternalFlat", "QuartzFlat"]
TargetType = Literal["NA", "science", "sky", "standard"]

PluggedHoleType = Literal[
    "OBJECT",
    "COHERENT_SKY",
    "GUIDE",
    "LIGHT_TRAP",
    "ALIGNMENT",
    "QUALITY",
    "MANGA",
    "MANGA_SINGLE",
    "MANGA_ALIGNMENT",
    "ACQUISITION_CENTER",
    "ACQUISITION_OFFAXIS",
]
PlannedHoleType = Literal[
    "ALIGNMENT",
    "APOGEE",
    "CENTER",
    "GUIDE",
    "TRAP"
]
ObjType = Literal[
    "GALAXY",
    "QSO",
    "STAR_BHB",
    "STAR_CARBON",
    "STAR_BROWN_DWARF",
    "STAR_SUB_DWARF",
    "STAR_CATY_VAR",
    "STAR_RED_DWARF",
    "STAR_WHITE_DWARF",
    "REDDEN_STD",
    "SPECTROPHOTO_STD",
    "HOT_STD",
    "ROSAT_A",
    "ROSAT_B",
    "ROSAT_C",
    "ROSAT_D",
    "SERENDIPITY_BLUE",
    "SERENDIPITY_FIRST",
    "SERENDIPITY_RED",
    "SERENDIPITY_DISTANT",
    "SERENDIPITY_MANUAL",
    "QA",
    "SKY",
    "NA",
]
