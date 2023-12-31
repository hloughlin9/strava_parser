import gpxpy
import pandas as pd
import numpy as np
import folium
import matplotlib.pyplot as plt
from datetime import datetime as dt
from geopy.distance import geodesic

class StravaParser:


    """
    A module to parse GPX files into a series of lat, long points
    and organized by time (H, M, S, and cumulative time), as well
    as workout distance.
    ...
    Attributes:
    -----------
    gpx_file: str
        File path to the GPX file to be analyzed.
    
    utc_offset: int
        Optional number of hours +/- (relative to UTC) of adjustment.
    """
        

    def __init__(self, gpx_file, utc_offset=None, miles=True):
        self.file = gpx_file
        self.utc_offset = utc_offset

        with open(self.file, "r") as self.run_file:
            self.run_parsed = gpxpy.parse(self.run_file)

        self.run_points = self.run_parsed.tracks[0].segments[0].points

        # If the user declares an offset relative to UTC, that will be used.

        if self.utc_offset is not None:
            timedelta = td(hours=self.utc_offset)

            for i, _ in enumerate(self.run_points):
                self.run_points[i].adjust_time(timedelta)

        # Convert the attributes into lists and derive the distance from
        # the previous lat/long pair if there is one.
        self.lats = [getattr(self.run_points[i], 'latitude') for i, _ in enumerate(self.run_points)]
        self.longs = [getattr(self.run_points[i], 'longitude') for i, _ in enumerate(self.run_points)]
        self.elevations = [getattr(self.run_points[i], 'elevation') for i, _ in enumerate(self.run_points)]
        self.times = [getattr(self.run_points[i], 'time') for i, _ in enumerate(self.run_points)]
        self.coords_pairs = [(self.lats[i], self.longs[i]) for i in range(len(self.run_points))]
        self.run_df = pd.DataFrame([self.lats, self.longs, self.elevations, self.times]).transpose()
        self.run_df.columns = ['latitude','longitude','elevation','time']
        self.run_df['distance_from_previous'] = [(0 if i < 1 else geodesic(self.coords_pairs[i-1],
                    self.coords_pairs[i]).miles) for i in range(len(self.run_df))]
        self.run_df['distance'] = [(i if miles == True else i * 0.621371192) for i in self.run_df['distance_from_previous']]
        self.run_df['distance'] = self.run_df['distance'].cumsum().round(2)
        self.run_df = self.run_df.drop(columns=['distance_from_previous'])
        self.run_df.index = self.run_df['distance'] // 1
        
    def generate_plots(self, kind=None):

        """
        Generate plots of the run data.
        ...
        Attributes:
        -----------
        kind: str (optional)
            Choose between 'elevation' and 'route'.
        """
        
        self.run_df_reset = self.run_df.reset_index(drop=True)

        title_string = f" for Run @ {self.run_df_reset['time'][0].strftime('%Y-%m-%d %H:%M')}"
        
        if kind == "elevation":
            fig = plt.figure(figsize=(10,2))
            plt.plot(self.run_df_reset['distance'], self.run_df_reset['elevation'])
            
            # Set xticks every 1% of max_distance
            exp_step = len(self.run_df_reset) / len(str(int(self.run_df_reset['distance'].max())))

            max_distance = self.run_df_reset['distance'].max()
            step_size = max_distance * 0.1
            plt.xticks(np.arange(0, max_distance, step_size))  
            
            plt.title(f"Elevation {title_string}")
            return plt.show()
    

        elif kind == "route":

            init_lat, init_long = self.run_df_reset.iloc[0]['latitude'], self.run_df_reset.iloc[0]['longitude']
            map_points = [(self.run_df_reset['latitude'][i], self.run_df_reset['longitude'][i]) for i in range(len(self.run_df_reset))]
            map1 = folium.Map(location=(init_lat, init_long), zoom_start=15)
            folium.PolyLine(map_points).add_to(map1)
            return map1
        
        else:
            raise ValueError("Must choose 'elevation' or 'route'.")
