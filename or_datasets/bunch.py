class Bunch(dict):
    """
    Dictionary-like object returned when fetching data sets.

    Some common options:

    Option | Type | Description | Default
    ------ | ---- | ----------- | -------
    data | List[Any] | An array of data for a set of instances | List[]
    instance | Optional[Any] | Data for a specified instance otherwise | None
    DESCR | str | The full description of the data set | None
    """

    def __init__(self, **kwargs):
        """Initialize the dictionary object"""
        super().__init__(kwargs)
