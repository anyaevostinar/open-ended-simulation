#!/usr/bin/env python

import random
import numpy
import sys
import copy

class Organism:
  '''A class to contain an organism'''
  def __init__(self, cellID, genome=[], parent=False, empty=False):
    self.age = 0
    self.empty = empty
    self.ID = cellID
    self.fitness = 0
    self.genome = genome
    if not self.empty:
      if len(genome):
        self.genome = genome
      elif parent:
        newGenome =[]
        for i in range(len(parent.genome)):
          newGenome.append(parent.genome[i])
        self.genome = newGenome
        self.mutate()
        parent.mutate()
        parent.fitness = 0
        parent.age = 0
      else:
        print "fail"

  def __repr__(self):
    info = "empty: " + str(self.empty) + ", ID: " + str(self.ID) + ", genome: " + str(self.genome) + ", fitness: " + str(self.fitness) + "\n"
    return info

  def update(self):
    '''Updates the organism's fitness based on its age'''
    if not self.empty:
      self.age += 1
      cur_gene = self.genome[self.age%len(self.genome)]
      self.fitness += cur_gene
      return True
    else:
      return False
      

  def mutate(self):
    newGenome = self.genome
    for i in range(len(newGenome)):
      if random.random() < .002:
        newGenome[i] = random.randint(0,1)
    self.genome = newGenome

    
      
  def findNeighbors(self):
    cellID = self.ID
    radius = 1
    world_x = pop_x
    world_y = pop_y
    cell_x = cellID % world_x
    cell_y = (cellID - cell_x)/world_x
    neighbor_ids = []
    for i in range(cell_x-radius, cell_x+radius+1):
      for j in range(cell_y-radius, cell_y+radius+1):
        if i<0:
          x = world_x + i
        elif i>=world_x:
          x = i-world_x
        else:
          x = i

        if j<0:
          y = world_y + j
        elif j>=world_y:
          y = j-world_y
        else:
          y = j

        neighbor_ids.append(y*world_x+x)

    return neighbor_ids

        
class Population:
  '''A class to contain the population and do stuff'''
  def __init__(self, popsize):
    self.currentUpdate = 0
    self.orgs = []
    self.pop_size = popsize
    

    for i in range(popsize):
      self.orgs.append(self.makeOrg())

  def makeOrg(self):
    '''A function to make a new organism randomly'''
    randomBitArray = numpy.random.randint(2, size=(100,))
    newOrg = Organism(len(self.orgs), genome=list(randomBitArray))
    return newOrg

  def reproduceOrg(self, org):
    '''A helper function to reproduce a host organism.'''
    ## Time to reproduce
    ## Returns list of neighbor indices
    dead_neighbor = False
    neighbors = org.findNeighbors()
    for ID in neighbors:
      if self.orgs[ID].empty:
        dead_neighbor = ID
        break
    if dead_neighbor:
      position = dead_neighbor
    else:
      position = random.choice(neighbors)
    newOrg = Organism(position, parent = org)

    self.orgs[position] = newOrg

  def update(self):
    '''A function that runs a single update'''
    self.currentUpdate+=1
    for org in self.orgs:
      if not org.empty:
        result = org.update()
        if org.fitness >= len(org.genome):
          self.reproduceOrg(org)


  def findBest(self, orgs_to_eval=False):
    '''Finds the best of the population or a provided subset'''
    if not orgs_to_eval:
      orgs_to_eval = self.orgs
    highest_fitness = 0
    fittest_org = False
    for org in orgs_to_eval:
      if org.fitness > highest_fitness:
        highest_fitness = org.fitness
        fittest_org = org
  
    if not fittest_org:
      print "Error! No Org selected!"
    return fittest_org

  def changeMetric(self, coal, history):
    '''Measuring the change potential in the population.'''
    cur_pop = history[-1]
    prev_pop = history[-2]
    new_count = 0
    for org_1 in cur_pop:
      match = False
      for org_2 in prev_pop:
        if org_1.genome == org_2.genome:
          match = True
          break
      if not match:
        new_count += 1
    return new_count


if len(sys.argv) == 1 or sys.argv[1] == "--help":
  print "usage: pop_x pop_y seed"
else:

  seed = int(sys.argv[3])
  random.seed(seed)
  numpy.random.seed(seed)

  coalesce = 100
  num_updates = 20000
  pop_x = int(sys.argv[1])
  pop_y = int(sys.argv[2])
  pop_size = pop_x*pop_y

  data_file = open("test_"+str(seed)+".dat", 'w')
  data_file.write("Update Change_Metric \n")

  history = []
  population_orgs = Population(pop_size)
  history.append(copy.deepcopy(population_orgs.orgs))
  for i in range(num_updates):
    population_orgs.update()
    if i != 0 and (i%coalesce == 0):
      history.append(copy.deepcopy(population_orgs.orgs))
      change = population_orgs.changeMetric(coalesce, history)
      data_file.write('{} {}\n'.format(i, change))


  data_file.close()
