class MyDirection:
    North = (0, 1)
    East = (1, 0)
    West = (-1, 0)
    South = (0, -1)
    Stop = (0, 0)

    opposite = {
        North: South,
        East: West,
        West: East,
        South: North,
        Stop: Stop,
    }

    fromStr = {
        'North': North,
        'East': East,
        'West': West,
        'South': South,
        'Stop': Stop,
    }

    toStr = {
        North: 'North',
        East: 'East',
        West: 'West',
        South: 'South',
        Stop: 'Stop',
    }
