import time
import random
import logging
import io
from datetime import datetime, timedelta
from rich.console import Console
from rich.table import Table
from rich.live import Live
from rich.text import Text
from rich.align import Align

# Mock function for testing - replace with your actual implementation
def mjd_to_datetime(mjd):
    """Convert MJD to datetime - mock implementation"""
    # MJD epoch is November 17, 1858
    epoch = datetime(1858, 11, 17)
    return epoch + timedelta(days=mjd)

class BufferedHandler(logging.Handler):
    """Custom logging handler that buffers log records"""
    def __init__(self):
        super().__init__()
        self.buffer = []
    
    def emit(self, record):
        self.buffer.append(record)
    
    def flush_to_console(self, console=None):
        """Flush buffered records to console"""
        if console is None:
            console = Console()
        
        for record in self.buffer:
            log_message = self.format(record)
            
            # Color code based on log level
            if record.levelno >= logging.ERROR:
                style = "red"
            elif record.levelno >= logging.WARNING:
                style = "yellow"
            elif record.levelno >= logging.INFO:
                style = "blue"
            else:
                style = "dim"
            
            console.print(log_message, style=style)
        
        self.buffer.clear()

class ObservationsDisplay:
    color_outside_range = "black"
    color_unknown = "white"
    color_no_data = "bright_black"
    color_apo = "dodger_blue3"
    color_lco = "green4"
    color_both = "purple4"
    color_missing = "red"

    def __init__(self, mjd_min, mjd_max, observatories=("apo", "lco")):
        self.console = Console()
        self.start_date = mjd_to_datetime(mjd_min) if isinstance(mjd_min, (int, float)) else mjd_min
        self.end_date = mjd_to_datetime(mjd_max) if isinstance(mjd_max, (int, float)) else mjd_max
        self.days_per_week = 7
        
        # Track completion status for each day
        self.completed = dict(apo=set(), lco=set())
        self.no_data = set()
        self.missing = set()
        self.offset = 0
        # Setup logging buffer
        self.log_buffer = BufferedHandler()
        self.log_buffer.setFormatter(logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%H:%M:%S'
        ))

        # Calculate the grid dimensions based on the date range
        self._setup_grid()
        self.observatories = observatories
    
    def _setup_grid(self):
        """Setup the grid based on start and end dates, organized by years"""
        # Calculate which years we need to display
        self.start_year = self.start_date.year
        self.end_year = self.end_date.year
        self.year_rows = list(range(self.start_year, self.end_year + 1))
        
        # For each year, we'll create a full year grid (Jan 1 to Dec 31)
        # but pad the beginning if our data doesn't start on Jan 1
        self.year_grids = {}
        self.dates = []
        
        self.offset = 0
        for i, year in enumerate(self.year_rows):
            year_start = datetime(year, 1, 1)
            year_end = datetime(year, 12, 31)
            
            # Find Monday of the week containing Jan 1
            jan1_weekday = year_start.weekday()  # 0=Monday, 6=Sunday
            grid_start = year_start - timedelta(days=jan1_weekday)
            if i == 0:
                self.offset = (self.start_date - grid_start).days
                
            # Find Sunday of the week containing Dec 31
            dec31_weekday = year_end.weekday()  # 0=Monday, 6=Sunday
            days_to_sunday = 6 - dec31_weekday
            grid_end = year_end + timedelta(days=days_to_sunday)
            
            # Generate dates for this year's grid
            year_dates = []
            current_date = grid_start
            while current_date <= grid_end:
                year_dates.append(current_date)
                current_date += timedelta(days=1)
            
            # Calculate weeks for this year
            total_days = len(year_dates)
            weeks = total_days // 7
            
            self.year_grids[year] = {
                'dates': year_dates,
                'weeks': weeks,
                'grid_start': grid_start,
                'grid_end': grid_end,
                'year_start': year_start,
                'year_end': year_end
            }
            
            # Add to master dates list with offset
            for i, date in enumerate(year_dates):
                self.dates.append(date)
    

    def get_day_color(self, day_index):
        """Return the color for a given day based on completion status"""
        if day_index >= len(self.dates):
            return self.color_outside_range
            
        date = self.dates[day_index]
        
        # Only show colored squares for dates within our actual range
        if date < self.start_date or date > self.end_date:
            return self.color_outside_range
        
        if day_index in self.missing:
            return self.color_missing        
        elif day_index in self.completed["apo"] and day_index in self.completed["lco"]:
            return self.color_both
        elif day_index in self.completed["apo"]:
            return self.color_apo
        elif day_index in self.completed["lco"]:
            return self.color_lco
        elif day_index in self.no_data:
            return self.color_no_data
        else:
            return self.color_unknown
    
    def _get_month_headers_for_year(self, year):
        """Generate month headers for a specific year"""
        year_data = self.year_grids[year]
        weeks = year_data['weeks']
        year_dates = year_data['dates']
        
        headers = ["   "]  # Space for day labels
        current_month = None
        text_to_add = ""
        
        for week in range(weeks):
            week_start_index = week * 7
            
            if week_start_index < len(year_dates):
                week_date = year_dates[week_start_index]
                
                # Only show month headers for dates within the actual year
                if week_date.year == year:
                    month_abbr = week_date.strftime("%b")
                    
                    # Only show month if it's different from previous week
                    if current_month != month_abbr:
                        headers.append(Text(f"{month_abbr[:1]}", style="dim"))
                        text_to_add = month_abbr[1:]
                        current_month = month_abbr
                    else:
                        if len(text_to_add) > 0:
                            headers.append(Text(text_to_add[:1], style="dim"))
                            text_to_add = text_to_add[1:]
                        else:
                            headers.append(Text(" "))
                else:
                    # This is padding (before Jan 1 or after Dec 31)
                    headers.append(Text(" "))
            else:
                headers.append(Text(" "))
        
        return headers
    
    def create_contributions_grid_for_year(self, year):
        """Create the contributions grid for a specific year"""
        year_data = self.year_grids[year]
        weeks = year_data['weeks']
        year_dates = year_data['dates']
        
        table = Table.grid(padding=0)
        
        # Add columns for day labels and each week in this year
        table.add_column()  # For day labels
        for _ in range(weeks):
            table.add_column()
        
        # Add month headers
        month_headers = self._get_month_headers_for_year(year)
        table.add_row(*month_headers)
        
        # Create rows for each day of the week
        day_names = ["S", "M", "T", "W", "T", "F", "S"]
        
        for day_of_week in range(self.days_per_week):
            row = [Text(day_names[day_of_week].ljust(3), style="dim")]
            
            for week in range(weeks):
                day_index_in_year = week * 7 + day_of_week
                
                if day_index_in_year < len(year_dates):
                    date = year_dates[day_index_in_year]
                    
                    # Find this date in our master dates list to get the right index
                    master_day_index = None
                    for i, master_date in enumerate(self.dates):
                        if master_date == date:
                            master_day_index = i
                            break
                    
                    if master_day_index is not None:
                        color = self.get_day_color(master_day_index)
                        
                        # Show square only for dates within the actual year and our date range
                        if (date.year == year and 
                            self.start_date <= date <= self.end_date):
                            square = Text("■", style=color)
                        elif date.year == year:
                            # Within the year but outside our date range
                            square = Text("■", style=self.color_no_data)
                        else:
                            # Padding dates (before Jan 1 or after Dec 31)
                            square = Text(" ")
                    else:
                        square = Text(" ")
                else:
                    square = Text(" ")
                    
                row.append(square)
            
            table.add_row(*row)
        
        return table
    
    def create_display(self):
        """Create the complete display with title and yearly grids"""
        date_range = f"{self.start_date.strftime('%b %d, %Y')} - {self.end_date.strftime('%b %d, %Y')}"
        title = Text("SDSS/APOGEE Observations", style="bold white")
        subtitle = Text(date_range, style="dim")
        
        # Create legend
        legend = Table.grid(padding=(0, 1))
        legend.add_column()
        legend.add_column()
        legend.add_column()
        legend.add_column()
        legend.add_column()
        
        items = [
            Text("■", style=self.color_no_data),
            Text("None", style="dim"),
        ]
        if "apo" in self.observatories:
            items.extend([
                Text("■", style=self.color_apo),
                Text("APO", style="dim"),
            ])
        if "lco" in self.observatories:
            items.extend([
                Text("■", style=self.color_lco),
                Text("LCO", style="dim"),
            ])            

        if "apo" in self.observatories and "lco" in self.observatories:
            items.extend([
                Text("■", style=self.color_both),
                Text("Both", style="dim"),
            ])
        legend.add_row(*items)
        
        # Combine everything
        main_table = Table.grid()
        main_table.add_column()
        main_table.add_row(Align.center(title))
        main_table.add_row(Align.center(subtitle))
        main_table.add_row("")
        
        # Add each year's grid with year header
        for i, year in enumerate(self.year_rows):
            # Add year header
            year_header = Text(str(year), style="bold cyan")
            main_table.add_row(Align.left(year_header))
            
            # Add the grid for this year
            year_grid = self.create_contributions_grid_for_year(year)
            main_table.add_row(Align.center(year_grid))
            
            # Add spacing between years except after the last one
            if i < len(self.year_rows) - 1:
                main_table.add_row("")
        
        main_table.add_row("")
        main_table.add_row(Align.center(legend))
        
        return main_table
    
    def add_observation(self, date, observatory):
        """Add an observation for a specific date and observatory"""
        # Find the day index for this date
        for i, grid_date in enumerate(self.dates):
            if grid_date.date() == date.date():
                self.completed[observatory].add(i)
                break
    
    def simulate_completion(self):
        """Randomly complete days within the specified date range"""
        # Only consider days within our actual date range
        valid_days = []
        for i, date in enumerate(self.dates):
            if self.start_date <= date <= self.end_date:
                valid_days.append(i)
        
        if valid_days:
            day_to_complete = random.choice(valid_days)
            observatory = random.choice(list(self.observatories))
            self.completed[observatory].add(day_to_complete)
            
            # Log the observation (this will be buffered)
            logger = logging.getLogger(__name__)
            logger.info(f"Observation completed at {observatory.upper()} on {self.dates[day_to_complete].strftime('%Y-%m-%d')}")
            
            return True
        return False
    
    def run_simulation(self, updates_per_second=2, observations_per_update=3):
        """Run the simulation with buffered logging"""
        # Setup logging to use our buffer
        logger = logging.getLogger(__name__)
        logger.setLevel(logging.INFO)
        
        # Remove any existing handlers and add our buffer
        for handler in logger.handlers[:]:
            logger.removeHandler(handler)
        logger.addHandler(self.log_buffer)
        
        # Count total days in range
        total_days = (self.end_date - self.start_date).days + 1
        max_observations = total_days * len(self.observatories)
        
        logger.info("Starting observation simulation...")
        
        with Live(self.create_display(), refresh_per_second=updates_per_second, screen=True) as live:
            try:
                total_completed = 0
                while total_completed < max_observations:
                    # Random delay between completions
                    time.sleep(random.uniform(0.5, 2.0))
                    
                    # Complete multiple observations per update
                    updated = False
                    for _ in range(observations_per_update):
                        if self.simulate_completion():
                            updated = True
                            total_completed += 1
                            
                            # Log progress occasionally
                            if total_completed % 10 == 0:
                                logger.info(f"Progress: {total_completed}/{max_observations} observations completed")
                    
                    if updated:
                        live.update(self.create_display())
                
                logger.info("Simulation completed!")
                
            except KeyboardInterrupt:
                logger.warning("Simulation interrupted by user")
        
        # After Live display ends, flush all buffered logs
        print("\n" + "="*50)
        print("SIMULATION LOG:")
        print("="*50)
        self.log_buffer.flush_to_console(self.console)

if __name__ == "__main__":
    # Setup basic logging
    logging.basicConfig(level=logging.INFO)
    
    # Example with logging during simulation
    start = datetime(2024, 1, 1)
    end = datetime(2024, 3, 31)
    display = ObservationsDisplay(start, end)
    
    print("Running simulation with logging...")
    print("Logs will appear after the display ends.\n")
    
    display.run_simulation(updates_per_second=3, observations_per_update=2)