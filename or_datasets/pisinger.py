import tarfile
import os
import urllib.request
import shutil
import tempfile
from or_datasets import Bunch
from typing import Dict


def _fetch_file(key: str) -> tarfile.TarFile:
    lookup = {
        "small": "smallcoeff_pisinger.tgz",
        "large": "largecoeff_pisinger.tgz",
        "hard": "hardinstances_pisinger.tgz",
    }

    filename = os.path.join(tempfile.gettempdir(), lookup[key])

    if not os.path.exists(filename):
        # get data
        url = f"http://www.diku.dk/~pisinger/{lookup[key]}"
        headers = {"Accept": "application/zip"}
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req) as response:
            with open(filename, "wb") as out_file:
                shutil.copyfileobj(response, out_file)

    tf = tarfile.open(filename, "r")

    return tf


def _parse_file(
    tf: tarfile.TarFile, instance: str, member: tarfile.TarInfo, bunch: Dict
) -> None:
    with tf.extractfile(member) as fh:
        # 100 instances per file
        for i in range(100):
            name = fh.readline().decode("utf-8").strip("\n")

            n = int(fh.readline().decode("utf-8").strip("\n").split()[1])
            c = int(fh.readline().decode("utf-8").strip("\n").split()[1])
            z = int(fh.readline().decode("utf-8").strip("\n").split()[1])
            fh.readline()  # time
            # edges
            p = []
            w = []
            x = []

            for i in range(n):
                item, profit, weight, xValue = [
                    int(x) for x in fh.readline().decode("utf-8").strip("\n").split(",")
                ]
                p.append(profit)
                w.append(weight)
                x.append(xValue)

            fh.readline()
            fh.readline()

            data = (name, n, c, p, w, z, x)

            if name == instance:
                bunch["data"].append(data)
                bunch["instance"] = data
                break

            if not instance:
                bunch["data"].append(data)


def fetch_knapsack(name: str, instance: str = None, return_raw=True) -> Bunch:
    """
    Fetches knapsack data sets from http://hjemmesider.diku.dk/~pisinger/codes.html

    Possible sets are `small`, `large` and `hard`.

    Usage for getting a Knapsack instance is:
    ```python
    bunch = fetch_knapsack(
        "small", instance="knapPI_1_50_1000-1"
    )
    name, n, c, p, w, z, x = bunch["instance"]
    ```

    Parameters:
        name: String identifier of the dataset. Can contain multiple instances
        instance: String identifier of the instance. If `None` the entire set is
            returned.

        return_raw: If `True` returns the raw data as a tuple

    Returns:
        Network information.
    """

    tf = _fetch_file(name)

    members = []
    if instance:
        for instancefile in tf.getnames():
            if instancefile.endswith(".txt"):
                continue

            if instance:
                rawInstanceFileName = "_".join(instance.split("_")[:-1])
                if instancefile == f"{rawInstanceFileName}.csv":
                    members = [tf.getmember(instancefile)]
                    break
    else:
        members = tf.getmembers()

    bunch = Bunch(data=[], instance=None, DESCR="Knapsack")
    for member in members:
        if member.name.endswith(".txt"):
            continue

        _parse_file(tf, instance, member, bunch)

    tf.close()
    return bunch
