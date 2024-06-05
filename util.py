import numpy as np

# 주어진 세 점의 좌표
PA = np.array([
    [128.3497, 38.6346],    # N
    [126.1864, 33.1123],    # S
    [131.8689, 37.2426],    # E
    [124.6350, 37.9675]     # W
])

PB = np.array([
    [409.43, 1.0],
    [164.84, 760.0],
    [799.0, 179.73],
    [1.0, 85.32]
])



def calculate_transformation(points_A, points_B):
    # A 좌표계의 점들을 확장하여 행렬을 생성 (x_A, y_A, 1)
    A_expanded = np.hstack((points_A, np.ones((points_A.shape[0], 1))))

    # 선형 시스템을 풀기 위해 B 좌표계의 각 좌표들을 분리
    B_x = points_B[:, 0]
    B_y = points_B[:, 1]

    # 각 축에 대해 least squares solution을 계산
    params_x, _, _, _ = np.linalg.lstsq(A_expanded, B_x, rcond=None)
    params_y, _, _, _ = np.linalg.lstsq(A_expanded, B_y, rcond=None)

    # 변환 행렬 및 이동 벡터 추출
    transformation_matrix = np.array([[params_x[0], params_x[1]], [params_y[0], params_y[1]]])
    translation_vector = np.array([params_x[2], params_y[2]])

    return transformation_matrix, translation_vector


transformation = [
    calculate_transformation(np.array([PA[0], PA[1], PA[2]]), np.array([PB[0], PB[1], PB[2]])),
    calculate_transformation(np.array([PA[0], PA[1], PA[3]]), np.array([PB[0], PB[1], PB[3]]))
]


def transform_coordinate(x_A, y_A):
    index = 0 if np.cross(PA[0] - PA[1], np.array([x_A, y_A] - PA[1])) < 0 else 1
    A_coord = np.array([x_A, y_A])
    B_coord = transformation[index][0].dot(A_coord) + transformation[index][1]
    return B_coord


# 8 directions
direction_str = ['N', 'NE', 'E', 'SE', 'S', 'SW', 'W', 'NW']


def get_direction(wd):
    return direction_str[int((wd + 22.5) / 45) % 8] if not np.isnan(wd) else 'nan'
