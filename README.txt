1. DATA
    
    - included: data/ (processed demand, weather, features, test forecasts)

    - raw EIA-930 files (~436 MB, not included), download by following these instructions:
    -> https://www.eia.gov/electricity/gridmonitor/dashboard/electric_overview/US48/US48 
    -> go to "DOWNLOAD DATA"
    -> select "SIX-MONTH FILES" 
    -> from the years 2018-2026 download every csv file with the description name "SUBREGION"
    -> total: 17 csv files

    - data/weather.csv: hourly 2 m temperature 
    (ERA5 via the Open-Meteo Historical Weather API) for Ashburn, Richmond and Norfolk; included.

    - Put the 17 files in ~/Desktop/EIA_hourly_demand/ (the path data_handling.py reads),
    then run data_handling.py

    - because data/ is included, you can start at features.py 



2. HOW TO RUN (in this order)
Run each script from inside code/, e.g. python modelling.py

    - data_handling.py -> data exploration, cleaning and preprocessing and 2 exploratory plots; close each plot window to continue.
        -- outputs: dom_load_clean.csv, dom_merged.csv

    - featres.py -> feautures necessary for the models: it produces the final csv table used for the models
        -- outputs: features.csv

    - modelling.py -> trains all models on Oct 2018-Dec 2022, selects settings on 2023, scors the test set,
    runs the pre-registered experiment and the secondary refit. Outputs: test_output.txt, secondary_output.txt, data/test_forecasts.csv.
    Note: rerunning it re-scores the test set (see reporting.md, 15 Nov)


    - figures.py -> produces the figures used in the report pdf
        -- outputs: figures/ fig1_demand.pdf, fig1_demand.png, fig2_temperature.pdf, fig2_temperature.png,
         fig3_rec_hours.pdf, fig3_rec_hours.png, fig4_ME.pdf, fig4_ME.png, figures_output.txt


    - check_forecasts.py -> checks test_forecasts.csv. It needs the git history (ac484f6), which is not in the ZIP;
    its result is in check_output.txt
       


3. SETUP

- Python 3.12
- matplotlib==3.11.2
- numpy==2.4.4
- pandas==3.0.2
- scikit-learn==1.9.1


4. OTHER FILES

 - hypothesis.md -> pre-registered hypothesis and decision rule, with the dated 8 Nov amendment (arm C)
 - reporting.md -> notes, results and observations for the project
 - test_output.txt, secondary_output.txt, test_forecasts.csv
 - figures_output.txt 
