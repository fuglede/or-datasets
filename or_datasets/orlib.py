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


def fetch_gap(name: str, instance: str, return_raw=True) -> Bunch:
    """
    Fetches GAP data instances from
    http://people.brunel.ac.uk/~mastjjb/jeb/orlib/gapinfo.html

    Possible instances are `gap{i}-{m}{n}-{j}` for sets i=1,...,12,a,b,c,d and
    instance with m agents and n jobs where j is a number up to 5 for numeric instance
    types and 6 otherwise.

    Instance sets i=1,...,12 are solved as maximization problems and therefore with
    negative costs.

    Usage for getting amn GAP instance is:
    ```python
    bunch = fetch_rcspp(instance="gap1")
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

    bunch = Bunch(data=[], instance=None, DESCR="GAP")

    instance_num = None
    if instance:
        instance_num = int(instance.split("-")[1]) if "-" in instance else None        

    with _fetch_file(name) as file:
        # problems per file
        P = int(file.readline())
        
        for p in range(P):
            m, n = [int(x) for x in file.readline().split()]

            have_numeric_prefix = name.removeprefix("gap").isnumeric()
            set_prefix = "c" if have_numeric_prefix else name.removeprefix("gap")
            instance_name = f"{set_prefix}{m}{n}-{p+1}"

            c = []
            d = []

            for i in range(m):
                nums = [int(x) for x in file.readline().split()]
                # due too linebreak
                while(len(nums) < n):
                    nums += [int(x) for x in file.readline().split()]

                if have_numeric_prefix:
                    nums = [ -x for x in nums]

                c += [nums]

            for i in range(m):
                nums = [int(x) for x in file.readline().split()]
                # due too linebreak
                while(len(nums) < n):
                    nums += [int(x) for x in file.readline().split()]                    
                d += [nums]

            nums = [int(x) for x in file.readline().split()]
            # due too linebreak
            while(len(nums) < m):
                nums += [int(x) for x in file.readline().split()]      
            Q = nums

            if instance_num and instance_num != p+1:
                continue

            data = (instance_name, n, m, c, d, Q)
            bunch["data"].append(data)
            if instance == instance_name:
                bunch["instance"] = data
                break

    return bunch


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

    return bunch
