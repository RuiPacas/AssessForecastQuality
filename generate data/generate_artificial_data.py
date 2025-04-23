import pandas as pd
import numpy as np
import os

actual_quantity = 100
number_of_weeks = 40
number_of_models = 5
number_of_parts = 1000
number_of_subparts = 5

distance_penalty = 0.5

ics_penalty = 0.1
penalty_per_ic = {
    "0": 0,
    "1": 0.1 * ics_penalty,
    "2": 0.2 * ics_penalty,
    "3": 0.3 * ics_penalty,
    "5": 0.5 * ics_penalty,
    "8": 0.8 * ics_penalty,
    "13": 1.2 * ics_penalty,
}
ics_probability = {
    "0": 0.30,
    "1": 0.20,
    "2": 0.15,
    "3": 0.15,
    "5": 0.1,
    "8": 0.05,
    "13": 0.05,
}
ics = []
for key in ics_probability.keys(): 
    for i in range(int(ics_probability[key] * 100)):
        ics.append(key)

color_penalty = 1.5
colors_probability = {
    "": 0.60,
    "RED": 0.10,
    "GREEN": 0.10,
    "BLUE": 0.10,
    "GRAY": 0.10,
}
colors = []
for key in colors_probability.keys():
    for i in range(int(colors_probability[key] * 100)):
        colors.append(key)

index_penalty = 0.1
index_probability = {
    "0": 0.25,
    "1": 0.25,
    "2": 0.25,
    "3": 0.25,
}
indexes = []
for key in index_probability.keys():
    for i in range(int(index_probability[key] * 100)):
        indexes.append(key)


models = []
model_forecasts = {}
for i in range(number_of_models):
    while True : 
        model_id = ''.join(np.random.choice(list('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890'), 3))
        if model_id not in models:
            models.append(model_id)
            model_forecasts[model_id] = {}
            break

used_part_ids = {}
def generate_part_and_subparts(model_id):
    part_id = ''.join(np.random.choice(list('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890'), 10))
    while True:
        part_id = ''.join(np.random.choice(list('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890'), 10))
        if(part_id not in used_part_ids[model_id]):
            used_part_ids[model_id].append(part_id)
            break

    subparts = []
    for _ in range(number_of_subparts):
        while True:
            [color] = np.random.choice(colors, 1)
            [index] = np.random.choice(indexes, 1)
            [ic] = np.random.choice(ics, 1)
            subpart = {"color": color, "index": index, "ics": ic}
            if subpart not in subparts:
                subparts.append(subpart)
                break
    return part_id, subparts

# generate number_of_parts parts per model
parts_per_model = {}

for model in models:
    parts_per_model[model] = []
    used_part_ids[model] = []
    for i in range(number_of_parts):
        part_id, subparts = generate_part_and_subparts(model)
        for subpart in subparts:
            parts_per_model[model].append({ "partCodeId": f"{part_id}{subpart["index"]}{subpart["color"]}", "vehicleModelId": model, "year": 2025, "week": 1, "actualQuantity": actual_quantity, "dfQuantity": None,  "numberOfInstallationConditions": subpart["ics"] })


all_forecasts = []
for model in models:
    for forecast_week in range(1, number_of_weeks + 1):
        model_forecasts[model][forecast_week] = [] 
        for week in range(forecast_week, number_of_weeks + 1):
            distance = week - forecast_week
            [df_forecast] = np.random.normal(actual_quantity, distance_penalty * (distance + 1), 1)
            week_forecast_for_model = { "partCodeId": "model" + model,  "vehicleModelId": model, "numberOfInstallationConditions": None, "year": 2025, "week": week, "dfQuantity": df_forecast, "actualQuantity": actual_quantity, "forecastWeek": forecast_week, "forecastDistance": distance }
            all_forecasts.append(week_forecast_for_model)
            for part in parts_per_model[model]:
                [color_factor] = np.random.normal(1, color_penalty if len(part["partCodeId"]) > 11 else 0  , 1)
                [index_factor] = np.random.normal(1, index_penalty if part["partCodeId"][10] in ['1','2','3'] else 0, 1)
                [ic_factor] = np.random.normal(1, penalty_per_ic[str(part["numberOfInstallationConditions"])], 1)
                all_factors = color_factor * index_factor * ic_factor
                part_df = df_forecast * all_factors
                part_with_df = { "partCodeId": part["partCodeId"], "vehicleModelId": part["vehicleModelId"], "year": 2025, "week": week, "actualQuantity": actual_quantity, "dfQuantity": part_df,  "numberOfInstallationConditions": part["numberOfInstallationConditions"], "forecastWeek": forecast_week, "forecastDistance": distance}
                all_forecasts.append(part_with_df)



df = pd.DataFrame(all_forecasts, columns=["partCodeId", "vehicleModelId", "numberOfInstallationConditions", "year", "week", "dfQuantity", "actualQuantity", "forecastWeek", "forecastDistance"])

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
