import matplotlib.pyplot as plt
import numpy as np


class Plotter:
    def __init__(self) -> None:
        pass

    def plot_var_vs_depth(self, var, var_list, depth_list, filename):
        fig, ax = plt.subplots()
        ax.scatter(var_list, depth_list, s=0.2)
        if var == "temp":
            plt.xlabel("Temperature [ᵒC]")
        elif var == "psal":
            plt.xlabel("Salinity [PSU]")
        plt.ylabel("Depth [m]")
        plt.gca().invert_yaxis()
        # plt.show()
        plt.savefig("imgs/x_vs_depth/" + filename + ".png")
        plt.clf()

    def plot_var_vs_depth_bad_vs_good_data(
        self,
        var,
        var_list_good,
        var_list_bad,
        depth_list_good,
        depth_list_bad,
        filename,
    ):
        # Convert lists to NumPy arrays for easier manipulation
        var_list_good = np.array(var_list_good)
        var_list_bad = np.array(var_list_bad)
        depth_list_good = np.array(depth_list_good)
        depth_list_bad = np.array(depth_list_bad)

        # Find indices of values in var_list_bad that are not in var_list_good
        mask = np.isin(var_list_bad, var_list_good, invert=True)

        # Filter var_list_bad and depth_list_bad using the mask
        var_list_bad_filtered = var_list_bad[mask]
        depth_list_bad_filtered = depth_list_bad[mask]

        fig, ax = plt.subplots()
        ax.scatter(var_list_good, depth_list_good, s=1, c="#00FF00", label="Good Data")
        ax.scatter(
            var_list_bad_filtered,
            depth_list_bad_filtered,
            s=1,
            c="#FF0000",
            marker="^",
            label="Bad Data",
        )  # Set marker to triangle
        if var == "temp":
            plt.xlabel("Temperature [ᵒC]")
        elif var == "psal":
            plt.xlabel("Salinity [PSU]")
        plt.ylabel("Depth [m]")
        plt.gca().invert_yaxis()
        plt.legend()
        plt.savefig("imgs/bad_vs_good/" + filename + ".png")
        plt.clf()
