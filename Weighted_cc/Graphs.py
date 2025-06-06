import math
from collections import defaultdict
import copy
import decimal
from decimal import Decimal
decimal.getcontext().rounding = "ROUND_HALF_UP"
class Graph:
    def __init__(self, filename):
        self.num_e=0
        self.graph = defaultdict(list)
        self.cycles = []
        self.nodelist = []
        self.paths = defaultdict(list)
        self.start = ''
        self.ddG = defaultdict(decimal.Decimal)
        self.ddG_cc = defaultdict(list)
        self.ddG_save = defaultdict(decimal.Decimal)
        self.err = defaultdict(decimal.Decimal) #pair-err
        self.weight = defaultdict(list)
        self.print_e = defaultdict(decimal.Decimal)
        if filename is not None:
            fp=open(filename)
            try:
                for line in fp:
                    data = line.strip().split()
                    if len(data)==3:
                        weight="no"
                    elif len(data)>3:
                        weight="yes"
                    elif len(data)<3:
                        raise Exception("input error")
                        exit()
                    self.addEdge(data,weight)
                    self.num_e += 1
            finally:
                fp.close()
                Exception("Illegal input! Please check your input file.")
        else:
            print("Error: No input files")
            exit()
#        if len(data) > 3:
#            warnings.warn("Please make sure 4th column in input is standard deviation generated by BAR ")


        self.V=list(self.graph.keys())
        self.cycleset= set()



    def addEdge(self, data,weight):
        mol1, mol2, b_ddG=data[0:3]
        self.graph[mol1].append(mol2)
        self.graph[mol2].append(mol1)
        self.ddG[(mol1, mol2)] = decimal.Decimal(b_ddG)
        self.ddG[(mol2, mol1)] = -1*decimal.Decimal(b_ddG)
        self.print_e[(mol1,mol2)]=0
        self.ddG_save[(mol1, mol2)] = decimal.Decimal(0)
        self.ddG_save[(mol2, mol1)] = decimal.Decimal(0)
        self.weight[(mol1,mol2)].append(decimal.Decimal(1))
        self.weight[(mol2,mol1)].append(decimal.Decimal(1))
        self.err[(mol1,mol2)]=-1
        self.err[(mol2,mol1)]=-1
        self.ddG_cc[(mol1, mol2)].append(decimal.Decimal(b_ddG))
        self.ddG_cc[(mol2, mol1)].append(-1 * decimal.Decimal(b_ddG))
        if weight=="yes":#if bar_std is provided, compare bar_std with single pair std
#            warnings.warn("Please make sure 4th colunma data is BAR std")
            self.err[(mol1,mol2)]=decimal.Decimal(data[3])
            self.err[(mol2,mol1)]=decimal.Decimal(data[3])
            w_lst=data[3:]
            for i in range(0,len(w_lst)):
                self.weight[(mol1, mol2)].append(decimal.Decimal(w_lst[i])**2)
                self.weight[(mol2, mol1)].append(decimal.Decimal(w_lst[i])**2)
                self.ddG_cc[(mol1, mol2)].append(decimal.Decimal(b_ddG))
                self.ddG_cc[(mol2, mol1)].append(-1*decimal.Decimal(b_ddG))
        self.weight_num=len(self.weight[(mol1,mol2)])

    def getAllPathsUtil(self, u, d, visited, path, iscycle=False):
        self.num_iteration += 1
        if iscycle:
            if self.num_iteration > 1:
                visited[u] = True
        else:
            visited[u] = True
            if self.num_iteration == 1:
                self.start = u
        path.append(u)
        if self.num_iteration > 1 and u == d:
            if iscycle:
                if len(path) > 3:
                    path_s=copy.deepcopy(path)
                    path_s.sort()
                    path_str={''.join(path_s)}
                    if not path_str <self.cycleset:
                        self.cycles.append(copy.deepcopy(path))
                        self.cycleset.add(''.join(path_s))
            else:
                self.paths[(self.start, d)].append(copy.deepcopy(path))

        else:
            for i in self.graph[u]:
                if visited[i] == False:
                    self.getAllPathsUtil(i, d, visited, path, iscycle=iscycle)
        path.pop()
        visited[u] = False

    def getAllCyles(self):
        visit = dict(zip(self.graph.keys(), [False] * (len(self.graph))))
        for mol in self.V:
            visited=visit
            path=[]
            self.num_iteration=0
            self.getAllPathsUtil(mol, mol, visited, path, iscycle=True)
            visit[mol] = True
        return



    def getDelta(self,n, cycle_list):
        delta = decimal.Decimal(0.0)
        edges = 0
        std=decimal.Decimal(0)
        for i in range(len(cycle_list) - 1):
            mol1, mol2 = cycle_list[i:i + 2]
            delta += self.ddG_cc[mol1, mol2][n]
            edges += 1
            std += self.weight[mol1,mol2][n]
        return delta, edges , std

    def CycleClosure(self,n,edge_error):
        # cycle closure for all the cycles of a single molecule
        for k in range(len(self.cycles)):
            cycle_list=self.cycles[k]
            delta,edges,std_sum=self.getDelta(n,cycle_list)
            single_err=abs(delta/decimal.Decimal(math.sqrt(edges)))
            for i in range(len(cycle_list) - 1):
                mol1, mol2 = cycle_list[i:i + 2]
                if edge_error==True:
                    if edges > 6: #ignore cycles more than 6edges
                        continue
                    if single_err >self.err[mol1,mol2]:
                        self.err[mol1,mol2] = single_err
                        self.err[mol2, mol1] = single_err
                    continue
                scale = self.weight[mol1,mol2][n]/std_sum
                ene = self.ddG_cc[mol1,mol2][n]
                newene = ene - scale * delta
                self.ddG_cc[mol1, mol2][n] = newene
                self.ddG_cc[mol2, mol1][n] = -newene


    def chk_continue(self,n, tol=0.001):
        for curr_key in self.ddG.keys():
            if abs(self.ddG_save[curr_key] - self.ddG_cc[curr_key][n]) > tol:
                return True
        return False

    def iterateCycleClosure(self, minimum_cycles=2):
        for n in range(0,self.weight_num):
            i = 0
            while i < minimum_cycles or self.chk_continue(n,0.001) :
                cal_error=True if (i==0) else False #if the first iteration, calculate pair error
                for curr_key in self.ddG.keys():            #save the current energy value for the next step
                    self.ddG_save[curr_key] = self.ddG_cc[curr_key][n]
                self.CycleClosure(n,cal_error)
                i += 1
        for molpair in self.print_e:
            self.nodelist.append([molpair[0], molpair[1], self.err[molpair]])

    def printEnePairs(self):

        print("Printing Pairwise Energies:")
        print('{:8s} {:10s}'.format('Pair', 'ddG_cc'),end='')
        for k in range(1,self.weight_num):
            print(' {:^10s}'.format("ddG_wcc"+str(k)),end='')
        print(' {:^10s}'.format('pair_error'))
        for molpair in self.print_e:
            print('{:>2s}-{:2s}{:^14.4f}'.format(molpair[0],molpair[1], self.ddG_cc[molpair][0],),end='')
            for k in range(1,self.weight_num):
                print(" {:^10.4f}".format(self.ddG_cc[molpair][k]),end="")
            print('{:^10.4f}'.format(Decimal(self.err[molpair]).quantize(decimal.Decimal('0.00'))))
            #self.nodelist.append([molpair[0], molpair[1], self.err[molpair]])
        print("*" * 100)



