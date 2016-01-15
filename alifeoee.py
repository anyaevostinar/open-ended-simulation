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

  def __eq__(self, other):
    return numpy.array_equal(self.genome, other.genome)

  def __hash__(self):
    return hash(numpy.array_str(self.genome))

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
    newGenome = numpy.copy(self.genome)
    for i in range(len(newGenome)):
      if random.random() < .007:
        if newGenome[i] == 0:
          newGenome[i] = 1
        else:
          newGenome[i] = 0
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
    self.cur_persist = None
    self.prev_persist = None
    self.novel_orgs = None
    

    for i in range(popsize):
      self.orgs.append(self.makeOrg())

  def makeOrg(self):
    '''A function to make a new organism randomly'''
    randomBitArray = numpy.random.randint(2, size=(100,))
    newOrg = Organism(len(self.orgs), genome=randomBitArray)
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

  def getPersistentOrgs(self, history):
    '''A helper function that figures out the genotypes that have persisted since coalescence time.'''
    #We are assuming that the history orgs are saved every coalescence time because it is much easier.
    cur_pop = set(history[-1])
    cur_coal = set(history[-2])

    self.cur_persist = cur_pop.intersection(cur_coal)


    if not self.prev_persist:
      prev_pop = set(history[-2])
      if len(history)>2:
        prev_coal = set(history[-3])
      else:
        prev_coal = set(history[-2])

      self.prev_persist = prev_pop.intersection(prev_coal)

    if self.novel_orgs:
      self.novel_orgs = self.novel_orgs | self.prev_persist
    else:
      self.novel_orgs = self.prev_persist
  

  def changeMetric(self, history):
    '''Measuring the change potential in the population.'''
    self.getPersistentOrgs(history)
    
    new_orgs = self.cur_persist - self.prev_persist

    return len(new_orgs)

  def noveltyMetric(self, history):
    '''Measuring the novelty potential in the population.'''
    #There should probably be a coalescence calculation in here, but I have no idea how to do it.
    #Make a running set that saves all persistent organisms ever to compare against
    #Have update set cur and prev persist set to none and then check that

    ##THIS IS BROKEN AND NOT PASSING ITS TEST BUT I DONT KNOW WHY

    if not self.cur_persist:
      self.getPersistentOrgs(history)



    return len(self.cur_persist - self.novel_orgs)

  def complexityMetric(self):
    '''Measuring the complexity potential in the population.'''
    #Normally we would count the length of skeletons, but that doesn't quite work with this system.
    #Instead, I am going to count the number of 1's for now because they are what contributes to fitness.
    #We can switch to true knockouts once we make a more complicated fitness structure.
    most_complex = 0

    for org in set(self.cur_persist):
      total = numpy.sum(org.genome)
      if total > most_complex:
        most_complex = total
    return most_complex

  def ecologyMetric(self):
    '''Measuring the ecology potential in the population.'''
    #persistent orgs?
    return len(set(self.orgs))
    

def noveltyTest():
  '''Verifies that Novelty Metrics are working. 
    Should print n: 0, n: 1, , n: 0'''
  sample = [Organism(0,genome=numpy.array([0,0]))]
  sample_2 = [Organism(0,genome=numpy.array([1,0]))]
  sample_3 = [Organism(0,genome=numpy.array([1,0]))]
  sample_4 = [Organism(0,genome=numpy.array([1,0]))]
  
  history = [sample, sample_2, sample_3, sample_4]

  test_pop = Population(0)
  for j in range(2,5):
    print "Novelty: ", test_pop.noveltyMetric(history[:j])



if len(sys.argv) < 4 or sys.argv[1] == "--help":
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
  data_file.write("Update Change_Metric Novelty_Metric Complexity_Metric Ecology_Metric\n")

'''  history = []
  population_orgs = Population(pop_size)
  history.append(copy.deepcopy(population_orgs.orgs))
  for u in range(num_updates):
    population_orgs.update()
    if u != 0 and (u%coalesce == 0):
      history.append(copy.deepcopy(population_orgs.orgs))
      population_orgs.prev_persist = population_orgs.cur_persist
      population_orgs.cur_persist = None
      change = population_orgs.changeMetric(history)
      novelty = population_orgs.noveltyMetric(history)
      complexity = population_orgs.complexityMetric()
      ecology = population_orgs.ecologyMetric()
      data_file.write('{} {} {} {} {}\n'.format(u, change, novelty, complexity, ecology))


  data_file.close()
'''

noveltyTest()


