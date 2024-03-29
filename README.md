[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.7761883.svg)](https://doi.org/10.5281/zenodo.7761883)  
[![License: CC0-1.0](https://img.shields.io/badge/License-Creative_Commons_Zero_1.0-green.svg)](https://creativecommons.org/publicdomain/zero/1.0/)  

# boreal_wildfire_feedbacks  

#### Author: Adam M. Young  
#### email: adam.m.young@outlook.com  
#### date created: 2023-03-12
---
This repository contains the code and scripts needed to recreate analysis
designed to model historical area burned in boreal forest ecosystems in North
America and project 21st-century area burned under different climate change 
scenarios. All datasets created through this analysis are available for download
via the USGS Data Repository (sciencebase.gov).  


The following code will allow for downloading the prerequisite software and datasets, 
as well as and runnning of the analysis. The code also provides the step-by-step directions for recreating the analyis. 


<span style="color:red"> **WARNING** </span>: Will run the full analysis, including installing libraries and 
downloading all datasets. Strongly advised to do this step-by-step instead.

```bash

$ curl -LJO https://github.com/amyoun01/boreal_wildfire_feedbacks/archive/refs/heads/main.zip
$ unzip boreal_wildfire_feedbacks-main.zip

$ bash boreal_wildfire_feedbacks-main/run_analysis.sh

```


This project was funded by the USGS National Climate Adaptation Science Center, 
Award number XXXX to T. Scott Rupp at the University of Alaska Fairbanks.  
