import tarfile
import os
import urllib.request
import shutil
import tempfile
from or_datasets import Bunch


def _fetch_file(key):
    lookup = {
        "planar": "planar.tgz",
        "grid": "grid.tgz",
        "Canad-C": "C.tgz",
        "Canad-C+": "CPlus.tgz",
        "Canad-R": "R.tgz",
    }

    filename = os.path.join(tempfile.gettempdir(), lookup[key])

    if not os.path.exists(filename):
        # get data
        url = f"http://groups.di.unipi.it/optimize/Data/MMCF/{lookup[key]}"
        headers = {"Accept": "application/zip"}
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req) as response:
            with open(filename, "wb") as out_file:
                shutil.copyfileobj(response, out_file)

    tf = tarfile.open(filename, "r")

    return tf


def _get_edges(m, fh):
    E = []
    c = []
    Q = []
    for i in range(m):
        source, target, cost, capacity = [int(x) for x in fh.readline().split()]
        E.append((source - 1, target - 1))  # we want zero indexed nodes
        c.append(cost)
        Q.append(capacity)

    return E, c, Q


def _get_commodities(k, fh):
    OD = []
    D = []
    for i in range(k):
        origin, dest, demand = [int(x) for x in fh.readline().split()]
        OD.append((origin - 1, dest - 1))  # we want zero indexed nodes
        D.append(demand)

    return OD, D


def fetch_linear_mcf(name: str, instance: str = None, return_raw=True) -> Bunch:
    """
    Fetches multicommodity data sets from
    http://groups.di.unipi.it/optimize/Data/MMCF.html

    Possible sets are `planar` and `grid`.

    Usage for getting a MCF instance is:
    ```python
    bunch = fetch_linear_mcf(
        "planar", instance="planar33"
    )
    name, n, m, k, E, c, Q, OD, D = bunch["instance"]
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
            if instancefile.endswith(".doc"):
                continue

            if instance:
                if instancefile == f"{instance}":
                    members = [tf.getmember(instancefile)]
                    break
    else:
        members = tf.getmembers()

    bunch = Bunch(data=[], instance=None, DESCR="MCF")
    for member in members:
        name = member.name

        if name.endswith(".doc"):
            continue

        with tf.extractfile(member) as fh:
            n = int(fh.readline())
            m = int(fh.readline())
            k = int(fh.readline())

            # edges
            E, c, Q = _get_edges(m, fh)

            # commodities
            OD, D = _get_commodities(k, fh)

        data = (name, n, m, k, E, c, Q, OD, D)
        bunch["data"].append(data)

        if instance:
            bunch["instance"] = data

    tf.close()
    return bunch


def fetch_mcf_network_design(name: str, instance: str = None, return_raw=True) -> Bunch:
    """
    Fetches multicommodity data sets from
    http://groups.di.unipi.it/optimize/Data/MMCF.html

    Possible sets are `Canad-C`, .

    Usage for getting a FCMCF instance is:
    ```python
    bunch = fetch_mcf_network_design(
        "Canad-C", instance="c33"
    )
    name, n, m, k, E, c, Q, f, OD, D = bunch["instance"]
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
            if instancefile == f"{instance}.dow":
                members = [tf.getmember(instancefile)]
                break
    else:
        members = tf.getmembers()

    bunch = Bunch(data=[], instance=None, DESCR="FCMCF")
    for member in members:
        name = member.name

        with tf.extractfile(member) as fh:
            # skip first line
            fh.readline()

            n, m, k = [int(x) for x in fh.readline().split()]

            # edges
            E = []
            c = []
            Q = []
            f = []
            for i in range(m):
                source, target, cost, capacity, fixed, someNumber, arcId = [
                    int(x) for x in fh.readline().split()
                ]
                E.append((source - 1, target - 1))  # we want zero indexed nodes
                c.append(cost)
                Q.append(capacity)
                f.append(fixed)

            # commodities
            OD = []
            D = []
            for i in range(k):
                origin, dest, demand = [int(x) for x in fh.readline().split()]
                OD.append((origin - 1, dest - 1))  # we want zero indexed nodes
                D.append(demand)

        data = (name, n, m, k, E, c, Q, f, OD, D)
        bunch["data"].append(data)

        if instance:
            bunch["instance"] = data

    tf.close()
    return bunch
