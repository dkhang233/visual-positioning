import geojson
import numpy as np


scale = 25
trans_x = -6.2
trans_z = -4.8

transform_matrix = np.array([[scale, 0, - trans_x * scale],
                        [0, scale, - trans_z * scale],
                        [0, 0, 1]])

coordinates=[
                [
                    [5.8, -4.8],
                    [-6.2, -4.8],
                    [-6.2, 4.9003],
                    [-4.0215, 4.9003],
                    [-4.0215, 6],
                    [5.8, 6]
                ],
                [
                    [-3.887, -4.8],
                    [-5.55604, -4.8]
                ],
                [
                    [-1.41443, -3.34106],
                    [-2.73287, -3.34106],
                    [-2.73287, 1.66494],
                    [-1.41443, 1.66494]
                ],
                [
                    [-5.76162, -4.15827],
                    [-6.2, -4.15827],
                    [-6.2, -2.88941],
                    [-5.76162, -2.88941]
                ],
                [
                    [-4.6482, -2.80516],
                    [-6.2, -2.80516],
                    [-6.2, -1.32057],
                    [-4.6482, -1.32057]
                ],
                [
                    [-4.6482, 0.459868],
                    [-6.2, 0.459868],
                    [-6.2, 1.57999],
                    [-4.6482, 1.57999]
                ],
                [
                    [-4.4215, 4.07536],
                    [-6.2, 4.07536],
                    [-6.2, 4.8003],
                    [-4.4215, 4.8003]
                ]
            ]

labels = ["wall","door","table","cabinet","table","table","table"]
homogeneous = [[[x, y, 1] for x, y in ring] for ring in coordinates]

# Nhân từng tọa độ với ma trận `a`
transformed = [
    [transform_matrix @ np.array(coord) for coord in ring] for ring in homogeneous
]

collection = geojson.FeatureCollection([])

count = 0
for ring in transformed:
    polygon = geojson.Polygon([[(coord[0], coord[1]) for coord in ring]])
    # print(polygon)
    collection.features.append(geojson.Feature(geometry=polygon, properties={"style": labels[count]}))
    count += 1

with open("output.json", "w") as f:
    geojson.dump(collection, f)
