# coding: utf-8
from typing import List

from img2table.tables.objects.cell import Cell


def coordinate_approximately_equal(coord_1: int, coord_2: int, leeway: int = 2):
    return abs(coord_1 - coord_2) <= leeway


def adjacent_cells(cell_1: Cell, cell_2: Cell) -> bool:
    """
    Compute if two cells are adjacent
    :param cell_1: first cell object
    :param cell_2: second cell object
    :return: boolean indicating if cells are adjacent
    """
    if not ((0.98 <= (cell_1.width / cell_2.width) <= 1.02) or (0.98 <= (cell_1.height / cell_2.height) <= 1.02)):
        return False

    # Checking if one cell is to the left of the other
    if cell_1.x2 < cell_2.x1 or cell_2.x2 < cell_1.x1:
        return False

    # Checking if one cell is above the other
    if cell_1.y2 < cell_2.y1 or cell_2.y2 < cell_1.y1:
        return False

    # Check if cell1 is within cell2
    if cell_1.x1 > cell_2.x1 and cell_1.x2 < cell_2.x2 and cell_1.y1 > cell_2.y1 and cell_1.y2 < cell_2.y2:
        return False

    # Conditions for cells to be adjacent:
    return (
            coordinate_approximately_equal(cell_1.x1, cell_2.x2) or
            coordinate_approximately_equal(cell_1.x2, cell_2.x1) or
            coordinate_approximately_equal(cell_1.y1, cell_2.y2) or
            coordinate_approximately_equal(cell_1.y2, cell_2.y1)
    )

    # Check correspondence on vertical borders
    overlapping_y = min(cell_1.y2, cell_2.y2) - max(cell_1.y1, cell_2.y1)
    diff_x = min(abs(cell_1.x2 - cell_2.x1),
                 abs(cell_1.x1 - cell_2.x2),
                 abs(cell_1.x1 - cell_2.x1),
                 abs(cell_1.x2 - cell_2.x2))

    # Check correspondence on horizontal borders
    overlapping_x = min(cell_1.x2, cell_2.x2) - max(cell_1.x1, cell_2.x1)
    diff_y = min(abs(cell_1.y2 - cell_2.y1),
                 abs(cell_1.y1 - cell_2.y2),
                 abs(cell_1.y1 - cell_2.y1),
                 abs(cell_1.y2 - cell_2.y2))

    if (overlapping_y > 50 and diff_x <= min(min(cell_1.width, cell_2.width) * 0.05, 5)) or \
            (overlapping_x > 50 and diff_y <= min(min(cell_1.height, cell_2.height) * 0.05, 5)):
        return True

    return False


def cluster_cells_in_tables(cells: List[Cell]) -> List[List[Cell]]:
    """
    Based on adjacent cells, create clusters of cells that corresponds to tables
    :param cells: list cells in image
    :return: list of list of cells, representing several clusters of cells that form a table
    """
    # Loop over all cells to create relationships between adjacent cells
    clusters = list()
    for i in range(len(cells)):
        for j in range(i, len(cells)):
            adjacent = adjacent_cells(cells[i], cells[j])
            # If cells are adjacent, find matching clusters
            if adjacent:
                matching_clusters = [idx for idx, cl in enumerate(clusters) if {i, j}.intersection(cl)]
                if matching_clusters:
                    remaining_clusters = [cl for idx, cl in enumerate(clusters) if idx not in matching_clusters]
                    new_cluster = {i, j}.union(*[cl for idx, cl in enumerate(clusters) if idx in matching_clusters])
                    clusters = remaining_clusters + [new_cluster]
                else:
                    clusters.append({i, j})

    # Return list of cell objects
    list_table_cells = [[cells[idx] for idx in cl] for cl in clusters]

    return list_table_cells
