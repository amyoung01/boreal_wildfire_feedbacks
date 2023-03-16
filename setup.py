from setuptools import setup, find_packages

setup(name="wildfire_analysis",
      version="1.0",
      packages=(
            find_packages() + 
            find_packages(where='./utils') + 
            find_packages(where='./data_processing'))
      )

