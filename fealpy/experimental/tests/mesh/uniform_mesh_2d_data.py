import numpy as np

init_mesh_data = [
    {
        "extent": (0, 2, 0, 2),
        "h": (1.0, 1.0),
        "origin": (0, 0),

        "node": np.array([[[0, 0], [0, 1], [0, 2]],
                          [[1, 0], [1, 1], [1, 2]],
                          [[2, 0], [2, 1], [2, 2]]], dtype=np.float64),
        "edge": np.array([[0, 3],
                          [1, 4],
                          [5, 2],
                          [3, 6],
                          [4, 7],
                          [8, 5],
                          [1, 0],
                          [2, 1],
                          [3, 4],
                          [4, 5],
                          [6, 7],
                          [7, 8]], dtype=np.int32),
        "face": np.array([[0, 3],
                          [1, 4],
                          [5, 2],
                          [3, 6],
                          [4, 7],
                          [8, 5],
                          [1, 0],
                          [2, 1],
                          [3, 4],
                          [4, 5],
                          [6, 7],
                          [7, 8]], dtype=np.int32),

        "cell": np.array([[0, 1, 3, 4],
                          [1, 2, 4, 5],
                          [3, 4, 6, 7],
                          [4, 5, 7, 8]], dtype=np.int32),

        "NN": 9,
        "NE": 12,
        "NF": 12,
        "NC": 4,
    }
]

entity_data = [
    {
        "extent": (0, 2, 0, 2),
        "h": (1.0, 1.0),
        "origin": (0, 0),

        "entity_node": np.array([[0, 0],
                                 [0, 1],
                                 [0, 2],
                                 [1, 0],
                                 [1, 1],
                                 [1, 2],
                                 [2, 0],
                                 [2, 1],
                                 [2, 2]], dtype=np.float64),
    }
]

entity_measure_data = [
    {
        "extent": (0, 2, 0, 2),
        "h": (1.0, 1.0),
        "origin": (0, 0),

        "edge_length": (1.0, 1.0),
        "cell_area": 1.0,
    }
]

interpolation_points_data = [
    {
        "extent": (0, 2, 0, 2),
        "h": (1.0, 1.0),
        "origin": (0, 0),

        "ipoints_p1": np.array([[0, 0],
                                [0, 1],
                                [0, 2],
                                [1, 0],
                                [1, 1],
                                [1, 2],
                                [2, 0],
                                [2, 1],
                                [2, 2]], dtype=np.float64),
        "ipoints_p2": np.array([[0.0, 0.0],
                                [0.0, 1.0],
                                [0.0, 2.0],
                                [1.0, 0.0],
                                [1.0, 1.0],
                                [1.0, 2.0],
                                [2.0, 0.0],
                                [2.0, 1.0],
                                [2.0, 2.0],
                                [0.5, 0.0],
                                [0.5, 1.0],
                                [0.5, 2.0],
                                [1.5, 0.0],
                                [1.5, 1.0],
                                [1.5, 2.0],
                                [0.0, 0.5],
                                [0.0, 1.5],
                                [1.0, 0.5],
                                [1.0, 1.5],
                                [2.0, 0.5],
                                [2.0, 1.5],
                                [0.5, 0.5],
                                [0.5, 1.5],
                                [1.5, 0.5],
                                [1.5, 1.5]], dtype=np.float64),
    }
]

quadrature_formula_data = [
    {
        "extent": (0, 2, 0, 2),
        "h": (1.0, 1.0),
        "origin": (0, 0),

        "bcs_q1": (np.array([[0.5, 0.5]], dtype=np.float64),
                   np.array([[0.5, 0.5]], dtype=np.float64)),
        "bcs_q2": (np.array([[0.78867513, 0.21132487],
                             [0.21132487, 0.78867513]], dtype=np.float64),
                   np.array([[0.78867513, 0.21132487],
                             [0.21132487, 0.78867513]], dtype=np.float64)),
    }
]

shape_function_data = [
    {
        "extent": (0, 2, 0, 2),
        "h": (1.0, 1.0),
        "origin": (0, 0),

        "shape_function_p1": np.array([[0.25, 0.25, 0.25, 0.25]], dtype=np.float64),
        "shape_function_p2": np.array([[0, 0, 0, 0, 1, 0, 0, 0, 0]], dtype=np.float64),
    }
]

grad_shape_function_data = [
    {
        "grad_shape_function_u": np.array([[[-0.5, -0.5],
                   [-0.5, 0.5],
                   [0.5, -0.5],
                   [0.5, 0.5]]], dtype=np.float64),
        "grad_shape_function_x": np.array([[[[-0.5, -0.5],
                    [-0.5, 0.5],
                    [0.5, -0.5],
                    [0.5, 0.5]],
                   
                   [[-0.5, -0.5],
                    [-0.5, 0.5],
                    [0.5, -0.5],
                    [0.5, 0.5]],
                   
                   [[-0.5, -0.5],
                    [-0.5, 0.5],
                    [0.5, -0.5],
                    [0.5, 0.5]],
                   
                   [[-0.5, -0.5],
                    [-0.5, 0.5],
                    [0.5, -0.5],
                    [0.5, 0.5]]]], dtype=np.float64),
    }
]