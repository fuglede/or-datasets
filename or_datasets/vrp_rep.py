import math
import zipfile
import os
import xml.etree.ElementTree as ElementTree
import copy
import urllib.request
import shutil
import tempfile
from or_datasets import Bunch
from typing import List, Tuple, Optional


def fetch_vrp_rep(name: str, instance: str = None, return_raw=True) -> Bunch:
    """
    Fetches data sets from [VRP-REP](http://www.vrp-rep.org).

    Usage for getting a VRPTW instance is:
    ```python
    bunch = fetch_vrp_rep(
        "solomon-1987-r1", instance="R101_025"
    )
    name, n, E, c, d, Q, t, a, b, x, y = bunch["instance"]
    ```

    Parameters:
        name: String identifier of the dataset. Can contain multiple instances
        instance: String identifier of the instance. If `None` the entire set is
            returned.

        return_raw: If `True` returns the raw data as a tuple

    Returns:
        Network information.
    """

    # http://www.vrp-rep.org/datasets/download/solomon-1987-c1.zip

    filename = os.path.join(tempfile.gettempdir(), f"{name}.zip")

    if not os.path.exists(filename):
        url = f"http://www.vrp-rep.org/datasets/download/{name}.zip"
        headers = {"Accept": "application/xml"}
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req) as response:
            with open(filename, "wb") as out_file:
                shutil.copyfileobj(response, out_file)

    zf = zipfile.ZipFile(filename, "r")

    trees = []
    for instancefile in zf.namelist():
        if not instancefile.endswith(".xml"):
            continue

        if instance:
            if instancefile == f"{instance}.xml":
                with zf.open(instancefile) as f:
                    trees.append(ElementTree.parse(f))
                    break
        else:
            with zf.open(instancefile) as f:
                trees.append(ElementTree.parse(f))

    bunch = Bunch(data=[], instance=None, DESCR="VRPTW")
    for tree in trees:
        root = tree.getroot()

        instanceName: Optional[str] = _get_name(root)

        node_list = _get_node_list(root)

        n: int = len(node_list)

        # edges, distance, time
        m, c, t, x, y = _get_distance(n, node_list)

        # vehicle profile
        fleet = root.find("fleet")
        Q, T = _get_vehicle_profile(fleet)

        # requests
        requests = root.find("requests")
        d, a, b = _get_requests(requests, n, m, t)

        # set tw for duplicate depot node
        a[n - 1] = a[0]
        b[n - 1] = T

        if return_raw:
            data = (instanceName, n, m, c, d, Q, t, a, b, x, y)
        else:
            # TODO
            # generate model based on data
            # milp = mip.Model()
            # mapping = Mapping()
            # graphs: List[igraph.Graph] = []
            # data = Model(milp, mapping, graphs)
            pass

        bunch["data"].append(data)

        if instance:
            bunch["instance"] = data

    return bunch


def _get_name(root: ElementTree.Element) -> Optional[str]:
    info = root.find("info")
    if info:
        name = info.find("name")
        if name is not None and name.text:
            return name.text
        else:
            raise KeyError("no 'name' element")
    else:
        raise KeyError("no 'info' element")

    return None


num = 27
useNumer = False


def _get_node_list(root: ElementTree.Element):
    network = root.find("network")
    if network:
        nodes = network.find("nodes")
        if nodes:
            node_list = nodes.findall("node")
        else:
            raise KeyError("no 'nodes' element")
    else:
        raise KeyError("no 'network' element")

    if useNumer:
        node_list = node_list[:num]

    # duplicate depot node
    end_node = copy.deepcopy(node_list[0])
    end_node.set("id", str(len(node_list)))
    node_list.append(end_node)

    return node_list


def _get_distance(n, nodes: List[ElementTree.Element]):
    x: List[int] = [0] * n
    y: List[int] = [0] * n
    m: List[Tuple[int, int]] = []
    c: List[float] = []
    t: List[float] = []

    # calculate distance
    for node in nodes:
        id_attr = node.get("id")
        if id_attr:
            i = int(id_attr)
        else:
            raise KeyError("no 'id' attribute in 'node' element")

        cx = node.find("cx")
        if cx is not None and cx.text:
            x[i] = int(float(cx.text))
        else:
            raise KeyError("no 'cx' element")

        cy = node.find("cy")
        if cy is not None and cy.text:
            y[i] = int(float(cy.text))
        else:
            raise KeyError("no 'cy' element")

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
                t.append(value)
                m.append((i, j))

            if j != n - 1 and i != 0:
                c.append(value)
                t.append(value)
                m.append((j, i))

    return m, c, t, x, y


def _get_vehicle_profile(fleet: Optional[ElementTree.Element]):
    if fleet:
        vehicle = fleet.find("vehicle_profile")
    else:
        raise KeyError("no 'vehicle_profile' element")

    if vehicle:
        # capacity
        capacity = vehicle.find("capacity")
        if capacity is not None and capacity.text:
            Q = int(float(capacity.text))
        else:
            raise KeyError("no 'capacity' element")

        # time limit
        max_travel_time = vehicle.find("max_travel_time")
        if max_travel_time is not None and max_travel_time.text:
            t_limit = int(float(max_travel_time.text))
            T = t_limit
        else:
            raise KeyError("no 'max_travel_time' element")

    return Q, T


def _get_requests(
    requests: Optional[ElementTree.Element],
    n: int,
    m: List[Tuple[int, int]],
    t: List[float],
):
    d: List[int] = [0] * n
    a: List[int] = [0] * n
    b: List[int] = [0] * n

    if requests:
        request_list = requests.findall("request")

        if useNumer:
            request_list = request_list[: num - 1]

        for request in request_list:
            id_attr = request.get("id")
            if id_attr:
                i = int(id_attr)
            else:
                raise KeyError("no 'id' attribute in 'request' element")

            # demand
            quantity = request.find("quantity")
            if quantity is not None and quantity.text:
                d[i] = int(float(quantity.text))
            else:
                raise KeyError("no 'quantity' element")

            # time windows
            tw = request.find("tw")
            _get_tw(tw, i, a, b)

            service_time = request.find("service_time")
            _get_service_time(service_time, t, i, m)

    else:
        raise KeyError("no 'requests' element")

    return d, a, b


def _get_tw(tw, i, a, b):
    if tw is not None:
        start = tw.find("start")
        if start is not None and start.text:
            a[i] = int(start.text)
        else:
            raise KeyError("no 'start' element")

        end = tw.find("end")
        if end is not None and end.text:
            b[i] = int(end.text)
        else:
            raise KeyError("no 'end' element")
    else:
        raise KeyError("no 'tw' element")


def _get_service_time(service_time, t, i, m):
    if service_time is not None and service_time.text:
        s: int = int(float(service_time.text))
    else:
        raise KeyError("no 'service_time' element")
    for j, e in enumerate(m):
        if e[0] == i:
            t[j] += s
