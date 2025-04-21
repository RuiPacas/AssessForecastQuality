import pandas as pd
import numpy as np
import sys
import argparse
import os

parser = argparse.ArgumentParser()
parser.add_argument('--actualQuantity', '-a', help="Actual Quantity, default = 700", type= int, default=700, required= False)
parser.add_argument('--numberOfWeeks', '-w', help="Number of Weeks, default = 40", type= int, default=40, required= False)
parser.add_argument('--numberOfModels', '-nm', help="Number of Models, default = 5", type= int, default=5, required= False)
parser.add_argument('--numberOfParts', '-p', help="Number of parts per model, default = 750", type= int, default=750, required= False)
parser.add_argument('--numberOfSubparts', '-sp', help="Max number of subparts per part (different colors, index, ics), default = 5", type= int, default=5, required= False)
parser.add_argument('--icsPenalty', '-ics', help="Installation Conditions penalty, default = 1", type= int, default=1, required= False)
parser.add_argument('--colorPenalty', '-c', help="Color Penalty, default = 1", type= int, default=1, required= False)
parser.add_argument('--indexPenalty', '-idx', help="Index penalty, default = 1", type= int, default=1, required= False)

args = parser.parse_args()
actual_quantity = args.actualQuantity
number_of_weeks = args.numberOfWeeks
number_of_models = args.numberOfModels
number_of_parts = args.numberOfParts
number_of_subparts = args.numberOfSubparts

ics_penalty = args.icsPenalty
penalty_per_ic = {
    "0": 1 * ics_penalty,
    "1": 2 * ics_penalty,
    "2": 3 * ics_penalty,
    "3": 4 * ics_penalty,
    "5": 5 * ics_penalty,
    "8": 6 * ics_penalty,
    "13": 7 * ics_penalty,
}

color_penalty = args.colorPenalty
index_penalty = args.indexPenalty

models = []
model_forecasts = {}
for i in range(number_of_models):
    while True : 
        model_id = ''.join(np.random.choice(list('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890'), 3))
        if model_id not in models:
            models.append(model_id)
            model_forecasts[model_id] = {}
            break

# for each week, create forecast for each model
for i in range(number_of_models):
    model_forecasts[models[i]][1] = [] 
    for j in range(1, number_of_weeks + 1):
        n_week_model_forecast = np.random.normal(actual_quantity, 200, number_of_models)
        model_forecasts[models[i]][1].append({ "partCodeId": "part" + models[i], "vehicleModelId": models[i], "numberOfInstallationConditions": None, "year": 2025, "week": j, "dfQuantity": n_week_model_forecast[0], "actualQuantity": actual_quantity, "forecastWeek": 1, "forecastDistance": j - 1 })

for forecast_week in range(2, number_of_weeks + 1):
    for i in range(number_of_models):
        model_forecasts[models[i]][forecast_week] = []
        for previous_part_df in model_forecasts[models[i]][forecast_week-1]:
            if(previous_part_df["week"] < forecast_week):
                continue
            n_week_model_forecast = np.random.normal(previous_part_df["actualQuantity"], 5 * (previous_part_df["week"] - forecast_week + 1), 1)
            model_forecasts[models[i]][forecast_week].append({ "partCodeId": previous_part_df["partCodeId"], "vehicleModelId": models[i], "numberOfInstallationConditions": None, "year": previous_part_df["year"], "week": previous_part_df["week"], "dfQuantity": n_week_model_forecast[0], "actualQuantity": previous_part_df["actualQuantity"], "forecastWeek": forecast_week, "forecastDistance": previous_part_df["week"] - forecast_week })


# generate number_of_parts parts per model
parts_per_model = {}
for model in models:
    parts_per_model[model] = []
    for i in range(number_of_parts):
        part_id = ''.join(np.random.choice(list('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890'), 10))
        while part_id in parts_per_model[model]: 
            part_id = ''.join(np.random.choice(list('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890'), 10))
        for j in range(number_of_subparts):
            while True:
                can_add = True
                [color] = np.random.choice(['', '', '', 'RED', 'GREEN', 'BLUE', 'GRAY'], 1)
                [index] = np.random.choice([' ', ' ', ' ', '1', '2', '3'], 1)
                [ics] = np.random.choice(['0', '1', '2', '3', '5', '8', '13'], 1)
                for part in parts_per_model[model]:
                    if part["partCodeId"][:10] == part_id and part["partCodeId"][10:11] == index and part["partCodeId"][11:] == color and part["numberOfInstallationConditions"] == ics:
                        can_add = False
                    else:
                        can_add = True
                if can_add:
                    parts_per_model[model].append({ "partCodeId": f"{part_id}{index}{color}", "vehicleModelId": model, "year": 2025, "week": 1, "actualQuantity": actual_quantity / len(ics), "dfQuantity": None,  "numberOfInstallationConditions": ics })
                    break

# Create first forecast 
all_parts_with_forecast = {1: []}
for model in models:
    for model_forecast in model_forecasts[model][1]:
        week = model_forecast["week"]
        actual_quantity_per_subpart = model_forecast["actualQuantity"] / number_of_subparts
        part_factor_per_subpart = model_forecast["dfQuantity"] / number_of_subparts

        for part in parts_per_model[model]:
            color_factor = np.random.normal(part_factor_per_subpart, color_penalty if len(part["partCodeId"]) > 11 else 3  , 1)
            index_factor = np.random.normal(part_factor_per_subpart, index_penalty if part["partCodeId"][10] in ['1','2','3'] else 3, 1)
            ic_factor = np.random.normal(part_factor_per_subpart, penalty_per_ic[str(part["numberOfInstallationConditions"])], 1)
            all_factors = (color_factor + index_factor + ic_factor) / 3
            part = { "partCodeId": part["partCodeId"], "vehicleModelId": part["vehicleModelId"], "year": 2025, "week": week, "actualQuantity": actual_quantity_per_subpart, "dfQuantity": all_factors[0],  "numberOfInstallationConditions": part["numberOfInstallationConditions"], "forecastWeek": 1, "forecastDistance": week - 1}
            all_parts_with_forecast[1].append(part)

# create subsequent forecasts for the rest of the weeks, taking the previous into consideration
for forecast_week in range(2, number_of_weeks + 1):
    all_parts_with_forecast[forecast_week] = []
    for part in all_parts_with_forecast[forecast_week - 1]:
        if(part["week"] < forecast_week):
            continue
        for model_forecast in model_forecasts[part["vehicleModelId"]][forecast_week]:
            if model_forecast["week"] == part["week"]:
                part_factor_per_subpart = model_forecast["dfQuantity"] / number_of_subparts

                color_factor = np.random.normal(part_factor_per_subpart, color_penalty if len(part["partCodeId"]) > 11 else 3, 1)
                index_factor = np.random.normal(part_factor_per_subpart, index_penalty if part["partCodeId"][10] != ' ' else 3, 1)
                ic_factor = np.random.normal(part_factor_per_subpart, penalty_per_ic[str(part["numberOfInstallationConditions"])], 1)
                
                new_df = (color_factor + index_factor + ic_factor) / 3
                
                all_parts_with_forecast[forecast_week].append({ "partCodeId": part["partCodeId"], "vehicleModelId": part["vehicleModelId"], "year": 2025, "week": part["week"], "actualQuantity": part["actualQuantity"], "dfQuantity": new_df[0],  "numberOfInstallationConditions": part["numberOfInstallationConditions"], "forecastWeek": forecast_week, "forecastDistance": part["week"] - forecast_week })
                break
        



all_rows = []
for model in models:
    for forecast_week in range(1, number_of_weeks + 1):
        for model_forecast in model_forecasts[model][forecast_week]:
                all_rows.append(model_forecast)
for forecast_week in range(1, number_of_weeks + 1):
    for part in all_parts_with_forecast[forecast_week]:
        all_rows.append(part)

df = pd.DataFrame(all_rows, columns=["partCodeId", "vehicleModelId", "numberOfInstallationConditions", "year", "week", "dfQuantity", "actualQuantity", "forecastWeek", "forecastDistance"])

# delete  all folders inside the folder ./generate data/datasets/general and all files inside those folders
for root, dirs, files in os.walk("./generate data/datasets/general", topdown=False):
    for name in files:
        os.remove(os.path.join(root, name))
    for name in dirs:
        os.rmdir(os.path.join(root, name))
#write the dataframe to parquet in the folder ./datasets/general and partition it by vehicleModelId
df.to_parquet("./generate data/datasets/general", engine='pyarrow', partition_cols=["vehicleModelId"], index=False)

records_per_part = (number_of_weeks * (number_of_weeks +1)) / 2
print("Success, number of rows should be", (records_per_part * number_of_parts * number_of_models * number_of_subparts) + (records_per_part * number_of_models)) 