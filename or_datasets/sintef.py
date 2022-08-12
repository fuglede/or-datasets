import math
import zipfile
import os
import urllib.request
import shutil
import tempfile
from or_datasets import Bunch


def _fetch_file(key):
    lookup = {
        "li-lim-100": "pdp_100.zip",
        "li-lim-200": "pdp_200.zip",
        "li-lim-400": "pdp_400.zip",
        "li-lim-600": "pdp_600.zip",
        "li-lim-800": "pdptw800.zip",
        "li-lim-1000": "pdptw1000.zip",
    }

    filename = os.path.join(tempfile.gettempdir(), lookup[key])

    if not os.path.exists(filename):
        # get data
        url = f"https://www.sintef.no/contentassets/1338af68996841d3922bc8e87adc430c/{lookup[key]}"
        headers = {"User-agent": "Mozilla/5.0"}
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req) as response:
            with open(filename, "wb") as out_file:
                shutil.copyfileobj(response, out_file)

    zf = zipfile.ZipFile(filename, "r")

    return zf


def fetch_pdptw(name: str, instance: str = None, return_raw=True) -> Bunch:
    """
    Fetches pickup and delivery data sets from https://www.sintef.no/projectweb/top/

    Possible sets are `li-lim-n` where n = [100, 200, 400, 600, 800, 1000]

    Usage for getting a PDPTW instance is:
    ```python
    bunch = fetch_pdptw(
        "li-lim-100", instance="lc101"
    )
    name, n, E, k, c, d, Q, t, a, b, x, y, T, P, D = bunch["instance"]
    ```

    Parameters:
        name: String identifier of the dataset. Can contain multiple instances
        instance: String identifier of the instance. If `None` the entire set is
            returned.

        return_raw: If `True` returns the raw data as a tuple

    Returns:
        Network information.
    """

    zf = _fetch_file(name)

    members = []
    path_prefix = ""
    for instancefile in zf.namelist():
        if instance:
            # special naming for 100 set
            if name.endswith("100"):
                path_prefix, instancefile = instancefile.split("/")

            if instancefile == f"{instance}.txt":
                members = [ "/".join([path_prefix, instancefile]) if path_prefix else instancefile ]
                break
        else:
            members.append(instancefile)

    bunch = Bunch(data=[], instance=None, DESCR="PDPTW")
    for member in members:        
        with zf.open(member) as fh:
            # special naming for 100 set
            if name.endswith("100"):
                member = instancefile.split("/")[0]

            name = member.split(".")[0]

            k, Q, speed = [int(x) for x in fh.readline().split()]

            # tasks
            x = []
            y = []
            d = []
            a = []
            b = []
            s = []
            P = []
            D = []
            for line in fh:
                task, xCoord, yCoord, demand, early, late, service, pickup, delivery = [
                    int(x) for x in line.split()
                ]
                x.append(xCoord)
                y.append(yCoord)
                d.append(demand)
                a.append(early)
                b.append(late)
                s.append(service)
                P.append(pickup)
                D.append(delivery)

            # # filter first n reqs
            # num = 10
            # indeces = [i for i,pickup in enumerate(P) if pickup == 0]
            # indeces = indeces[:num]
            # indeces += [D[i] for i in indeces[1:]]
            # indeces.sort()

            # x = [j for i,j in enumerate(x) if (i in indeces)]
            # y = [j for i,j in enumerate(y) if (i in indeces)]
            # d = [j for i,j in enumerate(d) if (i in indeces)]
            # a = [j for i,j in enumerate(a) if (i in indeces)]
            # b = [j for i,j in enumerate(b) if (i in indeces)]
            # s = [j for i,j in enumerate(s) if (i in indeces)]
            # P = [indeces.index(j) for i,j in enumerate(P) if (i in indeces)]
            # D = [indeces.index(j) for i,j in enumerate(D) if (i in indeces)]
            
            # duplicate depot
            x.append(x[0])
            y.append(y[0])
            d.append(d[0])
            a.append(a[0])
            b.append(b[0])
            s.append(s[0])
            P.append(P[0])
            D.append(D[0])

            n = len(x)
            E = []
            c = []
            t = []

            for i in range(n):
                for j in range(n):
                    if j <= i:
                        continue

                    value = (
                        int(math.sqrt(math.pow(x[i] - x[j], 2) + math.pow(y[i] - y[j], 2)) * 10)
                        / 10
                    )

                    if i != n - 1 and j != 0 and not (i == 0 and j == n - 1):
                        c.append(value)
                        t.append(value + s[i])
                        E.append((i, j))

                    if j != n - 1 and i != 0:
                        c.append(value)
                        t.append(value + s[j])
                        E.append((j, i))

            data = (name, n, E, k, c, d, Q, t, a, b, x, y, t, P, D)
            bunch["data"].append(data)

            if instance:
                bunch["instance"] = data

    zf.close()
    return bunch
