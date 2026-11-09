# Experiment
    ## Question:
            Can gradient-boosted trees forecast demand above the highest load in their training data and does predicting load as a difference from the recent 7-day mean fix this?

    ## Known facts before running:
            Training maximum (October 2018 - December 2022) --> 22,415 MW
            
            Test hours (January 2024 - September 2026) above train_max --> 389 hours (1.6%) are higher than the train_max by approximately 863.38 MW. In other words, the test set contains 389 hours that each of them surpasses the train_max by 863 MW on average, averaging about 23,278 MW.

            Demand rose about 5,000 MW in total from 2019 to 2025.

    ## Prediction:
            On the 389 hours, raw-MW trees under-forecast by about 900 MW. The difference target reduces that bias by about 80%. 

            Overall test Mean Absolute Error (MAE) changes by less than 5%, because these hours account for only 1.6% of the test set.

    ## Reasoning:
            Decision Trees and standard Random Forests cannot exceed the training maximum because they are piecewise constant models that partition the input space into regional averages, rather than fitting a continuous equation.

            Gradient-boosted trees add many small, piecewise-constant trees that predict the errors of the previous step, allowing the cumulative sum to drift slightly past the original training boundaries, although each tree is flat beyond the range of its training inputs, so predictions cannot follow an upward trend.

            We will use the difference instead of the ratio because: 
                In the temperature-demand scatter plot, the U curve moved up by about 5,000 MW at all temperatures rather than stretching. 
                
                In the profile plot, the daily swings shrank relative to the mean, while a ratio model assumes the shape stays fixed. A flat block of data centre load on top makes this plot flatter.

    ## Design: 
           Gradient-boosted trees, raw vs difference target with a linear model as a comparison.

           Same features, hyperparameters and seeds for both versions.

           Training on --> Oct 2018 - Dec 2022
           Validate on --> 2023
           Test on --> Jan 2024 - Sept 2026

            Level --> mean load over the 7 days ending 24h before the target hour

    ## How I will judge it:
            ME and MAE on the 389 hours
            MAE on the top 5% of hours
            Overall MAE

            95% confidence interval for the MAE difference from a paired bootstrap over days.

            Supported if: 
                On the 389 hours, the difference model's mean under-forecast is at least 50% smaller than the raw model's and the 95% bootstrap interval for the MAE difference on those hours excludes 0.

            Partly supported if:
                The interval excludes 0 but the reduction is below 50%.

            Not supported if: 
                The interval includes 0 or the difference model is worse.

        ## 6 November 2026:
                Final models are trained on Oct 2018 - Dec 2022 only, while 2023 is used only for choosing settings. 
                
                As a secondary analysis, the linear and best tree models are also refitted on Oct 2018 - Dec 2023 and evaluated on the same test hours; this does not change the pre-registered test of our experiment.

        ## 8 November 2026:
                On validation data, the difference target with the same absolute features as the raw model did not reduce bias:

                Raw tree model --> ME: +668 MW
                Difference tree model --> ME: +685 MW (!) 

                Diagnosis:
                
                level_7d as a feauture confounds structural growth with multi-day weather spells. 
                
                An additional arm is therefore added (Arm C): difference target with load features expressed relative to level_7d (lag - level_7d) and level_7d removed as feature. 
                
                All three arms will be reported on the test set; the pre-registered arm is reported as registered.