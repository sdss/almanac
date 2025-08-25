import numpy as np
from time import time
from datetime import datetime
from itertools import cycle
from typing import Tuple, Union, Optional, List, Dict, Any
from astropy.table import Table
from astropy.time import Time
from astropy.io.registry import register_identifier, register_reader, register_writer
from pydl.pydlutils.yanny import is_yanny, read_table_yanny, write_table_yanny
from rich.console import Console
from rich.table import Table as RichTable
from rich.text import Text

register_identifier("yanny", Table, is_yanny)
register_reader("yanny", Table, read_table_yanny)
register_writer("yanny", Table, write_table_yanny)


def get_observatories(apo: bool, lco: bool) -> Tuple[str, ...]:
    """Get observatory names based on boolean flags.
    
    Args:
        apo: Whether to include APO observatory
        lco: Whether to include LCO observatory
        
    Returns:
        Tuple of observatory names ("apo", "lco", or both)
    """
    if apo and not lco:
        return ("apo",)
    elif lco and not apo:
        return ("lco",)
    else:
        return ("apo", "lco")


def timestamp_to_mjd(v: float) -> float:
    """Convert Unix timestamp to Modified Julian Date (MJD).
    
    Args:
        v: Unix timestamp in seconds
        
    Returns:
        Modified Julian Date as float
    """
    return (v / 86400.0) + 40587.5


def get_current_mjd() -> int:
    """Get current Modified Julian Date as integer.
    
    Returns:
        Current MJD as integer
    """
    return int(timestamp_to_mjd(time()))


def datetime_to_mjd(date: str) -> int:
    """Convert date string to Modified Julian Date.
    
    Args:
        date: Date string in format "YYYY-MM-DD"
        
    Returns:
        Modified Julian Date as integer
    """
    return int(timestamp_to_mjd(datetime.strptime(date, "%Y-%m-%d").timestamp()))

def mjd_to_datetime(mjd: float) -> datetime:
    """Convert Modified Julian Date to datetime object.
    
    Args:
        mjd: Modified Julian Date
        
    Returns:
        Datetime object
    """
    return Time(mjd, format='mjd').datetime

def parse_mjds(mjd: Optional[int], mjd_start: Optional[int], mjd_end: Optional[int], 
               date: Optional[str], date_start: Optional[str], date_end: Optional[str], 
               earliest_mjd: int = 0) -> Tuple[Union[int, range, Tuple[int, ...]], int, int]:
    """Parse MJD and date parameters to determine observation date range.
    
    Args:
        mjd: Single MJD value (can be negative for relative to current)
        mjd_start: Start MJD for range (can be negative for relative to current)
        mjd_end: End MJD for range (can be negative for relative to current)
        date: Single date string in "YYYY-MM-DD" format
        date_start: Start date string in "YYYY-MM-DD" format
        date_end: End date string in "YYYY-MM-DD" format
        earliest_mjd: Earliest allowed MJD value (default: 0)
        
    Returns:
        Tuple containing:
            - MJD values (single int, range, or tuple)
            - Start MJD (int)
            - End MJD (int)
            
    Raises:
        ValueError: If more than one time specification method is provided
        RuntimeError: If no valid time specification is found
    """
    has_mjd_range = mjd_start is not None or mjd_end is not None
    has_date_range = date_start is not None or date_end is not None

    current_mjd = get_current_mjd()
    n_given = sum([has_mjd_range, has_date_range, mjd is not None, date is not None])
    if n_given > 1:
        raise ValueError(
            "Cannot specify more than one of --mjd, --mjd-start/--mjd-end, --date, --date-start/--date-end"
        )
    if n_given == 0:
        return (current_mjd, current_mjd, current_mjd)
    if mjd is not None:
        if mjd < 0:
            mjd += current_mjd
        return ((mjd, ), mjd, mjd)
    if has_mjd_range:
        mjd_start = mjd_start or earliest_mjd
        if mjd_start < 0:
            mjd_start += current_mjd
        mjd_end = mjd_end or current_mjd
        if mjd_end < 0:
            mjd_end += current_mjd
        return (range(mjd_start, 1 + mjd_end), mjd_start, mjd_end)
    if date is not None:
        mjd = datetime_to_mjd(date)
        return ((mjd, ), mjd, mjd)
    if has_date_range:
        mjd_start = earliest_mjd if date_start is None else datetime_to_mjd(date_start)
        mjd_end = current_mjd if date_end is None else datetime_to_mjd(date_end)
        return (range(mjd_start, 1 + mjd_end), mjd_start, mjd_end)

    raise RuntimeError("Should not be able to get here")


def rich_display_exposures(
    table: Table,
    sequence_indices: Optional[Dict[str, np.ndarray]] = None,
    console: Optional[Console] = None,
    header_style: str = "bold cyan",
    column_names: Optional[List[str]] = None,
    sequence_styles: Tuple[str, ...] = ("green", "yellow"),
    missing_style: str = "blink bold red",
    title_style: str = "bold blue",
) -> None:
    """Display exposure information using Rich table formatting.
    
    Args:
        table: Astropy Table containing exposure data
        sequence_indices: Dictionary mapping sequence names to index arrays (default: None)
        console: Rich Console instance (default: None, creates new one)
        header_style: Style for table headers (default: "bold cyan")
        sequence_styles: Tuple of styles to cycle through for sequences (default: ("green", "yellow"))
        missing_style: Style for missing/error entries (default: "red")
        title_style: Style for the table title (default: "bold blue")
    """
    if console is None:
        console = Console()
    
    # Create the title
    observatory, mjd = table["observatory"][0], table["mjd"][0]
    title = f"{len(table)} exposures from {observatory.upper()} on MJD {mjd}"
    
    # Create Rich table
    rich_table = RichTable(title=title, title_style=title_style, show_header=True, header_style=header_style)
    
    # Add columns based on the astropy table columns
    if column_names is None:
        column_names = table.colnames

    for col_name in column_names:
        rich_table.add_column(col_name, justify="center")
    
    # Prepare sequence tracking
    if sequence_indices is None:
        all_sequence_indices = []
    else:
        all_sequence_indices = np.vstack(
            [v for v in sequence_indices.values() if len(v) > 0]
        )
    
    sequence_styles_cycle = cycle(sequence_styles)
    in_sequence, current_sequence_style = (False, next(sequence_styles_cycle))
    
    # Add rows to the table
    for i, row in enumerate(table):
        # Check if this row is part of a sequence
        row_style = None
        
        if len(all_sequence_indices) > 0:
            try:
                j, k = np.where(all_sequence_indices == i)
            except:
                pass
            else:
                # Could be start or end of sequence, and could be out of order
                start_of_sequence = 0 in k
                end_of_sequence = 1 in k

                if start_of_sequence:
                    in_sequence = True
                    current_sequence_style = next(sequence_styles_cycle)
                elif end_of_sequence:  # only end of sequence
                    in_sequence = False

        # Determine row style
        if in_sequence:
            row_style = current_sequence_style
        else:
            # Check if it's missing or has issues
            if not table["path_exists"][i]:
                row_style = missing_style
            else:
                # Check if any field contains "Missing"
                row_contains_missing = any(
                    str(row[col]).find("Missing") > -1 for col in table.colnames
                )
                if row_contains_missing:
                    row_style = missing_style
        
        # Convert row data to strings and apply styling if needed
        row_data = []
        for col in column_names:
            value = str(row[col])
            if row_style:
                row_data.append(Text(value, style=row_style))
            else:
                row_data.append(value)
        
        rich_table.add_row(*row_data)
    
    console.print(rich_table)
    console.print()  # Add a blank line after the table
