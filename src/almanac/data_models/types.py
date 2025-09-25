from typing import Literal

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
    "open_fiber"
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
    "boss_shared"
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
