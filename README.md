## Overview

This is a simple Python Flask web app that estimates daily calorie needs
for weight maintenance and weight loss.

It supports multiple basal metabolic rate (BMR) formulas and converts results
to both kilocalories and kilojoules.

## Calculation Methodology

1. Basal Metabolic Rate (BMR) is calculated using one of the following formulas:
   - Mifflin-St Jeor
   - Revised Harris-Benedict (1984)
   - Katch-McArdle (lean body mass–based)

2. BMR is multiplied by an activity factor to estimate Total Daily Energy
   Expenditure (TDEE).

3. Weight loss targets use the common heuristic:
   - 1 lb ≈ 3,500 kcal
   - 1 lb/week ≈ 500 kcal/day deficit

4. Metric targets are converted from kg/week to lb/week before calculating
   daily calorie deficits.

## Disclaimer

This calculator provides estimates only and is not medical advice.

Results are based on population averages and simplified metabolic equations.
Individual energy needs may vary.

Do not use this tool as a substitute for professional medical or nutritional
guidance.
