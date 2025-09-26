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
