from queue import Queue

fsize_x = 40
fsize_y = 30

#helpers 
def dist_x(a,b): # "sqare distance"
    r = 0
    for x in range(len(a)):
        a[x] = abs(b[x]-a[x])
    return max(a)
def step(xc,yc): 
    r = []
    if xc + 1 < fsize_x:
        r.append([xc+1,yc])
    if xc - 1 >= 0:
        r.append([xc-1,yc])
    if yc + 1 < fsize_y:
        r.append([xc,yc+1])
    if yc - 1 >= 0:
        r.append([xc,yc-1])
    return r;
def bfs(t,prep): #main function
    q = Queue()
    q.put(t)
    prev = [[[-1,-1] for x in range(fsize_y)] for y in range(fsize_x)]
    dist_g = [[-1 for x in range(fsize_y)] for y in range(fsize_x)]
    #obstacle avoidance (set obstacle points as unreachable) (columns are actually used as sqares)
    for x in range(fsize_x):
        for y in range(fsize_y):
            for z in range(len(prep)):
                if dist_x([x,y],prep[z][0]) < prep[z][1]:
                    dist_g[x][y] = -2
    #calculate prev and dist arrays (using standard bfs)
    prev[t[0]][t[1]] = [-2,-2]
    dist_g[t[0]][t[1]] = 0
    while(not q.empty()):
        v = q.get()
        s = step(v[0],v[1])
        for x in range(len(s)):
            if(dist_g[s[x][0]][s[x][1]] == -1):
                dist_g[s[x][0]][s[x][1]] = dist_g[v[0]][v[1]]+1
                prev[s[x][0]][s[x][1]] = v
                q.put(s[x])
    #print(*prev,sep = '\n')
    #print(*dist_g,sep = '\n')
    #way compressing : if going on straight line, compress the whole line to a single step
    for x in range(fsize_x):
        for y in range(fsize_y):
            if(prev[x][y][0] >= 0 and prev[x][y][1] >= 0):
                d = [0,0]
                d[0] = prev[x][y][0] - x 
                d[1] = prev[x][y][1] - y
                while(prev[prev[x][y][0]][prev[x][y][1]] == [prev[x][y][0]+d[0],prev[x][y][1]+d[1]]):
                    prev[x][y] = prev[prev[x][y][0]][prev[x][y][1]]
    #print(*prev,sep = '\n')
    return prev
