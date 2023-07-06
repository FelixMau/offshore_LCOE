# offshore_LCOE
Student Project to estimate LCOE and Energyharvest for offshore windturbines in Germany

Within this Project an Streamlit app was 

## How to use
1. Git Clone Repository to your local machine and with Conda install Packages from `environment.yml`
2. Make sure to download all necesary data sets as in file structure [here](https://tubcloud.tu-berlin.de/s/oqJYaQwYFWtT9p3/download) (**Most datasets should be included since v0.1.2** but [weather data](https://tubcloud.tu-berlin.de/s/DYnHGnYR4389bY8/download/western-europe-2011.nc) needs to be added manually)    


To run the app open your Terminal 
- activate Conda environment with `conda activate LCOE`
- navigate to the scripts folder and run `streamlit run visualiozation.py`

Now the App should be running at a localhost statet within your Terminal. The Default Port is 8501. 
If there is no link shown open a Browser and type `localhost:8051`

### On Ubuntu Server
1. Setup your Server as you like with an IP that you know.
2. apt-upgrade to be shure to be up to date
3. Optional: Navigate to ./home and mkdir `yourdir` and cd into `yourdir`
4. Go to the [Conda website](https://docs.conda.io/en/latest/miniconda.html#linux-installers) and copy the link for the Conda version you like or use this (maybe outdated) Version
   wget https://repo.continuum.io/archive/Anaconda3-2018.12-Linux-x86_64.sh (if you want to use a newer Version just replace the link after wget. 
5. Check for the downloaded Filename and install via `sudo bash Anaconda3-2018.12-Linux-x86_64.sh` (replace with downloaded Filename)
6. sudo apt install python3
7. `sudo apt install git`
8. `git clone https://github.com/FelixMau/offshore_LCOE.git`
9. `cd offshore_LCOE/data` `mkdir weather` `cd weather` `wget https://tubcloud.tu-berlin.de/s/DYnHGnYR4389bY8/download/western-europe-2011.nc` `cd ..` `cd ..`
10. `conda install pip`
11. `conda env create -f environment.yml`
12. `conda activate LCOE`
13. `cd offshore_LCOE/data/weather`
14. `streamlit run offshore_LCOE/scitps/visualization.py` (make sure to include typo in visualization)

### Troubleshooting

If you are facing issues with our program, follow these steps to troubleshoot:
1. Look up the error message: When encountering an error, carefully read the error message and try to understand its cause. This can often provide valuable insights into the issue you're facing.
2. Check the documentation: Review the project documentation, including the instructions and any troubleshooting sections, to see if there are any specific solutions or workarounds for the problem you're experiencing.
3. Search for similar issues: Search online resources, such as forums or issue trackers, to see if others have encountered a similar problem. This can help you find potential solutions or workarounds shared by the community.
4. Create an issue: If you're still unable to resolve the issue, consider creating an issue in the project's repository. Clearly explain the problem you're facing, provide any relevant error messages or logs, and include steps to reproduce the issue if possible. This will help the project maintainers and the community understand the problem and provide assistance.
Please note that our application may be more challenging to install and run on Windows machines, and we might not be able to provide extensive support for Windows-specific issues. However, we will do our best to assist you within our capabilities.

## Used tools

### [Atlite](https://atlite.readthedocs.io/en/latest/)
- Wind resource assessment: It provides functions to estimate the wind resource at a specific location using wind speed time series data.
- Moreover provides integrated functionality to download and process [ERA5](https://cds.climate.copernicus.eu/cdsapp#!/dataset/reanalysis-era5-single-levels?tab=form) weather data from Copernicus Earth observatio
- Turbine power curves: It includes models to represent the power output of different wind turbine types based on their power curves.
- Does not provide functionality to asses Wind parks ([Windpowerlib](https://github.com/oemof/feedinlib) could be used for that purpose) 

### [Geopandas](https://geopandas.org/en/stable/)
- Provides Geospatial functionality (additionally to Atlite)
- Extended Dataprocessing from Pandas

