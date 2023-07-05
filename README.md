# offshore_LCOE
Student Project to estimate LCOE and Energyharvest for offshore windturbines in Germany

## How to use
Git Clone Repository to your local machine and with Conda install Packages from `environment.yml`

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
5. Check for the downloaded Filename and install via `bash Anaconda3-2018.12-Linux-x86_64.sh` (replace with downloaded Filename)
6. `conda install git`
7. `git clone https://github.com/FelixMau/offshore_LCOE.git`
8. conda install pip
9. `conda env create -f environment.yml`
10. conda activate LCOE
11. `streanlit run offshore_LCOE/scitps/visualization.py` (make sure to include typo in visualization)

## Used tools

### [Atlite](https://atlite.readthedocs.io/en/latest/)
- Wind resource assessment: It provides functions to estimate the wind resource at a specific location using wind speed time series data.
- Moreover provides integrated functionality to download and process [ERA5](https://cds.climate.copernicus.eu/cdsapp#!/dataset/reanalysis-era5-single-levels?tab=form) weather data from Copernicus Earth observatio
- Turbine power curves: It includes models to represent the power output of different wind turbine types based on their power curves.
- Does not provide functionality to asses Wind parks ([Windpowerlib](https://github.com/oemof/feedinlib) could be used for that purpose) 

### [Geopandas](https://geopandas.org/en/stable/)
- Provides Geospatial functionality (additionally to Atlite)
- Extended Dataprocessing from Pandas

