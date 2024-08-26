from peewee import (
    AutoField,
    FloatField,
    BooleanField,
    DateTimeField,
    IntegerField,
    TextField,
    ForeignKeyField
)
from almanac.models.base import BaseModel
from almanac.models.fields import BitField

class Exposure(BaseModel):

    pk = AutoField(help_text="Primary key")
    
    #> Exposure information
    name = TextField(null=True, help_text="")
    observatory = TextField(help_text="Observatory acronym")
    mjd = IntegerField(help_text="Modified Julian Date of observation")
    exposure = IntegerField(help_text="Exposure number")

    prefix = TextField(help_text=f"Raw image basename prefix") # TODO: Does this ever change other than APO/LCO? Remove it?

    #> Identifiers
    field_id = IntegerField(null=True, help_text="Field identifier", column_name="fieldid")
    design_id = IntegerField(null=True, help_text="Design identifier", column_name="designid")
    config_id = IntegerField(null=True, help_text="Configuration identifier", column_name="configid")
    cart_id = TextField(null=True, help_text="Cart identifier (pre-FPS era)", column_name="cartid")
    plate_id = IntegerField(null=True, help_text="Plate identifier", column_name="plateid")
    map_id = IntegerField(null=True, help_text="Map identifier", column_name="mapid") # TODO what is this again

    #> Exposure types
    exp_type = TextField(null=True, help_text="Exposure type", column_name="exptype")
    image_type = TextField(null=True, help_text="Image type", column_name="imagetyp")
    plate_type = TextField(null=True, help_text="Plate type", column_name="platetyp")

    #> Lamp status
    lamp_quartz = BooleanField(null=True, help_text="Quartz lamp", column_name="lampqrtz")
    lamp_thar = BooleanField(null=True, help_text="ThAr lamp", column_name="lampthar")
    lamp_une = BooleanField(null=True, help_text="UNe lamp", column_name="lampune")

    #> Instrument configuration
    focus = FloatField(null=True, help_text="Focus position [-]") # TODO: units
    dither = FloatField(null=True, help_text="Dither position [pixels]", column_name="dithpix")
    collpist = FloatField(null=True, ) # TODO
    colpitch = FloatField(null=True, ) # TODO
    tcammid = FloatField(null=True, ) # TODO
    tlsdetb = FloatField(null=True, ) # TODO
    n_read = IntegerField(help_text="Number of up-the-ramp reads", column_name="nread")

    #> Observing conditions
    date_obs = DateTimeField(null=True, help_text="Observation date and time")
    seeing = FloatField(null=True, help_text="Seeing [arcseconds]")
    comment = TextField(null=True, help_text="Observer comment", column_name="obscmt")

    #> Flags
    warn_flags = BitField(default=0, help_text="Warning flags")
    flag_no_chip_a_image = warn_flags.flag(2**0, "Chip A was not read out (or file is missing)")
    flag_no_chip_b_image = warn_flags.flag(2**1, "Chip B was not read out (or file is missing)")
    flag_no_chip_c_image = warn_flags.flag(2**2, "Chip C was not read out (or file is missing)")
    
    info_flags = BitField(default=0, help_text="Information flags")
    flag_read_from_chip_a = info_flags.flag(2**0, "Exposure information read from chip A")
    flag_read_from_chip_b = info_flags.flag(2**1, "Exposure information read from chip B")
    flag_read_from_chip_c = info_flags.flag(2**2, "Exposure information read from chip C")

    class Meta:
        indexes = (
            (
                (
                    "observatory",
                    "mjd",
                    "exposure",
                    "prefix"
                ),
                True
            ), # Don't forget this comma
        )


    @property
    def path(self):
        return f"$SAS_BASE_DIR/sdsswork/data/apogee/{self.observatory}/{self.mjd}/{self.prefix}-{self.exposure}.apz"
        

class Sequence(BaseModel):

    """
    A set of sequential exposures of the same type, taken during the same night.
    """

    pk = AutoField(help_text="Primary key")
    mjd = IntegerField(help_text="Modified Julian Date of sequence")
    observatory = TextField(help_text="Observatory acronym")
    exp_type = TextField(help_text="A string describing the sequence type (e.g., Object, ArcLamp)")
    first_exposure = IntegerField(help_text="First exposure number of this sequence.")
    last_exposure = IntegerField(help_text="Last exposure number of this sequence.")
    n_exposures = IntegerField(help_text="Number of exposures in this sequence.")

    class Meta:
        indexes = (
            (
                (
                    "mjd",
                    "observatory",
                    "exp_type",
                    "first_exposure",
                    "last_exposure"
                ),
                True
            ), # Don't forget this comma
        )
class Visit(BaseModel):

    """
    An APOGEE visit is a sequence of sequential exposures of the same sources taken 
    with the same configuration (`field_id`, `plate_id`, `config_id`, `image_type`)
    at an observatory in a single night.
    """

    pk = AutoField(help_text="Primary key")
    sequence = ForeignKeyField(Sequence, column_name="sequence_pk")

    # All this information is just copied from the exposure level.
    observatory = TextField(help_text="Observatory acronym")
    mjd = IntegerField(help_text="Modified Julian Date of observation")

    @property
    def exposures(self):
        return self.sequence.exposures

