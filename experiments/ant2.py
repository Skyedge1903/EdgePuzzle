import csv, random, time, copy, multiprocessing
import numpy as np
from collections import deque

# ================= CONFIG =================
GRID = 16
ANTS = 32
ALPHA = 1.0      # pheromone weight
BETA = 3.0       # heuristic weight
RHO_GLOBAL = 0.2
EVAP = 0.02
LOG_EVERY = 5
FIXED_TILE = (8, 7, 138, 3)

# ================ CORE ====================
DIRS = [(-1,0,0,2),(0,1,1,3),(1,0,2,0),(0,-1,3,1)]

class Tile:
    def __init__(s,i,c):
        s.i=i
        s.cols = [c[-k:] + c[:-k] for k in range(4)]

class Cell:
    def __init__(s,opts): s.o=set(opts)
    def f(s): return len(s.o)==1
    def fail(s): return not s.o

class Grid:
    def __init__(s,tiles):
        s.t=tiles; s.N=len(tiles)
        opts=[(i,r) for i in range(s.N) for r in range(4)]
        s.g=[[Cell(opts) for _ in range(GRID)] for _ in range(GRID)]
        s.fixed=0

    def inb(s,r,c): return 0<=r<GRID and 0<=c<GRID

    def ok(s,r,c,tr):
        t,rot=tr; col=s.t[t].cols[rot]
        for dr,dc,i,j in DIRS:
            nr,nc=r+dr,c+dc
            if not s.inb(nr,nc):
                if col[i]!=-1: return False
            else:
                n=s.g[nr][nc]
                if n.f():
                    nt,nr2=next(iter(n.o))
                    if col[i]!=s.t[nt].cols[nr2][j]: return False
        return True

    def local_match(s,r,c,tr):
        t,rot=tr; col=s.t[t].cols[rot]; m=0
        for dr,dc,i,j in DIRS:
            nr,nc=r+dr,c+dc
            if s.inb(nr,nc) and s.g[nr][nc].f():
                nt,nr2=next(iter(s.g[nr][nc].o))
                if col[i]==s.t[nt].cols[nr2][j]: m+=1
        return m

    def set(s,r,c,tr):
        t,rot=tr
        s.g[r][c].o={tr}; s.fixed+=1
        # remove t from all other cells
        for i in range(GRID):
            for j in range(GRID):
                if (i,j)!=(r,c):
                    for ro in range(4):
                        s.g[i][j].o.discard((t,ro))
        # propagate constraints with full propagation
        queue = deque()
        for dr,dc,_,_ in DIRS:
            nr,nc=r+dr,c+dc
            if s.inb(nr,nc) and not s.g[nr][nc].f():
                queue.append((nr,nc))
        while queue:
            pr,pc = queue.popleft()
            if s.g[pr][pc].f(): continue
            old_len = len(s.g[pr][pc].o)
            s.g[pr][pc].o = {p for p in s.g[pr][pc].o if s.ok(pr,pc,p)}
            new_len = len(s.g[pr][pc].o)
            if new_len < old_len:
                for dr,dc,_,_ in DIRS:
                    nr,nc=pr+dr,pc+dc
                    if s.inb(nr,nc) and not s.g[nr][nc].f():
                        queue.append((nr,nc))
            if new_len == 1 and old_len > 1:
                tr2 = next(iter(s.g[pr][pc].o))
                t2,rot2 = tr2
                s.fixed +=1
                # remove t2 from all other cells
                for i in range(GRID):
                    for j in range(GRID):
                        if (i,j)!=(pr,pc):
                            for ro in range(4):
                                s.g[i][j].o.discard((t2,ro))
                # add its neighbors to queue
                for dr,dc,_,_ in DIRS:
                    nr,nc=pr+dr,pc+dc
                    if s.inb(nr,nc) and not s.g[nr][nc].f():
                        queue.append((nr,nc))

    def score(s):
        sc=0
        for r in range(GRID):
            for c in range(GRID):
                if s.g[r][c].f():
                    t,rot=next(iter(s.g[r][c].o)); col=s.t[t].cols[rot]
                    for dr,dc,i,j in DIRS:
                        nr,nc=r+dr,c+dc
                        if s.inb(nr,nc) and s.g[nr][nc].f():
                            nt,nr2=next(iter(s.g[nr][nc].o))
                            if col[i]==s.t[nt].cols[nr2][j]: sc+=1
        return sc//2

# =============== ANT ======================
class Ant:
    def __init__(s,pher,base): s.p=pher; s.g=copy.deepcopy(base)

    def run(s):
        cells=[(r,c) for r in range(GRID) for c in range(GRID)]
        while cells:
            # choose most constrained cell
            r,c=min(cells,key=lambda x: len(s.g.g[x[0]][x[1]].o))
            cells.remove((r,c))
            cell=s.g.g[r][c]
            if cell.f() or cell.fail(): continue
            opts=list(cell.o)
            weights = []; valid_tr = []
            for tr in opts:
                if not s.g.ok(r,c,tr): continue
                t,rot = tr
                pher = s.p[r,c,t,rot] ** ALPHA
                heu = (1 + s.g.local_match(r,c,tr)) ** BETA
                weights.append(pher * heu)
                valid_tr.append(tr)
            if not weights: continue
            probs = np.array(weights) / sum(weights)
            chosen_idx = np.random.choice(len(valid_tr), p=probs)
            tr = valid_tr[chosen_idx]
            s.g.set(r,c,tr)
        return s.g

def run_ant(ant):
    return ant.run()

# =============== SOLVER ===================
def solve(csv_file, it=2000):
    tiles=[]
    with open(csv_file) as f:
        for i,r in enumerate(csv.reader(f)): tiles.append(Tile(i,list(map(int,r))))
    base=Grid(tiles)
    r,c,t,rot=FIXED_TILE; base.set(r,c,(t,rot))

    pher=np.full((GRID,GRID,len(tiles),4),1/(len(tiles)*4))

    best=None; best_s=-1; start=time.time()
    for itn in range(1,it+1):
        ants=[Ant(pher,base) for _ in range(ANTS)]
        with multiprocessing.Pool() as pool:
            sols = pool.map(run_ant, ants)
        sol=max(sols,key=lambda g:(g.score(),g.fixed))
        sc=sol.score()*4 + sol.fixed
        if sc>best_s:
            best_s, best=sc, sol
            print(f"[+] New best | iter={itn} score={best.score()} fixed={best.fixed}")
        if itn%LOG_EVERY==0:
            dt=time.time()-start
            print(f"[LOG] iter={itn} best_score={best.score()} fixed={best.fixed} time={dt:.1f}s")
        # global pheromone update (elitist)
        for r in range(GRID):
            for c in range(GRID):
                if sol.g[r][c].f():
                    t,ro=next(iter(sol.g[r][c].o))
                    pher[r,c,t,ro]=(1-RHO_GLOBAL)*pher[r,c,t,ro]+RHO_GLOBAL*(sc/1000)
        # evaporation
        pher*=(1-EVAP)
        if best.fixed==GRID*GRID: break
    return best

# =============== RUN ======================
if __name__=='__main__':
    sol=solve('data/eternity2/eternity2_256.csv')
    print('FINAL | Score:',sol.score(),'Fixed:',sol.fixed)