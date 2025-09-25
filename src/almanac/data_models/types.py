from typing import Literal

Observatory = Literal["apo", "lco"]
Prefix = Literal["apR", "asR"]
Chip = Literal["a", "b", "c"]

ImageType = Literal[
    "Blackbody",
    "Dark",
    "Object",
    "DomeFlat",
    "ArcLamp",
    "InternalFlat",
    "QuartzFlat",
    "Missing"
]
TargetType = Literal["NA", "science", "sky", "standard"]

HoleType = Literal[
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
    "APOGEE",
    "CENTER",
    "TRAP",
    "BOSS",
    "APOGEE_SHARED",
    "APOGEE_SOUTH",
    "BOSSHALF",
    "BOSS_SHARED"
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
