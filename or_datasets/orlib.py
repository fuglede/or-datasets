import os
import urllib.request
import shutil
import tempfile
from or_datasets import Bunch


def _fetch_file(instance):
    filename = os.path.join(tempfile.gettempdir(), f"{instance}.txt")

    if not os.path.exists(filename):
        # get data
        url = f"http://people.brunel.ac.uk/~mastjjb/jeb/orlib/files/{instance}.txt"
        headers = {}
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req) as response:
            with open(filename, "wb") as out_file:
                shutil.copyfileobj(response, out_file)

    file = open(filename, "r")

    return file


def fetch_rcspp(instance: str, return_raw=True) -> Bunch:
    """
    Fetches RCSPP data instances from
    http://people.brunel.ac.uk/~mastjjb/jeb/orlib/rcspinfo.html

    Possible instances are `rcsp{i}` for 1,...,24.

    Usage for getting amn RCSPP instance is:
    ```python
    bunch = fetch_rcspp(instance="rcspp1")
    name, n, m, k, E, c, w, a, b = bunch["instance"]
    ```

    Parameters:
        name: String identifier of the dataset. Can contain multiple instances
        instance: String identifier of the instance. If `None` the entire set is
            returned.

        return_raw: If `True` returns the raw data as a tuple

    Returns:
        Network information.
    """

    bunch = Bunch(data=[], instance=None, DESCR="RCSPP")

    with _fetch_file(instance) as file:
        n, m, k = [int(x) for x in file.readline().split()]

        # edges
        E = []
        c = []
        w_vertices = [[None] * n] * k
        w = [[None] * m] * k
        a = [None] * k
        b = [None] * k

        a = [int(x) for x in file.readline().split()]
        b = [int(x) for x in file.readline().split()]

        for v in range(n):
            data = [int(x) for x in file.readline().split()]
            for h in range(k):
                w_vertices[h][v] = int(data[h])

        for e in range(m):
            data = [int(x) for x in file.readline().split()]
            E += [(data[0] - 1, data[1] - 1)]
            c += [int(data[2])]
            for h in range(k):
                w[h][e] = int(data[3 + h])  # beware of 0 values

        for j in range(m):
            u, v = E[j]
            for h in range(k):
                w[h][j] += w_vertices[h][u] / 2 + w_vertices[h][v] / 2

        data = (instance, n, m, k, 0, n - 1, E, c, w, a, b)
        bunch["data"].append(data)

        if instance:
            bunch["instance"] = data

    # file.close()
    return bunch
