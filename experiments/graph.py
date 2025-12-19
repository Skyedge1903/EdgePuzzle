import numpy as np
import pandas as pd
import random
from copy import deepcopy

# ==============================
# Paramètres
# ==============================
SIZE = 16
ROT = 4
GRAY = -1

TILES_CSV = "data/eternity2/eternity2_256.csv"
OUTPUT_CSV = "eternity2_solution_attempt.csv"

DIRS = [(-1,0),(0,1),(1,0),(0,-1)]  # N,E,S,W
OPP = [2,3,0,1]

# Hill climbing / SA parameters
ITER = 100000  # nombre d'itérations
T0 = 1.0
T_FINAL = 1e-4
ALPHA = 0.999

# ==============================
# Chargement des pièces et rotations
# ==============================
tiles = pd.read_csv(TILES_CSV, header=None).values.astype(int)
NTILES = len(tiles)

t_rot = np.zeros((NTILES*ROT,4), dtype=int)
for p in range(NTILES):
    for r in range(ROT):
        t_rot[p*ROT+r] = np.roll(tiles[p], -r)

# ==============================
# Initialisation grille et mapping
# ==============================
grid_pos = {}
idx = 0
for i in range(SIZE):
    for j in range(SIZE):
        grid_pos[idx] = (i,j)
        idx +=1
pos_to_piece = {v:k for k,v in grid_pos.items()}

# ==============================
# Placement initial glouton
# ==============================
piece_scores = []
for p in range(NTILES):
    piece_scores.append((len(set(c for c in tiles[p] if c!=GRAY)), p))
piece_scores.sort(reverse=True)  # pièces les plus contraintes d'abord
rotations = {}

for _,p in piece_scores:
    i,j = grid_pos[p]
    best_r, best_match = 0,-1
    for r in range(ROT):
        tp = t_rot[p*ROT + r]
        score = 0
        for d,(di,dj) in enumerate(DIRS):
            ni,nj = i+di,j+dj
            if 0<=ni<SIZE and 0<=nj<SIZE:
                q = pos_to_piece[(ni,nj)]
                if q in rotations:
                    tq = t_rot[q*ROT + rotations[q]]
                    if tp[d]==tq[OPP[d]]: score+=1
        if score>best_match:
            best_match=score
            best_r=r
    rotations[p]=best_r

# ==============================
# Fonction score officiel rapide
# ==============================
def compute_score(rotations, grid_pos):
    score = 0
    for p in range(NTILES):
        i,j = grid_pos[p]
        tp = t_rot[p*ROT + rotations[p]]
        for d,(di,dj) in enumerate(DIRS[:2]):  # N et E suffisent
            ni,nj = i+di,j+dj
            if 0<=ni<SIZE and 0<=nj<SIZE:
                q = pos_to_piece[(ni,nj)]
                tq = t_rot[q*ROT + rotations[q]]
                if tp[d]==tq[OPP[d]]: score+=1
    return score

current_score = compute_score(rotations, grid_pos)
rotations_best = deepcopy(rotations)
score_best = current_score
print(f"Score initial glouton : {current_score}")

# ==============================
# Hill climbing / SA ciblé sur pièces mal alignées
# ==============================
T = T0
for step in range(ITER):
    # Liste des pièces mal alignées
    bad_pieces = [p for p in range(NTILES) if sum(
        1 for d,(di,dj) in enumerate(DIRS[:2]) if 0<=grid_pos[p][0]+di<SIZE and 0<=grid_pos[p][1]+dj<SIZE and
        t_rot[p*ROT + rotations[p]][d]==t_rot[pos_to_piece[(grid_pos[p][0]+di,grid_pos[p][1]+dj)]*ROT + rotations[pos_to_piece[(grid_pos[p][0]+di,grid_pos[p][1]+dj)]]][OPP[d]]
    ) < sum(1 for c in tiles[p] if c!=GRAY)]
    if not bad_pieces:
        break

    p = random.choice(bad_pieces)

    if random.random()<0.5:
        # changer rotation
        old_r = rotations[p]
        new_r = random.randint(0,ROT-1)
        rotations[p]=new_r
        new_score = compute_score(rotations, grid_pos)
        delta = new_score - current_score
        if delta>0 or (delta<=0 and random.random()<T):
            current_score=new_score
            if current_score>score_best:
                score_best=current_score
                rotations_best=deepcopy(rotations)
        else:
            rotations[p]=old_r
    else:
        # swap avec une autre pièce mal alignée
        q = random.choice(bad_pieces)
        if q==p: continue
        grid_pos[p],grid_pos[q] = grid_pos[q],grid_pos[p]
        new_score = compute_score(rotations, grid_pos)
        delta = new_score - current_score
        if delta>0 or (delta<=0 and random.random()<T):
            current_score=new_score
            if current_score>score_best:
                score_best=current_score
                rotations_best=deepcopy(rotations)
        else:
            grid_pos[p],grid_pos[q] = grid_pos[q],grid_pos[p]

    T*=ALPHA
    if step%2000==0:
        print(f"Step {step}, T={T:.5f}, score_best={score_best}")

# ==============================
# Export CSV final
# ==============================
rows=[]
for p in range(NTILES):
    i,j = grid_pos[p]
    rows.append([i,j,p+1,rotations_best[p]])  # 1-based
pd.DataFrame(rows).to_csv(OUTPUT_CSV,header=False,index=False)
print(f"Export terminé : {OUTPUT_CSV}")
print(f"Score final estimé : {score_best}")
