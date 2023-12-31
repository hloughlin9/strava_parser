import gpxpy
import pandas as pd
import numpy as np
import folium
import matplotlib.pyplot as plt
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

        with open(self.file, "r") as run_file:
            self.run_parsed = gpxpy.parse(run_file)

        self.run_points = self.run_parsed.tracks[0].segments[0].points

        if self.utc_offset is not None:
            timedelta = td(hours=self.utc_offset)
            for point in self.run_points:
                point.adjust_time(timedelta)

        self.lats = [point.latitude for point in self.run_points]
        self.longs = [point.longitude for point in self.run_points]
        self.elevations = [point.elevation for point in self.run_points]
        self.times = [point.time for point in self.run_points]
        self.coords_pairs = list(zip(self.lats, self.longs))
        self.run_df = pd.DataFrame([self.lats, self.longs, self.elevations, self.times]).transpose()
        self.run_df.columns = ['latitude', 'longitude', 'elevation', 'time']
        self.run_df['distance_from_previous'] = [0 if i < 1 else geodesic(self.coords_pairs[i-1], self.coords_pairs[i]).miles for i in range(len(self.run_df))]
        self.run_df['distance'] = [i if miles else i * 0.621371192 for i in self.run_df['distance_from_previous']]
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
            max_distance = self.run_df_reset['distance'].max()
            step_size = max_distance * 0.1  # 1% of max_distance
            plt.xticks(np.arange(0, max_distance, step_size))  
            
            plt.title(f"Elevation {title_string}")
            return plt.show()

        elif kind == "route":
            init_lat, init_long = self.run_df_reset.iloc[0]['latitude'], self.run_df_reset.iloc[0]['longitude']
            map_points = [(self.run_df_reset['latitude'][i], self.run_df_reset['longitude'][i]) for i in range(len(self.run_df_reset))]
            map1 = folium.Map(location=(init_lat, init_long), zoom_start=13)
            folium.PolyLine(map_points).add_to(map1)
            return map1
        
        else:
            raise ValueError("Must choose 'elevation' or 'route'.")
