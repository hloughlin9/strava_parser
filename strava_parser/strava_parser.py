import gpxpy
import pandas as pd
import numpy as np
from geopy.distance import geodesic
from datetime import datetime as dt

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
    """
        
    def __init__(self, gpx_file):
        self.file = gpx_file

        with open(self.file, "r") as self.run_file:
            self.run_parsed = gpxpy.parse(self.run_file)

        # Praser derives the points in the activity.
        self.distance = []
        self.run_points = self.run_parsed.tracks[0].segments[0].points
        self.lats = [self.run_points[i].latitude for i in range(len(self.run_points))]
        self.longs = [self.run_points[i].longitude for i in range(len(self.run_points))]
        self.coords_pairs = [(self.lats[i], self.longs[i]) for i in range(len(self.run_points))]
        self.els = [self.run_points[i].elevation for i in range(len(self.run_points))]
        self.times = [str(self.run_points[i].time)[:-6] for i in range(len(self.run_points))]
        self.hours = [(int(str(self.times[i])[-8:-6])-4) for i in range(len(self.run_points))]
        self.minutes = [int(str(self.times[i])[-5:-3]) for i in range(len(self.run_points))]
        self.seconds = [int(str(self.times[i])[-2:]) for i in range(len(self.run_points))]
        self.cumulative_seconds = [(self.hours[i]*3600+self.minutes[i]*60+self.seconds[i]) for i in range(len(self.run_points))]
        self.start_seconds = self.cumulative_seconds[0]
        self.time_seconds = [(i-self.start_seconds) for i in self.cumulative_seconds]
        
        # Get the distance between each pair of coordinates.
        # If it's the first one, there is no pair of coordinates,
        # so we use 0.
        for i in range(len(self.coords_pairs)):
            if i < 1:
                self.distance.append(0)

            else:
                self.distance.append(geodesic(self.coords_pairs[i-1],
                    self.coords_pairs[i]).miles)
        
        self.cumsum = np.cumsum(self.distance)

        self.run_df = pd.DataFrame([self.cumsum, self.lats,
                                    self.longs, self.els, self.times, self.hours,
                                    self.minutes, self.seconds, self.cumulative_seconds, self.time_seconds]).transpose()
        self.run_df.columns = ['dist. (mi)','lat','long','el. (m)', 'timestamp', 'H', 'M', 'S',
                               'seconds (day)', 'seconds (workout)']
        self.run_df['dist (.00)'] = self.run_df['dist. (mi)'].astype(float).round(2)
        self.run_df['el. (ft.)'] = self.run_df['el. (m)'] * 3.284


        self.run_df['quarterMile'] = (self.run_df['dist (.00)'] // 0.25).astype(int)

    def get_quarters(self):

        df_ = self.run_df.copy()
        df_['constant'] = 1
        df_ = df_.groupby("quarterMile").agg({"constant":"sum"})
        self.df_ = df_
        return self.df_


    def get_user_timezone(self):

        utc_now = dt.utcnow().hour
        user_now = dt.now().hour

        if utc_now >= 5:
            print(f"UTC now: {utc_now}")

        else:
            print(f"USER now: {user_now}")
