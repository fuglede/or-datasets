import gzip
import os
import urllib.request
import shutil
import tempfile
from or_datasets import Bunch
import networkx as nx
import pickle


def _fetch_file(key, type):
    filename = os.path.join(tempfile.gettempdir(), f"USA-road-{type}.{key}.gr.gz")

    if not os.path.exists(filename):
        # get data
        url = (
            "http://www.diag.uniroma1.it/~challenge9/data/"
            f"USA-road-{type}/USA-road-{type}.{key}.gr.gz"
        )
        headers = {"Accept": "application/zip"}
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req) as response:
            with open(filename, "wb") as out_file:
                shutil.copyfileobj(response, out_file)

    gzf = gzip.open(filename, "rb")

    return gzf


def _get_resource_spp(d, E):
    sources, targets = map(list, zip(*E))
    tuples = list(zip(sources, targets, d))
    G = nx.MultiDiGraph()
    G.add_weighted_edges_from(tuples)
    length, path = nx.single_source_dijkstra(G, 0)

    return length, path


def _get_resource_limit(path_d, length_t, t, E, dest, p):
    w_t = length_t[dest - 1]

    path = path_d[dest - 1]
    w_d_t = 0

    i = 0
    prev = path[i]
    for i in path[1:]:
        e = E.index((prev, i))
        prev = i

        w_d_t += t[e]

    T = p * (w_d_t - w_t) + w_t
    return T


def _set_cache(filename, data):
    filepath = os.path.join(tempfile.gettempdir(), filename)
    with open(filepath, "wb") as file:
        pickle.dump(data, file)


def _get_cache(filename):
    data = None
    filepath = os.path.join(tempfile.gettempdir(), filename)
    if os.path.exists(filepath):
        with open(filepath, "rb") as file:
            data = pickle.load(file)
    return data


def fetch_rcspp(instance: str, destinations=[], p_values=[], return_raw=True) -> Bunch:
    """
    Fetches shortest path data set from
    http://www.diag.uniroma1.it//~challenge9/download.shtml

    Calculates resource limits based on tightness `p` between 0 and 1 as in
    Sedeño-Noda and Alonso-Rodríguez (2015) (doi: 10.1016/j.amc.2015.05.109).

    Multiple `dest` and `p` values provides multiples instances.

    Usage for getting a shortest path instance is:
    ```python
    bunch = fetch_spp(
        instance="NY"
    )
    name, n, m, E, d, t = bunch["instance"]
    ```

    Coordinates are not fetched. They are available from the website.

    Parameters:
        name: String identifier of the dataset. Can contain multiple instances
        instance: String identifier of the instance. If `None` the entire set is
            returned.

        return_raw: If `True` returns the raw data as a tuple

    Returns:
        Network information.
    """

    lookup_p = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8]

    # 1-indexed
    lookup_dests = {
        "USA": [24, 4893, 976909, 11973673, 23947347],
        "CTR": [23, 3752, 592985, 7040908, 14081816],
        "W": [22, 2502, 277351, 3131052, 6262104],
        "E": [21, 1897, 165233, 1799311, 3598623],
        "LKS": [21, 1660, 128912, 1379059, 2758119],
        "CAL": [20, 1375, 90684, 945407, 1890815],
        "NE": [20, 1234, 74219, 762227, 1524453],
        "NW": [],
        "FLA": [20, 1034, 53439, 535188, 1070376],
        "COL": [19, 660, 23256, 217833, 435666],
        "BAY": [18, 567, 17562, 160635, 321270],
        "NY": [18, 514, 14676, 132173, 264346],
    }

    if any([p not in lookup_p for p in p_values]):
        raise ValueError(f"A p value is not valid: {p_values}")
    if any([dest not in lookup_dests[instance] for dest in destinations]):
        raise ValueError(f"A destination is not valid: {destinations}")

    # initialize
    spp_bunch = None
    path_d = None
    length_t = None

    bunch = Bunch(data=[], instance=None, DESCR="RCSPP")

    if not destinations:
        destinations = lookup_dests[instance]
    if not p_values:
        p_values = lookup_p

    for dest in destinations:
        for p in p_values:
            instance_name = f"{instance}_{dest}_{p}"
            data = _get_cache(f"{instance_name}_data.bin")
            
            if data:
                bunch["data"].append(data)
                continue

            # not in cache
            if not spp_bunch:
                spp_bunch = fetch_spp(instance, return_raw)
                _, n, m, E, d, t = spp_bunch["instance"]

            if not path_d:
                path_d = _get_cache(f"{instance}_distance.bin")
            if not path_d:
                _, path_d = _get_resource_spp(d, E)
                _set_cache(f"{instance}_distance.bin", path_d)

            if not length_t:
                length_t = _get_cache(f"{instance}_travel.bin")
            if not length_t:
                length_t, _ = _get_resource_spp(t, E)
                _set_cache(f"{instance}_travel.bin", length_t)
    
            Q = _get_resource_limit(path_d, length_t, t, E, dest, p)

            w = [t]
            a = [0]
            b = [Q]

            data = (instance_name, n, m, 1, 0, dest - 1, E, d, w, a, b)
            _set_cache(f"{instance_name}_data.bin", data)

            bunch["data"].append(data)

    if len(bunch["data"]) == 1:
        bunch["instance"] = bunch["data"][0]

    return bunch


def _read_distance(instance):
    E = []
    d = []
    n = 0
    m = 0
    with _fetch_file(instance, "d") as file:
        # read lines
        for line in file:
            if line.startswith(b"c"):
                continue
            if line.startswith(b"p"):
                _, _, n, m = [x for x in line.split()]
                n = int(n)
                m = int(m)
            if line.startswith(b"a"):
                _, source, target, q = [x for x in line.split()]
                E.append((int(source) - 1, int(target) - 1))
                d.append(int(q))
    return E, d, n, m


def _read_time(instance):
    t = []
    with _fetch_file(instance, "t") as file:
        # read lines
        for line in file:
            if line.startswith(b"c"):
                continue
            if line.startswith(b"p"):
                continue
            if line.startswith(b"a"):
                _, _, _, q = [x for x in line.split()]
                t.append(int(q))

    return t


def fetch_spp(instance: str, return_raw=True) -> Bunch:
    """
    Fetches shortest path data set from
    http://www.diag.uniroma1.it//~challenge9/download.shtml

    Usage for getting a shortest path instance is:
    ```python
    bunch = fetch_spp(
        instance="NY"
    )
    name, n, m, E, d, t = bunch["instance"]
    ```

    Coordinates are not fetched. They are available from the website.

    Parameters:
        name: String identifier of the dataset. Can contain multiple instances
        instance: String identifier of the instance. If `None` the entire set is
            returned.

        return_raw: If `True` returns the raw data as a tuple

    Returns:
        Network information.
    """

    # check cache for bunch
    bunch = _get_cache(f"{instance}_bunch.bin")
    if bunch:
        return bunch

    bunch = Bunch(data=[], instance=None, DESCR="SPP")

    E, d, n, m = _read_distance(instance)
    t = _read_time(instance)

    data = (instance, n, m, E, d, t)
    bunch["data"].append(data)

    if instance:
        bunch["instance"] = data

    _set_cache(f"{instance}_bunch.bin", bunch)

    return bunch
