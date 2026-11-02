## Cleaning (data_handling.py)
     Sources:

        https://www.eia.gov/electricity/gridmonitor/dashboard/electric_overview/US48/US48

         https://open-meteo.com/en/docs/historical-weather-api

1) Combined the 17 files into one table of hourly Dominion demand and saved it, indexed by UTC time.

2) We want the PJM grid operator's Dominion zone (code DOM) which covers most of Virginia and contains the data-centre cluster.

    Balancing Authority --> PJM 
    Sub-Region --> DOM

3) Loop opens each file, keeps only the Dominion rows and puts them in a list, "pd.concat" then stacks the 17 pieces into 1 table.

4) Turned the column "UTC Time at End of Hour" into real dates with "pd.to_datetime", made it the index and sorted by it. 

    With "format=" I tell pandas exactly how the dates are written.

5) From 1 July 2018 05:00 UTC to 17 October 2026 there are 72,720 rows. 
    With "count()" we counted 70,700 so 2,020 rows have a timestamp but an empty demand value.

6) EIA says DOM's highest winter peak on record in 2025-26 was 25,413MW.

7) 30,000 MW threshold is the first cleaning rule: "d[d > 30000] = None".

8) gaps ≤ 2 h interpolated (method="time"); longer gaps left as NaN.

9) Caught 2 more missing hours: 19 October 2021 at 03:00 and 04:00 UTC
        
    Total missibg hours: 2,022 h, ~1.5e9 MW.

    Documented:

        1st: 5 gaps of 1-2 hours.

        2nd: 13 gaps of 23, 24, 25 hours --> the 23-hour and 25-hour ones are daylight-saving days because EIA reports in Virginia's local time.

        3rd: 1 gap of 1,704 hours; 71 days in a row with no data.

10) Listed the first hour, last hour and length of every gap ≥ 1 (see 13).

11) Demand is rising (temperature-demand scatter plot):
        
        peak of 2019 --> 20,000 MW 
        peak of 2026 --> 25,413 MW.
    
    In percentage terms the plot floor is rising even faster:
        lowest night-time hours from 7,500 MW to 12,000 MW;
        this is consistent with always-on data-centre load.

    Every year has 2 peaks: winter heating and summer cooling.

12) The 71-day gap is at the very start, from 9 July to 18 September 2018. We fix that by starting the data on October 1st 2018.
    
    Most whole-day gaps fall on the November clock-change day:
        2018, 2019, 2023, 2024, 2025;
        it appears to be a reccuring reporting gap.
    
    The October 2026 gap was cut off when we stopped the data at 30 September.

    Start 1 Oct 2018, end 30 Sept 2026.

13) 7 November clock-change days, plus 2 Aug 2020:

        70,128 hours, 288 missing demand and 0 missing temperatures

14) ERA5 via the Open-Meteo Historical API, hourly temperature_2m, GMT:
    
        Open-Meteo moved each point to the nearest ERA5 grid cell which is about 25km across:
            39.0/-77.5 --> Ashburn(data-centre hub),
            37.5/-77.5 --> Richmond,
            36.75/-76.25 --> Norfolk

15) Joined on the same timestamp, which is a simplification: demand is the avarage over the hour ending at t, while the temperature is an instant reading at t (a limitation).

## Exploration

16) Temperature-demand scatter plot:

        Demand rises when it's cold (need heating) and when it's hot (need cooling).

        The different color by year shows each year's U sitting higher than the last.

        The bottom of the U rises from about 7,500 MW to about 12,000 MW.

        At 15°C demand is the weather-independent (base) load.

        The base-line grew by roughly 5,000 MW.

        The whole U moves up by about the same amount everywhere.
        Peaks rose by roughly 5,000 MW too.

        A shift that is added(the same MW at every temperature) rather than multiplied
        (the same percentage) shows that the experiment should express load as a difference from recent levels, not ratio.

17) Line plot:

        hour 3 = 02:00-03:00 (hour-ending, see 27).

        2018 and 2026 are partial years and 2018 is mostly winter so it would distort the shape. 
        
        full years only: 2019-2025.

        Dividing by each year's mean removes the growth so we compare only the shape 
        of each year.

        If the night lines rise towards 1 over the years, the daily profile is flattening.

        The 3-4 am trough rises every year, from 0.83 of the daily mean in 2019
        to 0.89 in 2025 while the evening peak falls from 1.13 to 1.10. 
        
        The order is steady from year to year.
        
## Experiment facts

18) The training data peaks at 22,415 MW

        389 test hours or 1.6% of the test data are above that.

            These are exactly the record peaks that matter to most grid operators.

            Because there are only 389 of them the overall MAE may barely move in the experiment, while the errors on those hours could be large.

        On average, each hour of the 389 exceeds 22,415 MW by approximately 863 MW.
            
            training max (2018-2022) --> 22,415 MW
            test hours (2024-2026) higher than the training max --> 389 hours
            the share of test hours above the training max --> 0.0161
        
19) References for the modelling:

         Hands-On Machine Learning with Scikit-Learn & TensorFlow, Aurélien Géron pp. 195-199   

         Machine Learning: A Probabilistic Perspective, Kevin P. Murphy 
         pp. 543-563

         Information Theory, Inference, and Learning Algorithms, David J. C. MacKay pp. 527-533

## Features (features.py)

24) The fair fix for the data: min_periods=143

        level_7d --> the average demand over a past week (168 hours).

        min_periods = 144
        this tells pandas to compute the average anyway as long as we have at least 144 hours there.

        Our data are whole days so every day we keep has its night and its day so the average stays fair.

        143 hours = about 6 days so the average still works when one whole day is missing.

20) Why the difference target:

        We're predicting the difference, not the demand because Trees can't extrapolate above the training numbers.

        Instead of asking what will the demand be, we ask how far above or below last week's average will it be.

        Hence: forecast  = level_7d + predicted difference.
        The growth is carried by level_7d so the tree never has to extrapolate.

21) Expected 167 NaN but got 887, 720 extra.

        min_periods = 168 (7 days) --> 2483 NaNs
        min_periods = 144 (6 days) --> 887 NaNs
        min_periods = 143 (about 6 days because of the 25 hour clock change days) --> 166 NaNs

        24 + 144 - 1 = row 167, so 167 NaNs.

22) Number of windows containing the whole gap:

        Window is w rows and a gap is g rows, the number of windows that contain the whole gap is w-g+1.

        For our example: 168-g+1, so g = 25, so the missing day in November is 25 hours long, not 24. Our missing days are Virginia local days and the day the clock goes back has 25 hours. The March clock-change day has 23; that's why the total is still 288 = 12 x 24.

        With min_periods = 144, a window can lose at most 24 hours. A 25-hour gap leaves 143, one short, so we get a NaN.

        Fix: change min_periods = 143.

        For 2024 and 2025 we got 144 NaN hours each around 4-11 November; that's because of the US clock change where US clocks go back on the first Sunday of November.

23) Our data is hour-ending so:

        hour = 8 means the hour 07:00-08:00 local time.

24) On holidays:

        On public holidays offices close, so demand looks like a weekend even on a weekday! If we don't flag the holiday days the model thinks Christmas Day is a normal Wednessday and over-forecasts.

        Pandas has a ready-made list of US federal holidays.

        Oct-Dec 2018 --> 4 holidays
        2019 and 2020 --> 10 + 10 = 20 holidays
        2021-2025 --> 5 * 11 = 55 holidays
        Jan-Sept 2026 --> 7 holidays
        Total holidays: 86
        Total holiday hours: 86 * 24 = 2064

        4 Jul 2024 18:00 --> 1
        3 Jul 2024 18:00 --> 0

        Not all federal holidays cut load equally: e.g. Columbus day and Veterans day

25) On temperature features:

        A linear model can only draw straight lines in each feature so with temp_mean (data_handling.py) it can't bend.

        We create a column with the squared and then cubed temperature for our model to be able to draw a U-shaped curve

        Example: a + b * temp + c * temp ** 2

        Why the cube: the square gives a symmetric U and the cube lets the heating side and the cooling side differ. 

        Although trees don't need this, our Tao Hong linear benchmark does and it uses up to the cube.

26) features.py checks:

        Both asserts pass so there's exactly one row per hour and shift(24) really goes 24 h back.

        Lag check: 15 Jul 2024 12:00, lag_24 = 13,935

        Calendar check: 12:00 UTC --> hour 8(July, EDT) and hour 7(January, EST).

        Temperature check: 27.3 --> 745.29 --> 20,346.417

        Final table shape: 70,128 x 15.