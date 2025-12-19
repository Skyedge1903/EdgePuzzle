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
SOLUTION_CSV = "eternity2_solution_best.csv"
TOTAL_EDGES = 2 * SIZE * (SIZE - 1)

# ==============================
# Chargement des tuiles et rotations
# ==============================
def load_tiles():
    df = pd.read_csv(TILES_CSV, header=None)
    return df.values.astype(np.int16)

def precompute_rotations(tiles):
    N = len(tiles)
    t_rot = np.zeros((N, ROT, 4), dtype=np.int16)
    for p in range(N):
        for r in range(ROT):
            t_rot[p, r] = np.roll(tiles[p], -r)
    return t_rot

# ==============================
# Pré-calcul des compatibilités des couleurs
# ==============================
def precompute_compat(t_rot):
    """Pour chaque couleur, stocke quelles tuiles peuvent s’y attacher"""
    N = t_rot.shape[0]
    compat = [{} for _ in range(4)]  # N, E, S, W
    for d in range(4):
        color_dict = {}
        for i in range(N):
            for r in range(ROT):
                c = t_rot[i, r, d]
                if c not in color_dict:
                    color_dict[c] = []
                color_dict[c].append((i, r))
        compat[d] = color_dict
    return compat

# ==============================
# Score global ultra-rapide
# ==============================
def total_score(grid, t_rot):
    score = 0
    for i in range(SIZE):
        for j in range(SIZE):
            p, r = grid[i, j]
            t = t_rot[p, r]
            if i < SIZE-1:
                p2, r2 = grid[i+1, j]
                if t[2] == t_rot[p2, r2][0]:
                    score += 1
            if j < SIZE-1:
                p2, r2 = grid[i, j+1]
                if t[1] == t_rot[p2, r2][3]:
                    score += 1
    return score

# ==============================
# Initialisation du grid aléatoire
# ==============================
def init_grid(num_tiles):
    grid = np.zeros((SIZE, SIZE, 2), dtype=np.int16)
    for i in range(SIZE):
        for j in range(SIZE):
            grid[i, j, 0] = random.randint(0, num_tiles-1)
            grid[i, j, 1] = random.randint(0, ROT-1)
    return grid

# ==============================
# Monte-Carlo guidé
# ==============================
def monte_carlo_guided(grid, t_rot, compat, num_tiles, iterations=int(1e7)):
    best_grid = grid.copy()
    best_score = total_score(grid, t_rot)
    print(f"Score initial: {best_score}/{TOTAL_EDGES}")
    start_time = time.time()

    for it in range(1, iterations+1):
        # Choisir une case aléatoire
        i, j = random.randint(0, SIZE-1), random.randint(0, SIZE-1)
        p_old, r_old = grid[i, j]

        # Calculer les candidats compatibles avec voisins
        candidates = set()
        neighbors = []
        if i > 0:
            neighbors.append((t_rot[grid[i-1, j, 0], grid[i-1, j, 1], 2], 0))  # Nord du voisin -> Sud
        if i < SIZE-1:
            neighbors.append((t_rot[grid[i+1, j, 0], grid[i+1, j, 1], 0], 2))  # Sud du voisin -> Nord
        if j > 0:
            neighbors.append((t_rot[grid[i, j-1, 0], grid[i, j-1, 1], 1], 3))  # Ouest du voisin -> Est
        if j < SIZE-1:
            neighbors.append((t_rot[grid[i, j+1, 0], grid[i, j+1, 1], 3], 1))  # Est du voisin -> Ouest

        # Intersection des sets compatibles
        for idx, (color, dir_opposite) in enumerate(neighbors):
            poss = set(compat[dir_opposite].get(color, []))
            if idx == 0:
                candidates = poss
            else:
                candidates = candidates.intersection(poss)
        if not candidates:
            candidates = set((i2, r2) for i2 in range(num_tiles) for r2 in range(ROT))
        chosen = random.choice(list(candidates))
        grid[i, j] = chosen

        # Score et sauvegarde
        if it % 1000 == 0:
            total = total_score(grid, t_rot)
            if total > best_score:
                best_score = total
                best_grid = grid.copy()
                elapsed = time.time() - start_time
                print(f"Iteration {it}, temps: {elapsed:.1f}s, nouveau meilleur score: {best_score}/{TOTAL_EDGES}")
                save_solution_csv(best_grid)
    return best_grid, best_score

# ==============================
# Sauvegarde CSV
# ==============================
def save_solution_csv(grid):
    with open(SOLUTION_CSV, mode='w', newline='') as f:
        writer = csv.writer(f)
        for i in range(SIZE):
            for j in range(SIZE):
                p, r = grid[i, j]
                writer.writerow([i, j, p+1, r])

# ==============================
# Main
# ==============================
def main():
    tiles = load_tiles()
    t_rot = precompute_rotations(tiles)
    compat = precompute_compat(t_rot)
    grid = init_grid(len(tiles))
    best_grid, best_score = monte_carlo_guided(grid, t_rot, compat, len(tiles), iterations=int(1e7))
    print(f"Meilleur score final: {best_score}/{TOTAL_EDGES}")
    save_solution_csv(best_grid)

if __name__ == "__main__":
    main()
