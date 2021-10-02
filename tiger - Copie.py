#m=2 # en hauteur
#n=3 # en largeur
nbVariablePerCells=3 # constant
filename=r"test.cnf"
from pprint import pprint
from crocomine_client import CrocomineClient
from itertools import combinations
import subprocess
from subprocess import PIPE
import random
import time


fail=0
success=0

class game:
    def __init__(self):
        self.emergencies={"T":True,"S":True,"C":True}
        self.discoverbuffer=[]
        self.Continue=True
        self.Cases=[]
        self.clauses=[]
        status, msg, grid_infos = croco.new_grid()
        self.unknown_cell=dict()
        if(status!="Err"):
            self.ParseNewGridInfo(grid_infos)
            self.nbVar=nbVariablePerCells*self.dim[0]*self.dim[1] # ok 
            self.initCases()
            self.OnlyOneAnimalPerCase()
            #print(self.clauses)
            self.Start()

    def ParseNewGridInfo(self,infos):
        self.dim=(infos['m'],infos['n']) #2,3
        self.start=(infos['start'][0],infos['start'][1])
        self.animals_count={"T":infos['tiger_count'],"S":infos['shark_count'],"C":infos['croco_count'],-1:True}
        # land count and animal count
        
    def emergency(self,sorted_items):
        Change=False
        print("emergency")
        CellUnknownList=[]
        for line in self.Cases:
            for cell in line:
                if(cell.isKnown()==False):
                    CellUnknownList.append((cell.x,cell.y))
        #print(CellUnknownList)
        for animal in ["T","S","C"]:
            if(self.animals_count[animal]*len(CellUnknownList)<100 and self.emergencies[animal]):
                self.emergencies[animal]=False
                Change=True
                #print("added"+str(animal)+str(len(CellUnknownList)))
                self.AddProximityAnimalInformations(CellUnknownList,self.animals_count[animal],animal)
        if(Change==False):
            self.Montecarlo(sorted_items)

    def Montecarlo(self,sorted_items):
        GuessList=dict()
        goodGuessList=dict()
        ConfirmList=set()
        self.animals_count
        Continue=True
        for line in self.Cases:
            for cell in line:
                if(cell.animal==-1):
                    GuessList[(cell.x,cell.y)]=0
                    goodGuessList[(cell.x,cell.y)]={"T":0,"S":0,"C":0,-1:0}
                else:
                    ConfirmList.add(self.getCell((cell.x,cell.y)))
        random.seed(123)
        Max=(-1,0,0)
        tps1 = time.clock()
        while Max[0]<20 and (time.clock() - tps1)<2:
            Continue=False
            tab=[]
            for i in range(self.animals_count["T"]):
                tab.append("T")
            for i in range(self.animals_count["S"]):
                tab.append("S")
            for i in range(self.animals_count["C"]):
                tab.append("C")
            for i in range(len(GuessList)-self.animals_count["T"]-
                           self.animals_count["S"]-self.animals_count["C"]):
                tab.append(-1)
            animals=(random.sample(tab, k = len(tab)))
            error=False
            for key in GuessList:
                pop=animals.pop()
                if(self.getCell(key).IsAnimalPossible(pop)):
                    GuessList[key]=pop
                else:
                    error=True
                    break
            if(error):
                continue
            for cell in ConfirmList:
                if(cell.animal==-1 and cell.ProxCount==cell.KnownTreat):
                    copyTreat=cell.KnownTreat.copy()
                    neighbours=self.GetNeighbours(cell.x,cell.y)
                    for neighbour in neighbours:
                        if(neighbour in GuessList):
                            if(GuessList[neighbour]!=0):
                                tab[GuessList[neighbour]]+=1
                    if(cell.ProxCount!=copyTreat):
                        #print(cell.ProxCount)
                        #print(copyTreat)
                        Continue=True

            if(Continue==False):
                for key in GuessList:
                    goodGuessList[key][GuessList[key]]+=1
                    if(Max[0]<goodGuessList[key][GuessList[key]]):
                        Max=(goodGuessList[key][GuessList[key]],key[0],key[1],GuessList[key])
        #print(goodGuessList)
        if(Max[0]>0):
            self.guess(Max[1],Max[2],Max[3])
        else:
            self.Montecarlo2(sorted_items)
            
    def Montecarlo2(self,sorted_items):
        print(sorted_items)
        clausetofile(filename,self.nbVar,self.clauses,[])
        cmd = "gophersat-1.1.6.exe"
        for i in range(1):
    
            result = subprocess.run(
                [cmd, filename], stdout=PIPE, check=True, encoding="utf8")
            string = str(result.stdout)
            lines = string.splitlines()

            if lines[1] != "s SATISFIABLE":
                print("error montecarlo unsat")
            else:
                model = lines[2][2:].split(" ")
                print(model)
                for cell in sorted_items:
                    cell_pos=cell[0]
                    T=self.getVariable(cell_pos[0],cell_pos[1],"T",False)
                    S=self.getVariable(cell_pos[0],cell_pos[1],"S",False)
                    C=self.getVariable(cell_pos[0],cell_pos[1],"C",False)
                    if(C in model and S in model and T in model):
                        self.guess(cell_pos[0],cell_pos[1],-1)
                        del self.unknown_cell[cell_pos]
                        return

                for cell in sorted_items:
                    cell_pos=cell[0]
                    T=self.getVariable(cell_pos[0],cell_pos[1],"T",False)
                    S=self.getVariable(cell_pos[0],cell_pos[1],"S",False)
                    C=self.getVariable(cell_pos[0],cell_pos[1],"C",False)
                    if(C in model):
                        self.guess(cell_pos[0],cell_pos[1],"C")
                        del self.unknown_cell[cell_pos]
                        return
                    elif(S in model):
                        self.guess(cell_pos[0],cell_pos[1],"S")
                        del self.unknown_cell[cell_pos]
                        return
                    elif(T in model):
                        self.guess(cell_pos[0],cell_pos[1],"T")
                        del self.unknown_cell[cell_pos]
                        return                         
            
                    
                
        
    def Start(self):
        self.guess(self.start[0],self.start[1],-1)
        while self.Continue:
            reset=False
            while(len(self.discoverbuffer)):
                #print("DebugBuffer")
                pos=self.discoverbuffer.pop()
                if(self.checkChord(pos)):
                    chordcell=self.getCell(pos)
                    self.guess(pos[0],pos[1],-2)
                
            dictionary_items = self.unknown_cell.items()
            sorted_items = sorted(dictionary_items, key=lambda tup: tup[1],reverse=True)
            #print(sorted_items)
            for cell in sorted_items:

                if(reset):
                    break
                pos=cell[0]
                cell_object=self.getCell(pos)
                if(cell_object.animal==-1 and cell_object.getProxCount()[0]==False):
                    for animal in ["T","S","C",-1]:
                        if(self.animals_count[animal] and cell_object.IsAnimalPossible(animal)): # if count_of_animal is not 0
                            clausetofile(filename,self.nbVar,self.clauses,self.check_Animal_In_Cell(pos[0],pos[1],animal))
                            if(exec_gophersat(filename)):
                                self.guess(pos[0],pos[1],animal)
                                del self.unknown_cell[pos]
                                reset=True
                                break
                            else:
                                self.unknown_cell[pos]-=1
                else:
                    del self.unknown_cell[pos]

            if(reset==False):
                self.emergency(sorted_items)
                    
        return

    def IncrementHeuristicCell(self,cell):
        pos=(cell.x,cell.y)
        #print("incr"+str(pos))
        #print(self.unknown_cell)
        if pos in self.unknown_cell:

            self.unknown_cell[pos] = self.unknown_cell[pos]+1
            #print(self.unknown_cell)
        else:
            if(self.getCell(pos).animal==-1):
                self.unknown_cell[pos] = 1

    def SetAnimal(self,cell,animal):
        if(animal==-1):
            return
        elif(animal==0):
            cell.setAnimal(0)
            for i in ["T","S","C"]:
                self.clauses.append(self.getVariable(cell.x,cell.y,i,False)+" 0\n")
        else:
            cell.setAnimal(animal)
            self.clauses.append(self.getVariable(cell.x,cell.y,animal,True)+" 0\n")

    def AddToChordList(self,pos):
        self.discoverbuffer.append(pos)

    def checkChord(self,pos):
        chordcell=self.getCell(pos)
        tab=chordcell.ProxCount.copy()
        neighbours=self.GetNeighbours(pos[0],pos[1])
        unknownneighnb=0
        for neighbour in neighbours:
            neighbourcellAnimal=self.getCell(neighbour).animal
            if(neighbourcellAnimal=="T"):
                tab[0]-=1
            elif(neighbourcellAnimal=="S"):
                tab[1]-=1
            elif(neighbourcellAnimal=="C"):
                tab[2]-=1
            elif(neighbourcellAnimal==-1):
                unknownneighnb+=1
        if(tab[0]<1 and tab[1]<1 and tab[2]<1 and unknownneighnb>0):
            return True
        return False
                
    def guess(self,x,y,t):
        #print("guessed"+str(x)+","+str(y)+","+str(t))
        if(t==-1):
            status, msg, infos = croco.discover(x, y)
            
        elif(t==-2):
            #print("chord"+str(x)+str(y))
            status, msg, infos = croco.chord(x, y)
        else:
            status, msg, infos = croco.guess(x, y,t)
            
            for neighbour in self.GetNeighbours(x, y):
                cell_n=self.getCell(neighbour)
                if(cell_n.AddTreat(t)):
                    self.AddToChordList(neighbour)
             
            self.animals_count[t]-=1
        buffer=[]
        if(status=='OK'):
            #print(infos)
            for info in infos:
                if "pos" in info:
                    tamp=info["pos"]
                    pos=(tamp[0],tamp[1])
                    cell=self.getCell(pos)
                    
                    if "animal" in info:
                        self.SetAnimal(cell,info["animal"])
                        
                    elif "prox_count" in info:
                        self.SetAnimal(cell,0)
                        self.AddProximityKnowledge(cell,info["prox_count"])
                        buffer.append(pos)
                        
                    else:
                        self.IncrementHeuristicCell(cell)
                    
                    if "field" in info:
                        self.AddFieldInformation(cell,info["field"])
              
                #[{'animal': 'T', 'field': 'land', 'pos': [1, 2]},
            if(t==-1):
                self.AddToChordList((x,y))
            for k in buffer:
                self.AddToChordList(k)
                
        elif(status=="GG" or status=="KO"):
            self.Continue=False
            print(status)
            return
            
    def initCases(self):
        #print("dim:"+str(self.dim[0])+str(self.dim[1]))
        for i in range(self.dim[0]):
            self.Cases.append(self.initLigne(i,self.dim[1])) # n element par ligne

    def initLigne(self,x,n):
        tab=[]
        for i in range(n):
            tab.append(Case(x,i))
        return tab

    def getCell(self,coord):
        return self.Cases[coord[0]][coord[1]]

    def check_Animal_In_Cell(self,X,Y,animal):
        if(animal==-1):
            return self.check_No_Animals_In_Cell(X,Y)
        clause=self.getVariable(X,Y,animal,False)+" 0\n"
        return clause

    def check_No_Animals_In_Cell(self,X,Y):
        clause=""
        for animal in ["T","S","C"]:
             clause=clause+self.getVariable(X,Y,animal,True)+" "
        clause =clause+"0\n"
        return clause

    def getVariable(self,x,y,string,positive):
        if(string=="T"):
            clause=1
        elif(string=="S"):
            clause=2
        elif(string=="C"):
            clause=3
        else:
            print("Error bad string in getVariable"+str(string))
        cellnumber=y*self.dim[0]*nbVariablePerCells+x*nbVariablePerCells+clause
        if(positive):
            return str(cellnumber)
        else:
            return str(-(cellnumber))
           
    def OnlyOneAnimalPerCase(self):
        for x in range(self.dim[0]):
            for y in range(self.dim[1]):
                self.clauses.extend(self.OnlyOneAnimalPerCaseByCase(x,y))

    def OnlyOneAnimalPerCaseByCase(self,x,y)  :
        clauses=[]
        #!IsDauphin or !IsTigre  or IsCroco  
        clauses.append(self.getVariable(x,y,"S",False)+" "+self.getVariable(x,y,"T",False)+" "+self.getVariable(x,y,"C",True)+" 0\n")

        #IsDauphin or !IsTigre  or !IsCroco  
        clauses.append(self.getVariable(x,y,"S",True)+" "+self.getVariable(x,y,"T",False)+" "+self.getVariable(x,y,"C",False)+" 0\n")

        #!IsDauphin or IsTigre  or !IsCroco
        clauses.append(self.getVariable(x,y,"S",False)+" "+self.getVariable(x,y,"T",True)+" "+self.getVariable(x,y,"C",False)+" 0\n")

        return clauses

    def isInBound(self,coord):
        (x,y)=coord
        if(x>=0 and x<self.dim[0] and y>=0 and y<self.dim[1]):
            return True
        #print("Debug:Not in bound"+str(x)+str(y))
        return False

    def GetNeighbours(self,x,y):
        neighbours=[]
        for i in [(-1,-1),(-1,0),(-1,1),(0,-1),(0,1),(1,-1),(1,0),(1,1)]:
            neighbour=(x+i[0],y+i[1])
            if(self.isInBound(neighbour)):
                neighbours.append(neighbour)

        return neighbours
    
    def AddProximityKnowledge(self,cell,tab):
        if(cell.getProxCount()[0]==False):
            animal=["T","S","C"]
            cell.setProxCount(tab)
            neighbours=self.GetNeighbours(cell.x,cell.y)
            for i in range(3):
                self.AddProximityAnimalInformations(neighbours,tab[i],animal[i])
        
    def AddProximityAnimalInformations(self,neighbours,nb,animal):
        for comb in combinations(neighbours, len(neighbours)-nb+1):  #At least number of neigh because len(neighbours)-n+1 + n > len(neigh) 
            clause=""
            if (len(comb)):
                for c in comb:
                    clause=clause+self.getVariable(c[0],c[1],animal,True)+" "
                clause=clause+"0\n"
                self.clauses.append(clause)
            
        for comb in combinations(neighbours, nb+1):  # not more then number of neigh 
            clause=""
            if (len(comb)):
                for c in comb:
                    clause=clause+self.getVariable(c[0],c[1],animal,False)+" "
                clause=clause+"0\n"
                self.clauses.append(clause)
        
    def AddFieldInformation(self,case,field):
        if(case.terrain==-1):
            if(field=='sea'):
                self.clauses.extend(self.getVariable(case.x,case.y,"T",False)+" 0\n")
                case.setTerrain(0)
            elif(field=='land'):
                self.clauses.extend(self.getVariable(case.x,case.y,"S",False)+" 0\n")
                case.setTerrain(1)
            else: print("not land nor sea"+field)
        

class Case:

    def __init__(self,x,y): 
        self.terrain=-1  #-1 indeterminé 1 terre 0 ocean  
        self.ProxCount=[-1,-1,-1]   #tigredauphin  croco
        self.KnownTreat=[0,0,0]
        self.animal=-1
        self.x=x 
        self.y=y
        #print("init:"+str(x)+str(y))

    def AddTreat(self,animal):
        if(animal=="T"):
            self.KnownTreat[0]+=1
        elif(animal=="S"):
            self.KnownTreat[1]+=1
        elif(animal=="C"):
            self.KnownTreat[2]+=1
        else:
            print("Unknown Treat")
        if (self.ProxCount[0]==self.KnownTreat[0] and self.ProxCount[1]==self.KnownTreat[1] and self.ProxCount[2]==self.KnownTreat[2]):
            return True
        return False
    def isKnown(self):
        if(self.animal!=-1 or self.ProxCount[0]!=-1):
            return True
        else:
            return False

    def setProxCount(self,tab):
        if(self.x==2 and  self.y==3):
            print("Debug"+str(tab)+str(self.ProxCount))
        self.ProxCount=tab

    def getProxCount(self):
        if self.ProxCount[0]!=-1:
            return True,self.ProxCount
        else:
            return False,self.ProxCount

    def setAnimal(self, animal):
        self.animal=animal

    def setTerrain(self,terrain):
        self.terrain=terrain

    def IsAnimalPossible(self,animal):
        if(self.terrain==-1 or animal==-1):
            return True
        elif(self.terrain==0 and animal=="T"):
            return False
        elif(self.terrain==1 and animal=="S"):
            return False
        return True

    def VariableToCell(self,nb):
        nb=nb-1
        cellnb=nb//3
        y=cellnb//self.dim[0]
        x=cellnb%self.dim[0]
        if(nb%3==0):
            return "T",(x,y)
        elif(nb%3==1):
            return "S",(x,y)
        elif(nb%3==2):
            return "C",(x,y)
            

def clausetofile(filename,nbvar,clauses,checks):
    content="c  filedemineur.cnf\nc\n"
    
    content+= "p cnf "+str(nbvar)+" "+str(len(clauses)+len(checks))+"\n"
    for clause in clauses:
        content+= clause
    for check in checks:
        content+= check
    with open(filename, "w", newline="") as cnf:
        cnf.write(content)


def exec_gophersat(filename):

    cmd = "gophersat-1.1.6.exe"
    
    result = subprocess.run(
        [cmd, filename], stdout=PIPE, check=True, encoding="utf8"
    )
    string = str(result.stdout)
    lines = string.splitlines()
    #print("go4sat")
    #print(lines)
    if lines[1] != "s SATISFIABLE":
        global success
        success+=1
        return True

    #model = lines[2][2:].split(" ")
    global fail
    fail+=1
    return False

if __name__ == "__main__":
    server = "http://localhost:8000"
    group = "Groupe 37"
    members = "Theo et Anisa"
    croco = CrocomineClient(server, group, members)
    while True:
        state=game()
        print("---end---stat: "+str(success)+"/"+str(fail))



