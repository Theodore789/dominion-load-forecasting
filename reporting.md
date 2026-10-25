1) Combined the 17 files into one table of hourly Domininion demand and saved it, indexed by UTC time.

2) We want the PJM grid operator's Dominion zone (code DOM) which covers most of Viriginia and contains the data-centre cluster.
    Balancing Authority --> PJM, Sub-Region --> DOM

3) Loop opens each file, keeps only the Dominion rows and puts them in a list, "pd.concat" then stacks the 17 pieces into 1 table.

4) Turned the column "UTC Time at End of Hour" into real dates with "pd.to_datetime", made it the index and sorted by it. 
        With "format=" I tell pandas exactly how the dates are written.

5) From 1 July 2018 05:00 UTC to 17 October 2026 there are 72,720 rows. 
    With "count()" we counted 70,700 so 2,020 rows have a timestamp but an empty demand value.

6) EIA says DOM's highest winter peak on record in 2025-26 was 25,413MW.

7) 30,000 MW threshold is the first cleaning rule: "d[d > 30000] = None".

8) "gaps =" counts the missing hours: scattered hours(easy to fill) or long blocks(safer to drop).

9) missing hours --> fill,
   long blocks --> drop

10) Caught 2 more missing hours: 19 October 2021 at 03:00 and 04:00 UTC
    ,total: 2,022 missing hours.

    Documented: 
        1st: 5 gaps of 1-2 hours, 
        2nd: 13 gaps of 23, 24, 25 hours --> the 23-hour and 25-hour ones are daylight-saving days because EIA reports in Virginia's local time;
        3d: 1 gap of 1,704 hours; 71 days in a row with no data.

11) Next, we find where the long gaps are:
    "gap_id =",
    "summary =",
    "print()":
     the first and last hour and length of every gap of a day or longer.

12) Demand is rising (temperature-demand scatter plot):
        peak of 20219 --> 20,000 MW, peak of 2026 --> 25,413 MW.
    
    The plot floor is rising even faster:
        lowest nigh-time hours from 7,500 MW to 12,000 MW;
        this is demand that never switches off by data-centres working 24/7.

    Every year has 2 peaks: winter heating and summer cooling.

13) The 71-day gap is at the very start, from 9 July to 18 September 2018.
    We fix that by starting the data on October 1st 2018.
    
    Most whole-day gaps fall on the November clock-change day:
        2018, 2019, 2023, 2024, 2025;
        it's a recurring EIA reporting fault.
    
    The October 2026 gap will be cut off when we stop the data at 30 September.

14) With "load = load.loc["2018-10-01":"2026-09-30"]" we skip the long gap of       July-September 2018 and then stop at the last full month which is September 2026.

15) We have 288 hours missing in total which is 12 whole days: 
    7 November clock-change days, 4 in March and in August 2nd of 2020.

16) Working on the weather data:
    Open-Meteo moved each point to the nearest ERA5 grid cell which is about 25km across:
        39.0/-77.5 --> Ashburn(data-centre hub),
        37.5/-77.5 --> Richmond,
        36.75/-76.25 --> Norfolk

17) ".pivot": 
    before --> 1 row per location per hour, after --> 1 row per hour and one column per location.

    ".join" matches demand and temperature by timestamp and "how='left'" keeps every demand hour.

    We joined the demand and time for simplification because 
        demand is labelled by the end of each hour (see dom_load_clean.csv)
        and temperature is a reading at that moment (see weather.csv).

18) Temperature-demand scatter plot:
        demand rises when it's cold (need heating)
        and when it's hot (need cooling).

    The different color by year shows each year's U sitting higher thant the last.

19) Temperature-demand scatter plot key points:

        The bottom of the U rises from about 7,500 MW to about 13,000 MW.

        At around 15°C nobody heats or cools much, so demand there is weather-dependent load.

        The base-line grew by roughly 5,000 MW.

        The whole U moves up by about the same amount everywhere.
        Peaks rose by roughly 5,000 MW too.

        A shift that is added(the same MW at every temperature) rather than multiplied
        (the same percentage) shows that the experiment should express load as a difference from recent levels, not ratio.

20) Line plot:
        local time makes "hour 3" mean 3 am in Virginia.

        2018 and 2026 are partial years and 2018 is mostly winter so it would distort the shape. 
        
        We take years 2019-2025 with len(range()).

        Dividing by each year's mean removes the growth so we compare only the shape 
        of each year.

        If the night lines rise towards 1 over the year, the daily profile is flattening.

        The 3-4 am trough rises every year, from 0.83 of the daily mean in 2019
        to 0.89 in 2025 while the evening peak falls from 1.13 to 1.10. 
        
        The order is steady from year to year.
        

21) The training data peaks at 22,415 MW.
        389 test hours or 1.6% of the test data are above that.
            These are exactly the record peaks that matter to most grid operators.
            Because there are only 389 of them the overall MAE may barely move in the experiment, while the errors on those hours could be large.

        On average, each hour of the 389 exceeds 22,415 MW by approximately 863 MW.
            
            train max (2018-2022) --> 22,415 MW
            test hours (2024-2026) higher than train max --> 389 hours
            mean, average difference between test and train --> 0.0161
        
22) Using random forests, we will try to predict the mean output of these 389 hours which is about:
        
        863.3804627249357 MW