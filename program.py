import cotede
from cotede import qctests, datasets

from tqdm import tqdm
import xarray as xr
import pandas as pd
import numpy as np
from Plotter import Plotter
import time
import os


def convert_to_int(value):
    try:
        return int(value)
    except ValueError:
        return np.nan


def get_data(ncfiles_path):
    data_list = []
    parent_index_count = 0
    for file in os.listdir(ncfiles_path):
        ds = xr.open_dataset(ncfiles_path + file)
        parent_index = np.repeat(np.arange(len(ds["depth_row_size"].values)), ds["depth_row_size"].values)
        data = {
            "depth": ds["depth"].values,
            "press": ds["press"].values,
            "temp": ds["temp"].values,
            "psal": ds["psal"].values,
            "parent_index": parent_index + parent_index_count,
            "year": np.repeat(
                np.array([convert_to_int(date[:4]) for date in ds["datestr"].values]),
                np.unique(parent_index, return_counts=True)[1],
            ),
            "lat": np.repeat(np.array(ds["lat"]), np.unique(parent_index, return_counts=True)[1]),
            "lon": np.repeat(np.array(ds["lon"]), np.unique(parent_index, return_counts=True)[1]),
        }
        parent_index_count += parent_index[-1] + 1
        data_list.append(data)
        ds.close()

    df = pd.concat((pd.DataFrame(data) for data in data_list), ignore_index=True)
    return df


def apply_qc(data: pd.DataFrame):
    ### setting configuration
    cfg = {
        "temp": {
            "global_range": {"minval": -2, "maxval": 40},
            "gradient": {"threshold": 10.0},
            "spike": {"threshold": 2.0},
            # "tukey53H": {"threshold": 1.5},
        },
        "psal": {
            "global_range": {"minval": 0, "maxval": 41},
            "gradient": {"threshold": 5.0},
            "spike": {"threshold": 0.3},
            # "tukey53H": {"threshold": 1.0},
        },
        # "depth": {"global_range": {"minval": 0, "maxval": 5000}},
    }

    print(data)
    pqc = cotede.ProfileQC(data, cfg='eurogoos')
    print(pqc.keys())
    print(pqc.flags)
    # print
    # print("-" * 100)
    # print(data)
    # print(f"flags: {pqc.flags["temp"]}")

    # t_flags = pqc.flags["temp"]["overall"]
    # t_flags = t_flags <= 2

    # print(data[t_flags])
    # return None

    # print(len(data['temp'][pqc.flags['temp']['overall'] <= 2]))
    good_idx_dict = {attr: pqc.flags[attr]["overall"] <= 2 for attr in ["temp", "psal"]}

    # if not all(good_idx_dict["temp"]) and not data["depth"].isnull().any():
    # print("data: " + "-" * 100)
    # print(data)
    # print("good idx dict temp: " + "-" * 100)
    # print(good_idx_dict["temp"])

    return good_idx_dict
    # return None


def submit_data_to_qc(df: pd.DataFrame):
    filtered_data = {attr: [] for attr in ["temp", "temp_depth", "psal", "psal_depth", "press"]}
    # df = df[["temp", "psal", "depth", "press", "parent_index"]]
    groups = df.groupby("parent_index")
    # break_condition = 0
    for _, group in tqdm(groups, colour="GREEN"):
        # data = group.reset_index()[["temp", "psal", "depth", "press"]]
        data = group.reset_index()

        # FIXME: remove NaN from temp - REMOVE THIS, JUST FOR TEST, YOU ARE EXCLUDING THE PSAL doing this!
        data = data[~data.loc[:, "temp"].isnull()]

        idx_dict = apply_qc(data)
        # raise ValueError("ZAP 3")

        qc_temp = data["temp"][idx_dict["temp"]]
        qc_temp_depth = data["depth"][idx_dict["temp"]]
        qc_psal = data["psal"][idx_dict["psal"]]
        qc_psal_depth = data["depth"][idx_dict["psal"]]

        filtered_data["temp"] = np.concatenate([filtered_data["temp"], qc_temp])
        filtered_data["temp_depth"] = np.concatenate([filtered_data["temp_depth"], qc_temp_depth])
        filtered_data["psal"] = np.concatenate([filtered_data["psal"], qc_psal])
        filtered_data["psal_depth"] = np.concatenate([filtered_data["psal_depth"], qc_psal_depth])

        # break
        # if break_condition == 20:
        #     break
        # break_condition += 1

    return filtered_data


def main(ncfiles_path):
    ### get all the data
    df = get_data(ncfiles_path)
    plotter = Plotter()

    # ### select a subset of the data
    df = df[df["year"] == 2008].reset_index()
    # df = df[df['parent_index'] == 35485].reset_index()

    ### plot original data
    for var in ["temp", "psal"]:
        plotter.plot_var_vs_depth(var, df[var], df["depth"], filename=f"{var}_vs_depth")

    ### QC the data
    filtered_data = submit_data_to_qc(df)

    ### plot good data only
    for var in ["temp", "psal"]:
        plotter.plot_var_vs_depth(
            var,
            var_list=filtered_data[var],
            depth_list=filtered_data[f"{var}_depth"],
            filename=f"{var}_vs_depth_clean",
        )
        plotter.plot_var_vs_depth_bad_vs_good_data(
            var,
            var_list_good=filtered_data[var],
            var_list_bad=df.loc[:, var],
            depth_list_good=filtered_data[f"{var}_depth"],
            depth_list_bad=df.loc[:, "depth"],
            filename=f"{var}_vs_depth_clean_vs_bad",
        )


if __name__ == "__main__":
    print("-" * 100)
    print("-" * 100)
    ncfiles_path = "/mnt/storage6/caio/AW_CAA/CTD_DATA/MEDS_2021/ncfiles_standard/"
    start_time = time.time()
    main(ncfiles_path)

    print("--- %s seconds ---" % (time.time() - start_time))
