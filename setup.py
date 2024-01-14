from setuptools import setup, find_packages

setup(
    name='strava-parser',
    version='0.3',
    packages=find_packages(),
    install_requires=[
        'gpxpy',
        'pandas',
        'numpy',
        'geopy',
        'matplotlib',
        'folium',
    ],
)
