import numpy as np
import pandas as pd
import random
import csv
import time

# ==============================
# Paramètres
# ==============================
SIZE = 16
ROT = 4
TILES_CSV = "data/eternity2/eternity2_256.csv"
SOLUTION_CSV = "eternity2_solution_attempt.csv"
TOTAL_EDGES = 2 * SIZE * (SIZE - 1)


# ==============================
# Chargement des tuiles et pré-calcul rotations
# ==============================
def load_tiles():
    df = pd.read_csv(TILES_CSV, header=None)
    return df.values.astype(np.int16)


def precompute_rotations(tiles):
    """Pré-calculer toutes les rotations de chaque tuile"""
    N = len(tiles)
    t_rot = np.zeros((N, ROT, 4), dtype=np.int16)
    for p in range(N):
        for r in range(ROT):
            t_rot[p, r] = np.roll(tiles[p], -r)
    return t_rot


# ==============================
# Score local et global
# ==============================
def local_score(grid, t_rot, i, j):
    p, r = grid[i][j]
    t = t_rot[p, r]
    score = 0
    if i > 0:
        p2, r2 = grid[i - 1][j]
        if t[0] == t_rot[p2, r2][2]:
            score += 1
    if i < SIZE - 1:
        p2, r2 = grid[i + 1][j]
        if t[2] == t_rot[p2, r2][0]:
            score += 1
    if j > 0:
        p2, r2 = grid[i][j - 1]
        if t[3] == t_rot[p2, r2][1]:
            score += 1
    if j < SIZE - 1:
        p2, r2 = grid[i][j + 1]
        if t[1] == t_rot[p2, r2][3]:
            score += 1
    return score


def total_score(grid, t_rot):
    score = 0
    for i in range(SIZE):
        for j in range(SIZE):
            p, r = grid[i][j]
            t = t_rot[p, r]
            if i < SIZE - 1:
                p2, r2 = grid[i + 1][j]
                if t[2] == t_rot[p2, r2][0]:
                    score += 1
            if j < SIZE - 1:
                p2, r2 = grid[i][j + 1]
                if t[1] == t_rot[p2, r2][3]:
                    score += 1
    return score


# ==============================
# Génération initiale intelligente
# ==============================
def init_grid(num_tiles, t_rot):
    grid = [[None for _ in range(SIZE)] for _ in range(SIZE)]
    unused_tiles = set(range(num_tiles))

    # Placer les coins (-1)
    corners = [(0, 0), (0, SIZE - 1), (SIZE - 1, 0), (SIZE - 1, SIZE - 1)]
    for i, j in corners:
        found = False
        for p in list(unused_tiles):
            for r in range(ROT):
                t = t_rot[p, r]
                if ((i == 0 and t[0] == -1) or (i == SIZE - 1 and t[2] == -1)) and \
                        ((j == 0 and t[3] == -1) or (j == SIZE - 1 and t[1] == -1)):
                    grid[i][j] = (p, r)
                    unused_tiles.remove(p)
                    found = True
                    break
            if found: break
        if not found:
            raise ValueError(f"Aucun coin valide pour {i, j}")

    # Placer les bords (couleur -1 côté extérieur)
    for i in range(1, SIZE - 1):
        # Haut
        for p in list(unused_tiles):
            for r in range(ROT):
                t = t_rot[p, r]
                if t[0] == -1:
                    grid[0][i] = (p, r)
                    unused_tiles.remove(p)
                    break
            if grid[0][i] is not None: break
        # Bas
        for p in list(unused_tiles):
            for r in range(ROT):
                t = t_rot[p, r]
                if t[2] == -1:
                    grid[SIZE - 1][i] = (p, r)
                    unused_tiles.remove(p)
                    break
            if grid[SIZE - 1][i] is not None: break
        # Gauche
        for p in list(unused_tiles):
            for r in range(ROT):
                t = t_rot[p, r]
                if t[3] == -1:
                    grid[i][0] = (p, r)
                    unused_tiles.remove(p)
                    break
            if grid[i][0] is not None: break
        # Droite
        for p in list(unused_tiles):
            for r in range(ROT):
                t = t_rot[p, r]
                if t[1] == -1:
                    grid[i][SIZE - 1] = (p, r)
                    unused_tiles.remove(p)
                    break
            if grid[i][SIZE - 1] is not None: break

    # Remplir le reste aléatoirement
    positions = [(i, j) for i in range(1, SIZE - 1) for j in range(1, SIZE - 1) if grid[i][j] is None]
    random.shuffle(positions)
    for i, j in positions:
        p = unused_tiles.pop()
        r = random.randint(0, ROT - 1)
        grid[i][j] = (p, r)

    return grid


# ==============================
# Monte-Carlo avec contraintes
# ==============================
def monte_carlo_constraints(grid, t_rot, num_tiles, iterations=int(1e7)):
    best_grid = [row[:] for row in grid]
    best_score = total_score(grid, t_rot)
    print(f"Score initial: {best_score}/{TOTAL_EDGES}")
    start_time = time.time()

    # Positions non-corner pour swap
    non_corners = [(i, j) for i in range(SIZE) for j in range(SIZE) if
                   (i, j) not in [(0, 0), (0, SIZE - 1), (SIZE - 1, 0), (SIZE - 1, SIZE - 1)]]

    for it in range(1, iterations + 1):
        # Choisir deux cases aléatoires pour swap
        (i1, j1), (i2, j2) = random.sample(non_corners, 2)
        old1, old2 = grid[i1][j1], grid[i2][j2]
        grid[i1][j1], grid[i2][j2] = old2, old1

        # Optimiser rotation locale
        for (ii, jj) in [(i1, j1), (i2, j2)]:
            p, r = grid[ii][jj]
            best_local_score = local_score(grid, t_rot, ii, jj)
            best_r = r
            for rot in range(ROT):
                grid[ii][jj] = (p, rot)
                score = local_score(grid, t_rot, ii, jj)
                if score > best_local_score:
                    best_local_score = score
                    best_r = rot
            grid[ii][jj] = (p, best_r)

        # Vérifier score total
        total = total_score(grid, t_rot)
        if total > best_score:
            best_score = total
            best_grid = [row[:] for row in grid]
            elapsed = time.time() - start_time
            print(f"Iteration {it}, temps: {elapsed:.1f}s, nouveau meilleur score: {best_score}/{TOTAL_EDGES}")
            save_solution_csv(best_grid)
        else:
            # Revert swap si pas meilleur
            grid[i1][j1], grid[i2][j2] = old1, old2

    return best_grid, best_score


# ==============================
# Sauvegarde CSV
# ==============================
def save_solution_csv(grid):
    with open(SOLUTION_CSV, mode='w', newline='') as f:
        writer = csv.writer(f)
        for i in range(SIZE):
            for j in range(SIZE):
                p, r = grid[i][j]
                writer.writerow([i, j, p + 1, r])


# ==============================
# Main
# ==============================
def main():
    tiles = load_tiles()
    t_rot = precompute_rotations(tiles)
    grid = init_grid(len(tiles), t_rot)
    best_grid, best_score = monte_carlo_constraints(grid, t_rot, len(tiles), iterations=int(1e7))
    print(f"Meilleur score final trouvé: {best_score}/{TOTAL_EDGES}")
    save_solution_csv(best_grid)


if __name__ == "__main__":
    main()
