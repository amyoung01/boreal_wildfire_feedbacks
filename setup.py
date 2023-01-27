from setuptools import setup, find_packages

setup(name="wildfire_analysis",
      version="0.1",
      packages=(
            find_packages() + 
            find_packages(where='./utils') + 
            find_packages(where='./data') + 
            find_packages(where='./cffdrs') + 
            find_packages(where='./models'))
      )

