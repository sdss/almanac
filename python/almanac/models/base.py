from peewee import Model
from almanac.models.utils import get_database_and_schema

#database, schema = get_database_and_schema("/uufs/chpc.utah.edu/common/home/u6020307/almanac.sqlite")
database, schema = get_database_and_schema()

class BaseModel(Model):
    
    class Meta:
        database = database
        schema = schema
        legacy_table_names = False
