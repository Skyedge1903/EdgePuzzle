import csv, random, time, copy
import numpy as np

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
    def __init__(s,i,c): s.i=i; s.c=c
    def r(s,k): return s.c[-k:]+s.c[:-k]

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
        t,rot=tr; col=s.t[t].r(rot)
        for dr,dc,i,j in DIRS:
            nr,nc=r+dr,c+dc
            if not s.inb(nr,nc):
                if col[i]!=-1: return False
            else:
                n=s.g[nr][nc]
                if n.f():
                    nt,nr2=next(iter(n.o))
                    if col[i]!=s.t[nt].r(nr2)[j]: return False
        return True

    def local_match(s,r,c,tr):
        t,rot=tr; col=s.t[t].r(rot); m=0
        for dr,dc,i,j in DIRS:
            nr,nc=r+dr,c+dc
            if s.inb(nr,nc) and s.g[nr][nc].f():
                nt,nr2=next(iter(s.g[nr][nc].o))
                if col[i]==s.t[nt].r(nr2)[j]: m+=1
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
        # propagate constraints to neighbors
        for dr,dc,_,_ in DIRS:
            nr,nc=r+dr,c+dc
            if s.inb(nr,nc):
                s.g[nr][nc].o={p for p in s.g[nr][nc].o if s.ok(nr,nc,p)}

    def score(s):
        sc=0
        for r in range(GRID):
            for c in range(GRID):
                if s.g[r][c].f():
                    t,rot=next(iter(s.g[r][c].o)); col=s.t[t].r(rot)
                    for dr,dc,i,j in DIRS:
                        nr,nc=r+dr,c+dc
                        if s.inb(nr,nc) and s.g[nr][nc].f():
                            nt,nr2=next(iter(s.g[nr][nc].o))
                            if col[i]==s.t[nt].r(nr2)[j]: sc+=1
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
            tot=0; wheel=[]
            for tr in opts:
                if not s.g.ok(r,c,tr): continue
                pher=s.p[r][c][tr[0]][tr[1]]**ALPHA
                heu=(1+s.g.local_match(r,c,tr))**BETA
                tot+=pher*heu; wheel.append((tot,tr))
            if not wheel: continue
            x=random.random()*tot
            for v,tr in wheel:
                if v>=x:
                    s.g.set(r,c,tr); break
        return s.g

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
        sols=[a.run() for a in ants]
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