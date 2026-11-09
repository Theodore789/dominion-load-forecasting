# Sources:

1) U.S. Energy Information Administration (2026) Hourly Electric Grid Monitor (Form EIA-930): balancing authority sub-region data, six-month files. 

        Available at: https://www.eia.gov/electricity/gridmonitor/ 
        Accessed on: 18 October 2026

2) Zippenfenig, P. (2023) Open-Meteo.com Weather API [Computer software]. Zenodo. doi:10.5281/zenodo.7970649.

3) Hersbach, H. et al. (2020) ‘The ERA5 global reanalysis’, Quarterly Journal of the Royal Meteorological Society, 146(730), pp. 1999–2049. doi:10.1002/qj.3803.


# Cleaning (data_handling.py)

1) Combined the 17 files into one table of hourly Dominion demand and saved it, indexed by UTC time.

2) We want the PJM grid operator's Dominion zone (code DOM) which covers most of Virginia and contains the data-centre cluster.

        Balancing Authority --> PJM 
        Sub-Region --> DOM

3) Loop opens each file, keeps only the Dominion rows and puts them in a list, 
"pd.concat" then stacks the 17 pieces into 1 table.

4) Turned the column "UTC Time at End of Hour" into real dates with "pd.to_datetime", 
made it the index and sorted by it. 

    With "format=" I tell pandas exactly how the dates are written.

5) From 1 July 2018 05:00 UTC to 17 October 2026 there are 72,720 rows. 
    
    With "count()" we counted 70,700 so 2,020 rows have a timestamp but an empty demand value.

6) Highest hourly value in our cleaned EIA-930 data: 25,413 MW (winter 2025-26).

7) 30,000 MW threshold is the first cleaning rule: "d[d > 30000] = None".

8) gaps ≤ 2 h interpolated (method="time"); longer gaps left as NaN.

9) Caught 2 more missing hours: 19 October 2021 at 03:00 and 04:00 UTC (~1.5e9 MW, set to missing).
        
    Total missibg hours: 2,022 h

    Documented:

        1st: 5 gaps of 1-2 hours.

        2nd: 13 gaps of 23, 24, 25 hours --> 23-hour and 25-hour ones are
            daylight-saving days.
        because EIA reports in Virginia's local time.

        3rd: 1 gap of 1,704 hours; 71 days in a row with no data.

10) Listed the first hour, last hour and length of every gap ≥ 1 day (see 12).

11) Demand is rising (temperature-demand scatter plot):
        
            peak of 2019 --> 20,000 MW 
            peak of 2026 --> 25,413 MW.
    
    In percentage terms the plot floor is rising even faster:

        lowest night-time hours from 7,500 MW to 12,000 MW;
        this is consistent with always-on data-centre load.

    Every year has 2 peaks: winter heating and summer cooling.

12) The 71-day gap is at the very start, from 9 July to 18 September 2018. 

    We fix that by starting the data on October 1st 2018.
    
    Most whole-day gaps fall on the November clock-change day:
        2018, 2019, 2022, 2023, 2024, 2025;
        it appears to be a recurring reporting gap.
    
    The October 2026 gap was cut off when we stopped the data at 30 September.

    Start 1 October 2018, end 30 September 2026.

13) 7 November clock-change days (25 h each), 4 March clock-changes (23 h each), plus on the 2nd of August 2020 (24 hours) = 12 days = 288 h

14) ERA5 via the Open-Meteo Historical API, hourly temperature_2m, GMT:
    
        Open-Meteo moved each point to the nearest ERA5 grid cell which is about 25km across:
            39.0/-77.5 --> Ashburn (data-centre hub),
            37.5/-77.5 --> Richmond,
            36.75/-76.25 --> Norfolk

15) Joined on the same timestamp, which is a simplification: 
    
        Demand is the average over the hour ending at t, while the temperature is an instant reading at t (a limitation).


## Exploration

16) Temperature-demand scatter plot:

        Demand rises when it's cold (need heating) and when it's hot (need cooling).

        The different colour by year shows each year's U sitting higher than the last.

        The bottom of the U rises from about 7,500 MW to about 12,000 MW.

        At 15°C demand is the weather-independent (base) load.

        The base-line grew by roughly 5,000 MW.

        The whole U moves up by about the same amount everywhere.
        Peaks rose by roughly 5,000 MW too.

        A shift that is added (the same MW at every temperature) rather than multiplied (the same percentage) shows that the experiment should express load as a difference from recent levels, not ratio.

17) Line plot:

        hour 3 = 02:00-03:00 (hour-ending, see 22).

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

            Because there are only 389 of them the overall MAE may barely move in the experiment, 
            while the errors on those hours could be large.

        On average, each hour of the 389 exceeds 22,415 MW by approximately 863 MW.
            
            training max (2018-2022) --> 22,415 MW
            test hours (2024-2026) higher than the training max --> 389 hours
            the share of test hours above the training max --> 0.0161


# Features (features.py)

19) The fair fix for the data: min_periods=143

        level_7d --> the average demand over a past week (168 hours).

        min_periods = 143
        this tells pandas to compute the average anyway as long as we have at least 143 hours there.

        Our data are whole days so every day we keep has its night and its day so the average stays fair.

        143 hours = about 6 days so the average still works when one whole day is missing.

20) Why the difference target:

        We're predicting the difference, not the demand because Trees can't extrapolate above the training numbers.

        Instead of asking what will the demand be, we ask how far above or below last week's average will it be.

        Hence: forecast  = level_7d + predicted difference.
        The growth is carried by level_7d so the tree never has to extrapolate.

21) NaN counts in level_7d:

        min_periods = 168 (7 days) --> 2483 NaNs
        min_periods = 144 (6 days) --> 887 NaNs
        min_periods = 143 (about 6 days because of the 25 hour clock change days) --> 166 NaNs

        24 + 144 - 1 = row 167, so 167 NaNs.
        with 143: 24 + 143 - 1 = 166, all before 15 October 2018

22) Number of windows containing the whole gap:

        For 2024 and 2025 we got 144 NaN hours each around 4-11 November; 
        that's because of the US clock change where US clocks go back on the first Sunday of November.

        For our example: 168 - g + 1 = 144 --> g = 25, so the missing day in November is 25 hours long, not 24. 

        Window is w rows and a gap is g rows, the number of windows that contain the whole gap is w-g+1.

        Our missing days are Virginia local days and the day the clock goes back has 25 hours. 
        The March clock-change day has 23; that's why the total is still 288 = 12 x 24.

        With min_periods = 144, a window can lose at most 24 hours. A 25-hour gap leaves 143, one short, so we get a NaN.

        Fix: change min_periods = 143.


23) Our data is hour-ending so:

        hour = 8 means the hour 07:00-08:00 local time.

24) On holidays:

        On public holidays offices close, so demand looks like a weekend even on a weekday! 
        If we don't flag the holiday days the model thinks Christmas Day is a normal Wednessday and over-forecasts.

        Pandas has a ready-made list of US federal holidays.

        Oct-Dec 2018 --> 4 holidays
        2019 and 2020 --> 10 + 10 = 20 holidays
        2021-2025 --> 5 * 11 = 55 holidays
        Jan-Sept 2026 --> 7 holidays
        Total holidays: 86
        Total holiday hours: 86 * 24 = 2064

        4 Jul 2024 18:00 --> 1
        3 Jul 2024 18:00 --> 0

        Not all federal holidays cut load equally: e.g. Columbus Day and Veterans day.

25) On temperature features:

        A linear model can only draw straight lines in each feature so with temp_mean (data_handling.py) it can't bend.

        We create a column with the squared and then cubed temperature for our model to be able to draw a U-shaped curve.

        Example: a + b * temp + c * temp ** 2

        Why the cube: the square gives a symmetric U and the cube lets the heating side and the cooling side differ. 

        Although trees don't need this, our Tao Hong linear benchmark does and it uses up to the cube.

26) features.py checks:

        Both asserts pass so there's exactly one row per hour and shift(24) really goes 24 h back.

        Lag check: 15 Jul 2024 12:00, lag_24 = 13,935

        Calendar check: 12:00 UTC --> hour 8(July, EDT) and hour 7(January, EST).

        Temperature check: 27.3 --> 745.29 --> 20,346.417

        Late add (8 Nov 26'): rel_ columns: df["lag_"] - df["level-7d"]

        Final table shape: 70,128 x 18.


## Modelling (modelling.py)  

27) Day D = Virginia local day. We are going to be using the local day because all our calendar features, holidays and missing days are in local time already. A grid operator also plans in local days.

28) lag_168, which is "the same hour last week", can't react when the weather changes;
sudden cold weather after a mild week last week gives errors of thousands of MWs, and a holiday a week prior spoils the next week's forecast too.


## Baselines for the models

29) Seasonal naive on validation 2023 (8,664 h), scored:

        MAE --> 1236,68 MW 
        RMSE --> 1719,55 MW 
        MAPE --> 9.17 % 
        ME --> -40.67 MW  
        MAE_top5 --> 1901,80 MW 

        Under-forecast (our result from the ME):

        Error = actual - forecast ("y - pred", modelling.py).
        On ME: we get a negative value which means that the baseline is ~ -40.66 MW which indicates a slight over-forecast of about 40.66 MW.

        Over-forecast:

        If we had chosen to display the error as Error = forecast - actual, our ME value would then be positive: 40.66 MW, an indication of a small under-forecast.
        
30) Tao Hong vanilla linear model predictions:

        MAE --> 396.28 MW 
        RMSE --> 521.26 MW 
        MAPE --> 2.97 % 
        ME --> 140.91 MW 
        MAE_top5 --> 610.66 MW 


## Raw tree model parameters and results for the top run

31) Parameters and results for the raw model:

Top run:

        Parameters:

        max_iter=400, 
        learning_rate=0.06                          
        early_stopping=False, 
        random_state=0
        
        Results: 

        MAE --> 717.37 MW       
        RMSE --> 854.84 MW      
        MAPE --> 5.39 %        
        ME --> 676.21 MW       
        MAE_top5 --> 855.27 MW   

Other top runs (only parameters):

        max_iter=100 with learning_rate=0.05
        max_iter=100 with learning_rate=0.06
        max_iter=300 with learning_rate=0.06
        max_iter=400 with learning_rate=0.05

32) Raw-target trees under-forecast validation by 668 MW on average(ME ≈ MAE): 
out-of-range behaviour appears per region of feature space (!), not only above
the global maximum.


## Results on validation (2023 of 8,664 scored hours)

Error = actual − forecast, so positive ME = under-forecast. All models are scored on the same hours.

| Model | MAE (MW) | RMSE (MW) | MAPE (%) | ME (MW) | MAE_top5 (MW) |
|---|---|---|---|---|---|
| Seasonal naive (lag_168) | 1,236.68 | 1,1719.55 | 9.17 | −40.67 | 1,901.80 |
| Tao Hong linear | **396.28** | **521.26** | **2.96** | +140.91 | **610.66** |
| Trees, arm A (raw) | 717.37 | 854.84 | 5.39 | +676.21 | 855.27 |
| Trees, arm B (difference target) | 737.18 | 875.61 | 5.54 | +685.05 | 858.58 |
| Trees, arm C (difference target + relative features) | 482.67 | 642.40 | 3.60 | +152.30 | 613.49 |


## Experiment arms

All arms: same settings (max_iter 400, learning_rate 0.06, early_stopping False, random_state 0), same calendar and weather features (hour, day_of_week, month, is_holiday, temp_mean), same scored hours.
Arm A was refitted on fit_rows.

| Arm | Target the trees learn | Load features | Forecast | Val. ME (MW) | Question it answers |
|---|---|---|---|---|---|
| A (reference) | demand (MW) | lag_24, lag_48, lag_168, level_7d (absolute MW) | tree output | +676 | — |
| B (pre-registered) | d = demand − level_7d | same as A (absolute MW) | level_7d + predicted d | +685 | Does changing only the target remove the bias? **No** |
| C (amendment, 8 Nov) | d = demand − level_7d | rel_24, rel_48, rel_168 (lag − level_7d); no level_7d | level_7d + predicted d | +152 | Does making the features relative remove it? **Mostly: −77%** |


33) Arms comparison:

        B vs A: changing the target alone is of no consequence:

                +668 MW --> +685 MW

        C vs B: removing the absolute level from the inputs is what removes the bias:

                +685 MW --> +152 MW

34) Arm B evidence:

        Mean predicted difference target: -698 MW
        
        Mean actual difference target: -13 MW

        The trees expected a drop that never came, which accounts for almost all of 
        Arm B's +685 bias.

35) On our hypothesis MAE prediction number (< 5 % change):

        The actul result is that the MAE fell 32 %. 


## Results on monthly validation -only ME- (2023 of 8,664 scored hours)

|   local month |   linear |   A_raw |   B_diff_target |   C_relative |
|--------------:|---------:|--------:|----------------:|-------------:|
|             1 |   141.84 | 1080.58 |         1056.26 |       425.82 |
|             2 |    24.1  |  869.19 |          913.43 |       481.79 |
|             3 |   177.89 |  773.31 |          771.03 |       129.92 |
|             4 |   284.77 |  398.82 |          348.24 |       -50.47 |
|             5 |   207.37 |  580.82 |          610.45 |       142    |
|             6 |    68.16 |  742.76 |          782.13 |       447.27 |
|             7 |   264.02 |  669.58 |          755.06 |        82.75 |
|             8 |   104.27 |  543.57 |          510.75 |       -31.93 |
|             9 |    89.95 |  533.09 |          544.33 |       -64.63 |
|            10 |    11.4  |  666.78 |          616.45 |        58.33 |
|            11 |    90.55 |  668.2  |          697.69 |        87.98 |
|            12 |   213.36 |  600.49 |          631.26 |       138.87 |

Arm C cut the tree's bias by 77% and their MAE by 32%, but on validation
the interpretable linear benchmark is still the most accurate model. 

The linear model's trend term handles growth "for free", while the trees need careful
engineering just to catch up. 


## Results on the fair monthly comparison -only MAE- (val on 2023 of 8,664 scored hours)

|   local month |   linear |   A_raw |   B_diff_target |   C_relative |
|--------------:|---------:|--------:|----------------:|-------------:|
|             1 |   377.54 | 1102.04 |         1083.31 |       740.11 |
|             2 |   369.3  |  879.5  |          921.6  |       702.17 |
|             3 |   418.53 |  793.76 |          790.64 |       485.99 |
|             4 |   431.89 |  479.77 |          450.36 |       321.99 |
|             5 |   372.37 |  591.26 |          626.35 |       310.42 |
|             6 |   459.14 |  760.42 |          802.25 |       541.74 |
|             7 |   428.69 |  698.6  |          792.73 |       423.51 |
|             8 |   392.29 |  653.76 |          670.1  |       610.87 |
|             9 |   407.67 |  638.5  |          655.94 |       512.89 |
|            10 |   304.11 |  675.32 |          634.28 |       246    |
|            11 |   389.42 |  680.58 |          708.1  |       437.64 |
|            12 |   406    |  663.04 |          719.06 |       473.49 |


# MLP model

The MLP  was trained on Arm C and it uses it's representation, which is the best tree design on validation.


## MLP results and parameters -reference: Arm C MAE --> 482.67 MW

        1st run:

                Parameters:
                range(5)
                
                hidden_layer_sizes=(64, 32)
                alpha=1e-3
                max_iter=200
                early_stopping=False
                random_state=seed

                Results:
                MLP mean --> 556 MW (556.98)
                MLP standard deviation --> 4 MW (4.67)
                MAE 556 ± 4 MW


        2nd run -Prediction: 400 iterations with all other parameters fixed (1st run) will improve MAE by more than 20 MW

                Parameters changed:
                max_iter=200 -> max_iter=400

                Results:
                MAE 575.55 ± 10.20 MW --> worse than the 1st run by ~19 ± 14.20 MW, so our prediction was off


        3rd run -Prediction: alpha=1e-2 with all other parameters fixed (1st run) will improve MAE by more than 20 MW
                
                Parameters changed:
                alpha=1e-3 -> alpha=1e-2

                Results:
                MAE 554.89 ± 13.66 MW --> better than the 1st run by ~2 ± 17 MW, so our prediction was off


        4th run -Prediction: 1 only loop with all other parameters fixed (1st run) will improve MAE by more than 20 MW
                
                Parameters changed:
                range(5) -> range(1)

                Results:
                MAE 553.65 ± 0 MW --> better than the 1st run by ~3 ± 4 MW, so our prediction was off


## Final model table

|               |     MAE |    RMSE |   MAPE |     ME |   MAE_top5 |
|:--------------|--------:|--------:|-------:|-------:|-----------:|
| naive         | 1236.68 | 1719.55 |   9.17 | -40.67 |    1901.8  |
| linear        |  396.28 |  521.26 |   2.97 | 140.91 |     610.66 |
| A_raw         |  717.37 |  854.84 |   5.39 | 676.21 |     855.27 |
| B_diff_target |  737.18 |  875.61 |   5.54 | 685.05 |     858.58 |
| C_relative    |  482.67 |  642.4  |   3.6  | 152.3  |     613.49 |
| MLP_C_s0      |  553.32 |  744.24 |   4.14 | 183.22 |     681.74 |
| MLP_C_s1      |  564.87 |  755.31 |   4.23 | 201.03 |     664.2  |
| MLP_C_s2      |  557.38 |  744.2  |   4.17 | 104.95 |     699.63 |
| MLP_C_s3      |  553.95 |  743.11 |   4.15 | 104.07 |     632.25 |
| MLP_C_s4      |  555.43 |  747.15 |   4.16 | 103.3  |     612.81 |


# Final findings
        
        The relative representation (Arm C) works for neural networks as well.

         On our general problem, an interpretable model with the right structure (trend + temperature x month / hour) beats flexible models that have to **learn** that structure from about 4 years of data.


# References

Géron, A. (2017) Hands-On Machine Learning with Scikit-Learn and TensorFlow 1st edn. Sebastopol, CA: O’Reilly, pp. 195–199.   

Murphy, K.P. (2012) Machine learning: a probabilistic perspective. Cambridge, MA: MIT Press, pp. 543–563: trees and boosting.

MacKay, D.J.C. (2003) Information theory, inference, and learning algorithms. Cambridge: Cambridge University Press, pp. 527–533: MLPs.

Hong, T. et al. (2020) ‘Energy Forecasting: A Review and Outlook’, IEEE Open Access Journal of Power and Energy, 7, pp. 376–388. Available at: https://doi.org/10.1109/OAJPE.2020.3029979.