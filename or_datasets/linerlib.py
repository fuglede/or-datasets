import math
import zipfile
import csv
import os
import urllib.request
import shutil
import tempfile
import io
from or_datasets import Bunch
from typing import Dict, Any, Tuple, List


def _fetch_linerlib_zip():
    filename = os.path.join(tempfile.gettempdir(), "linerlib.zip")

    if not os.path.exists(filename):
        # get data
        url = "https://github.com/blof/LINERLIB/archive/master.zip"
        headers = {"Accept": "application/zip"}
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req) as response:
            with open(filename, "wb") as out_file:
                shutil.copyfileobj(response, out_file)

    zf = zipfile.ZipFile(filename, "r")

    return zf


def _convertToNumeric(key, value):
    integerKeys = [
        "FFEPerWeek",
        "Revenue_1",
        "TransitTime",
        "Distance",
        "Draft",
        "Capacity FFE",
        "TC rate daily (fixed Cost)",
        "panamaFee",
        "suezFee",
        "Quantity",
        "capacity",
    ]
    floatKeys = [
        "draft",
        "minSpeed",
        "maxSpeed",
        "designSpeed",
        "Bunker ton per day at designSpeed",
        "Idle Consumption ton/day",
        "speed",
    ]
    booleanKeys = ["IsPanama", "IsSuez"]

    if value and key in integerKeys:
        return int(value)

    if value and key in floatKeys:
        return float(value)

    if value and key in booleanKeys:
        return bool(value)

    return value


def fetch_linerlib(instance: str = None, return_raw=True) -> Bunch:
    """
    Fetches data sets from the GitHub [repository](https://github.com/blof/LINERLIB) of
    [LINERLIB](https://linerlib.org).

    Usage for getting an instances is:

    ```python
    data = fetch_linerlib(instance="Baltic")
    ```

    Parameters:
        instance: String identifier of the instance. If `None` the entire set is
            returned.
        return_raw: If `True` returns the raw data as a tuple

    Returns:
        Network and demand information.
    """

    zf = _fetch_linerlib_zip()

    files: Dict[str, Dict[str, Any]] = {}

    dataDir = "LINERLIB-master/data/"
    distFile = os.path.join(dataDir, "dist_dense.csv")
    fleetFile = os.path.join(dataDir, "fleet_data.csv")

    okInstancePrefix = ["Demand_", "fleet_", "transittime_revision/Demand_"]

    for instancefile in zf.namelist():
        if not (
            instancefile.endswith(".csv")
            and (
                any([p in instancefile for p in okInstancePrefix])
                or instancefile in [distFile, fleetFile]
            )
        ):
            continue

        instanceDemandFile = os.path.join(dataDir, f"Demand_{instance}.csv")
        instanceDemandRevisedFile = os.path.join(
            dataDir, f"transittime_revision/Demand_{instance}.csv"
        )
        instanceFleetFile = os.path.join(dataDir, f"fleet_{instance}.csv")

        if instance and instancefile not in [
            instanceDemandFile,
            instanceDemandRevisedFile,
            instanceFleetFile,
            distFile,
            fleetFile,
        ]:
            continue

        with zf.open(instancefile) as f:
            reader = csv.DictReader(io.TextIOWrapper(f, "utf-8"), delimiter="\t")
            d: Dict[str, Any] = {k: [] for k in reader.fieldnames}
            for row in reader:
                [d[k].append(_convertToNumeric(k, v)) for k, v in row.items()]

            files[instancefile] = d

    bunch = Bunch(data=[], instance=None, DESCR="LINERLIB")

    # format data
    fleet = files[fleetFile]
    del files[fleetFile]

    distance = files[distFile]
    del files[distFile]

    consolidatedDataDict: Dict[str, Dict[str, Any]] = {}

    # per instance
    for k, v in files.items():
        dataType = k[k.rfind("/") + 1 : k.rfind("_")]
        name = k[k.rfind("_") + 1 : k.rfind(".")]

        if name not in consolidatedDataDict:
            consolidatedDataDict[name] = {}

        consolidatedDataDict[name][dataType] = v

    bunch["data"] = [
        (k, v["Demand"], v["fleet"], fleet, distance)
        for k, v in consolidatedDataDict.items()
    ]

    if instance:
        bunch["instance"] = bunch["data"][0]

    return bunch


def fetch_linerlib_rotations(instance: str = None, return_raw=True) -> Bunch:
    """
    Gets the networks calculated in ["A Matheuristic for the Liner Shipping Network
    Design Problem with Transit Time Restrictions"](
    https://doi.org/10.1007/978-3-319-24264-4_14) by Brouer et al. 2015 from the
    LINERLIB GitHub [repository](https://github.com/blof/LINERLIB)

    Usage for getting the rotations related to an instance is:

    ```python
    data = fetch_linerlib(instance="Baltic")
    network = fetch_linerlib_rotations(instance="Baltic_best_base")
    ```

    This can be feeded into the [GraphBuilder][flowty.datasets.linerlib.GraphBuilder].


    Parameters:
        instance: String identifier of the instance. If `None` the entire set is
            returned.

            Note: Instance `Mediterranean` is called `Med`

        return_raw: If `True` returns the raw data as a tuple

    Returns:
        The rotations, speed and capacities of the network.
    """
    zf = _fetch_linerlib_zip()

    files: Dict[str, Tuple[List[str], List[str], List[str]]] = {}

    dataDir = "LINERLIB-master/results/BrouerDesaulniersPisinger2014/"

    for instancefile in zf.namelist():
        if not instancefile.endswith(".log") or not instancefile.startswith(dataDir):
            continue

        if instance and not instancefile[len(dataDir) :].startswith(instance):
            continue

        with zf.open(instancefile, "r") as f:
            name = instancefile[len(dataDir) : instancefile.rfind(".")]

            # data per service
            rotations = []
            speed = []
            capacities = []

            line = f.readline().decode("utf-8")

            while line:
                # rotations
                if line.startswith("service"):
                    capacityLine = f.readline().decode("utf-8")
                    capacityValue = int(capacityLine.strip().replace("capacity", ""))
                    capacities.append(capacityValue)
                    f.readline()  # num vessels

                    rotation = []
                    portLine = f.readline().decode("utf-8")
                    while portLine:
                        if portLine.startswith(" Butterfly"):
                            portLine = f.readline().decode("utf-8")
                            continue
                        if portLine == "\n":
                            break

                        portLineArray = portLine.split("\t")
                        portValue = portLineArray[1].strip()
                        rotation.append(portValue)

                        portLine = f.readline().decode("utf-8")
                    rotations.append(rotation)

                    speedLine = f.readline().decode("utf-8")
                    speedValue = float(speedLine.strip().replace("speed", ""))
                    speed.append(speedValue)

                # continue
                line = f.readline().decode("utf-8")

            files[name] = (rotations, speed, capacities)

    bunch = Bunch(data=[], instance=None, DESCR="LINERLIB rotations")

    bunch["data"] = [(k, v[0], v[1], v[2]) for k, v in files.items()]

    if instance:
        bunch["instance"] = bunch["data"][0]

    return bunch


class GraphBuilder:
    """
    Convinience builder class for constructiong graphs for liner shipping networks.
    """

    # constants
    edgeTransitTime = 3
    """The transsipment edge time."""
    edgeTransitCost = 10
    """The transsipment edge cost."""
    edgeLoadTime = 1
    """The load/unload edge time."""
    edgeLoadCost = 10
    """The load/unload edge cost."""
    edgeForfeitCost = 100
    """The forfeit edge cost."""

    # edge attributes
    cost: List[float] = []
    """The edge costs."""
    travelTime: List[float] = []
    """The edge transshipment times."""
    capacity: List[int] = []
    """The edge capacities."""

    def __init__(self, data, network):
        """
        Initialize graph builder.

        Parameters:
            data: Bunch of instance data.
            network: Bunch of network rotation data.

        """
        self.name, self.demand, self.fleet, self.fleet_data, self.distance = data[
            "instance"
        ]
        self.rotationName, self.rotations, self.speed, self.capacities = network[
            "instance"
        ]

    def portCallNodes(self) -> List[str]:
        """
        The port call nodes are ports reached by a rotation.

        Returns:
            The names like `P_{name}`
        """
        return list(
            set([f"C{i}_{r}" for i, rs in enumerate(self.rotations) for r in rs])
        )

    def originNodes(self) -> List[str]:
        """
        The origin nodes for the commodities.

        Returns:
            The names like `O_{name}`
        """
        return [
            f"O{i}_{self.demand['Origin'][i]}"
            for i in range(len(self.demand["Destination"]))
        ]

    def destinationNodes(self) -> List[str]:
        """
        The destination nodes for the commodities.

        Returns:
            The names like `D_{name}`
        """
        return [
            f"D{i}_{self.demand['Destination'][i]}"
            for i in range(len(self.demand["Destination"]))
        ]

    def voyageEdges(self) -> List[Tuple[str, str]]:
        """
        The voyage edges.

        Returns:
            Pairs of port node names.
        """
        zipDistance = list(
            zip(self.distance["fromUNLOCODe"], self.distance["ToUNLOCODE"])
        )
        edges = []
        for i, r in enumerate(self.rotations):
            self.cost += [0] * len(r)
            self.capacity += [self.capacities[i]] * len(r)

            for u, v in list(zip(r, r[1:])) + [(r[-1], r[0])]:
                edges.append((f"C{i}_{u}", f"C{i}_{v}"))
                self.travelTime.append(
                    self.distance["Distance"][zipDistance.index((u, v))]
                    / self.speed[i]
                    / 24
                )

        return edges

    def transitEdges(self) -> List[Tuple[str, str]]:
        """
        The transshipment edges.

        Returns:
            Pairs of port node names.
        """
        portCalls = self.portCallNodes()
        edges = []
        ports = set([v[v.rfind("_") + 1 :] for v in portCalls])
        for p in ports:
            calls = [v for v in portCalls if v[v.rfind("_") + 1 :] == p]
            transitPortEdges = [(u, v) for u in calls for v in calls if v != u]

            self.cost += [self.edgeTransitCost] * len(transitPortEdges)
            self.travelTime += [self.edgeTransitTime] * len(transitPortEdges)
            self.capacity += [math.inf] * len(transitPortEdges)
            edges += transitPortEdges

        return edges

    def loadEdges(self) -> List[Tuple[str, str]]:
        """
        The load/unload edges.

        Returns:
            Pairs of port node and origin/destination node names.
        """
        edges = []
        for i in range(len(self.demand["Destination"])):
            origin = self.demand["Origin"][i]
            dest = self.demand["Destination"][i]
            loadDemandEdges = []
            for j, rs in enumerate(self.rotations):
                if origin in rs:
                    loadDemandEdges.append((f"O{i}_{origin}", f"C{j}_{origin}"))
                if dest in rs:
                    loadDemandEdges.append((f"C{j}_{dest}", f"D{i}_{dest}"))

            self.cost += [self.edgeLoadCost] * len(loadDemandEdges)
            self.travelTime += [self.edgeLoadTime] * len(loadDemandEdges)
            self.capacity += [math.inf] * len(loadDemandEdges)
            edges += loadDemandEdges

        return edges

    def forfeitEdges(self) -> List[Tuple[str, str]]:
        """
        The forfeit edges.

        Returns:
            Pairs of origin/desition node names.
        """
        edges = []
        for i in range(len(self.demand["Destination"])):
            origin = self.demand["Origin"][i]
            dest = self.demand["Destination"][i]
            edges.append((f"O{i}_{origin}", f"D{i}_{dest}"))

            self.cost += [self.edgeForfeitCost]
            self.travelTime += [self.demand["TransitTime"][i]]
            self.capacity += [math.inf]

        return edges
