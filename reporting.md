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

23) References for the modelling:

         Hands-On Machine Learning with Scikit-Learn & TensorFlow, Aurélien Géron pgs. 195-199   

         Machine Learning: A Probabilistic Perspective, Kevin P. Murphy 
         pgs. 543-563

         Information Theory, Inference, and Learning Algorithms, David J. C. MacKay pgs. 527-533


24) The fair fix for the data: min_periods=144.

        level_7d --> the average demand over a past week (168 hours).

        min_periods = 144
        this tells pandas to compute the average anyway as long as we have at least 144 hours there.

        Our data are whole days so every day we keep has its night and its day so the average stays fair.

        144 hours = 6 days so the average still works when one whole day is missing.

        We're predicting the difference, not the demand because Trees can't extrapolate above the training numbers.

        Instead of asking what will the demand be, we ask how far above or below last week's average will it be.

        Hence: forecast  = level_7d + predicted difference.
        The growth is carried by level_7d so the tree never has to extrapolate.

25) Expected 167 NaN but got 887, 720 extra.

        min_periods = 168 (7 days) --> 2483 NaNs
        min_periods = 144 (6 days) --> 887 NaNs
        min_periods = 143 (about 6 days becuase of the 25 hour clock change days) --> 166 NaNs

        24 rows lost to shift(24) then the window needs 144 real values. The first valid row is 24 + 144 - 1 = row 167, so 167 NaNs.

        Henceforth, some windows lose more than 24 hours. Either a gap is longer than one day or two missing days fall within the same week.

26) Number of windows containing the whole gap:

        Window is w rows and a gap is g rows, the number of windows that contain the whole gap is w-g+1.

        For our example: 168-g+1, so g = 25, so the missing day in November is 25 hours long, not 24. Our missing days are Virginia local days and the day the clock goes back has 25 hours. The March clock-change day has 23; that's why the total is still 288 = 12 x 24.

        With min_periods = 144, a window can lose at most 24 hours. A 25-hour gap leaves 143, one short, so we get a NaN.

        Fix: change min_periods = 143.

        For 2024 and 2025 we got 144 NaN hours each around 4-11 November; that's because of the US clock change where US clocks go back on the first Sunday of November.

27) Our data is hour-ending so:

        hour = 8 means the hour 07:00-08:00 local time.

28) On holidays:

        On public holidays offices close, so demand looks like a weekend even on a weekday! If we don't flag the holiday days the model thinks Christmas Day is a normal Wednessday and over-forecasts.

        Pandas has a ready-made list of US federal holidays.

        Oct-Dec 2018 --> 4 holidays
        2019 and 2020 --> 10 + 10 = 20 holidays
        2021-2025 --> 5 * 11 = 55 holidays
        Jan-Sept 2026 --> 7 holidays
        Total holidays: 86
        Total holiday hours: 86 * 24 = 2064
