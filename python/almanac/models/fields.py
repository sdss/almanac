
from peewee import (ColumnBase, BitField as _BitField)


class BitField(_BitField):

    """A binary bitfield field that allows for `help_text` to be specified in each `FlagDescriptor`."""
    
    def __init__(self, *args, **kwargs):
        kwargs.setdefault('default', 0)
        super(_BitField, self).__init__(*args, **kwargs)
        self.__current_flag = 1

    def flag(self, value=None, help_text=None):
        if value is None:
            value = self.__current_flag
            self.__current_flag <<= 1
        else:
            self.__current_flag = value << 1

        class FlagDescriptor(ColumnBase):
            def __init__(self, field, value, help_text=None):
                self._field = field
                self._value = value
                self.help_text = help_text
                super(FlagDescriptor, self).__init__()
            def clear(self):
                return self._field.bin_and(~self._value)
            def set(self):
                return self._field.bin_or(self._value)
            def __get__(self, instance, instance_type=None):
                if instance is None:
                    return self
                value = getattr(instance, self._field.name) or 0
                return (value & self._value) != 0
            def __set__(self, instance, is_set):
                if is_set not in (True, False):
                    raise ValueError('Value must be either True or False')
                value = getattr(instance, self._field.name) or 0
                if is_set:
                    value |= self._value
                else:
                    value &= ~self._value
                setattr(instance, self._field.name, value)
            def __sql__(self, ctx):
                return ctx.sql(self._field.bin_and(self._value) != 0)
        return FlagDescriptor(self, value, help_text)        