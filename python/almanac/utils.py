import numpy as np
from time import time
from datetime import datetime
from astropy.utils.console import color_print
from itertools import cycle

def get_observatories(apo, lco):
    if apo and not lco:
        return ("apo", )
    elif lco and not apo:
        return ("lco", )
    else:
        return ("apo", "lco")
    
def timestamp_to_mjd(v):
    return (v / 86400.0) + 40587.5

def get_current_mjd():
    return int(timestamp_to_mjd(time()))

def datetime_to_mjd(date):
    return int(timestamp_to_mjd(datetime.strptime(date, "%Y-%m-%d").timestamp()))

def parse_mjds(mjd, mjd_start, mjd_end, date, date_start, date_end, earliest_mjd=0):
    has_mjd_range = (mjd_start is not None or mjd_end is not None)
    has_date_range = (date_start is not None or date_end is not None)
    
    n_given = sum([has_mjd_range, has_date_range, mjd is not None, date is not None])
    if n_given > 1:
        raise ValueError("Cannot specify more than one of --mjd, --mjd-start/--mjd-end, --date, --date-start/--date-end")
    
    if n_given == 0:
        return (get_current_mjd(), )

    if mjd is not None:
        if mjd < 0:
            mjd += get_current_mjd()
        return (mjd, )
    if has_mjd_range:
        mjd_start = mjd_start or earliest_mjd
        mjd_end = mjd_end or get_current_mjd()
        return range(mjd_start, 1 + mjd_end)
    if date is not None:        
        return (datetime_to_mjd(date), )
    if has_date_range:
        mjd_start = earliest_mjd if date_start is None else datetime_to_mjd(date_start)
        mjd_end = get_current_mjd() if date_end is None else datetime_to_mjd(date_end)
        return range(mjd_start, 1 + mjd_end)
    
    raise RuntimeError("Should not be able to get here")


def pretty_print_table(table, sequence_indices=None, header_color="lightcyan", sequence_colors=("lightgreen", "yellow")):
    
    observatory, mjd = table["observatory"][0], table["mjd"][0]
    color_print(f"{len(table)} exposures from {observatory.upper()} on MJD {mjd}:", header_color)

    lines, outs = table.formatter._pformat_table(
        table, -1, max_width=None, show_name=True, show_unit=None, show_dtype=False, align=None
    )
    n_header = outs["n_header"]      
    if sequence_indices is None:
        sequence_indices = []  
    
    color_print(lines[1], header_color)
    sequence_colors = cycle(sequence_colors)
    in_sequence, sequence_color = (False, next(sequence_colors))
    for i, line in enumerate(lines, start=-n_header):
        if i < 0:
            color_print(line, header_color)
        else:
            try:
                j, k = np.where(sequence_indices == i)
            except:
                None
            else:
                #print(f"found {j, k} {i} in {sequence_indices}")
                # could be start or end of sequence, and could be out of order
                start_of_sequence = (0 in k)
                end_of_sequence = (1 in k)
                
                if start_of_sequence:
                    in_sequence = True
                    sequence_color = next(sequence_colors)
                elif end_of_sequence: # only end of sequence
                    in_sequence = False
                        
            if in_sequence:
                color_print(line, sequence_color)
            else:                     
                print(line)
    
    color_print(lines[1], header_color)    
    print("\n")
    
    