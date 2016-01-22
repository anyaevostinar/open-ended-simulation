#!/usr/bin/env python

import random
import numpy
import sys
import copy

class Organism:
  '''A class to contain an organism'''
  def __init__(self, cellID, genome=[], parent=False, empty=False, lineage = -1):
    self.age = 0
    self.generation = 0
    self.empty = empty
    self.ID = cellID
    self.lineage = lineage
    self.prev_lineage = lineage
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
        self.lineage = parent.lineage
        self.prev_lineage = parent.prev_lineage
        self.generation = parent.generation + 1
        parent.generation = self.generation
        parent.mutate()
        parent.fitness = 0
        parent.age = 0
      else:
        print "fail"

  def __repr__(self):
    info = "lineage " + str(self.lineage) + ", ID: " + str(self.ID) + ", genome: " + str(self.genome) + ", fitness: " + str(self.fitness) + "\n"
    return info

  def __eq__(self, other):
    if numpy.array_equal(self.genome, other.genome) and (self.lineage == other.lineage):
      return True
    else:
      return False

  def __hash__(self):
    full = numpy.array_str(self.genome) + str(self.lineage)
    return hash(full)


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
    self.cur_persist = set()
    self.prev_persist = set()
    self.novel_orgs = set()
    

    for i in range(popsize):
      self.orgs.append(self.makeOrg(i))

  def makeOrg(self, lineage):
    '''A function to make a new organism randomly'''
    randomBitArray = numpy.random.randint(2, size=(100,))
    newOrg = Organism(len(self.orgs), genome=randomBitArray, lineage = lineage)
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
    persist_lin_cur = set()
  

    for org in cur_pop:
      persist_lin_cur.add(org.lineage)


    for org in cur_coal:
      if org.lineage in persist_lin_cur:
        self.cur_persist.add(org)


    #Now we have to reset the organism lineages to prepare for next cycle
    for i in range(len(self.orgs)):
      self.orgs[i].lineage = i
      history[-1][i].lineage = i


  def getNovelOrgs(self):
    #Update the list of all genomes we've seen (some duplicates if two lineages have same genome)
    #make this store actual genomes instead of organisms
    if self.novel_orgs:
      self.novel_orgs.update(self.prev_persist)
    else:
      self.novel_orgs = self.prev_persist
      

  def changeMetric(self, history):
    '''Measuring the change potential in the population.'''
    self.getPersistentOrgs(history)
    assert self.prev_persist, "prev_persist must exist"    
    self.getNovelOrgs()

    new_orgs = set()

    #we have to do nested for loops to do direct genome comparisons and not take organism lineage into account
    for org_1 in self.cur_persist:
      match = False
      for org_2 in self.prev_persist:
        if numpy.array_equal(org_1.genome, org_2.genome):
          match = True
          break
      if not match:
        new_orgs.add(org_1)

    return len(new_orgs)

  def noveltyMetric(self, history):
    '''Measuring the novelty potential in the population.'''
    if not self.cur_persist:
      self.getPersistentOrgs(history)

    novel = set()
    for org_1 in self.cur_persist:
      match = False
      for org_2 in self.novel_orgs:
        if numpy.array_equal(org_1.genome, org_2.genome):
          match = True
          break
      if not match:
        novel.add(org_1)

    #might be able to add novel to self.novel_orgs now?
    return len(novel)

  def complexityMetric(self):
    '''Measuring the complexity potential in the population.'''
    #Normally we would count the length of skeletons, but that doesn't quite work with this system.
    #Instead, I am going to count the number of 1's for now because they are what contributes to fitness.
    #We can switch to true knockouts once we make a more complicated fitness structure.
    most_complex = 0

    for org in set(self.orgs):
      total = numpy.sum(org.genome)
      if total > most_complex:
        most_complex = total
    return most_complex

  def ecologyMetric(self):
    '''Measuring the ecology potential in the population.'''

    unique_gen = set()
    for org in self.orgs:
      if numpy.array_str(org.genome) not in unique_gen:
        unique_gen.add(numpy.array_str(org.genome))

    return len(unique_gen)

  def avgGen(self):
    '''Records the average generation of the population.'''
    gen_total = 0.0
    count = 0
    for org in self.orgs:
      gen_total += org.generation
      count += 1

    if count > 0:
      return gen_total/count
    else:
      return 0

    return len(set(self.orgs))

    

def noveltyTest():
  '''Verifies that Novelty Metrics are working. 
    Should print n: 0, n: 1, , n: 0'''
  sample = [Organism(0,genome=numpy.array([0,0]), lineage=0)]
  sample_2 = [Organism(0,genome=numpy.array([1,0]), lineage =0)]
  sample_3 = [Organism(0,genome=numpy.array([1,0]),lineage = 0)]
  sample_4 = [Organism(0,genome=numpy.array([1,0]), lineage=0)]
  
  history = [sample, sample_2, sample_3, sample_4]

  test_pop = Population(0)
  for j in range(3,5):
    test_pop.prev_persist = test_pop.cur_persist
    test_pop.cur_persist = set()
    print "Novelty: ", test_pop.noveltyMetric(history[:j])
    print "Change: ", test_pop.changeMetric(history[:j])


def multiLineageTest():
  '''Test multiple lineages.'''
  sample_1 = [Organism(0, genome=numpy.array([0,0]), lineage=0), Organism(0, genome = numpy.array([1,1]), lineage=1)]
  sample_2 = [Organism(0, genome=numpy.array([0,0]), lineage=0), Organism(0, genome = numpy.array([1,1]), lineage=1)]
  sample_3 = [Organism(0, genome=numpy.array([0,1]), lineage=1), Organism(0, genome = numpy.array([1,1]), lineage=1)]
  sample_4 = [Organism(0, genome=numpy.array([0,1]), lineage=1), Organism(0, genome = numpy.array([1,1]), lineage=1)]

if len(sys.argv) < 4 or sys.argv[1] == "--help":
  print "usage: pop_x pop_y seed"
else:

  seed = int(sys.argv[3])
  random.seed(seed)
  numpy.random.seed(seed)

  coalesce = 1000
  num_gen = 100000
  pop_x = int(sys.argv[1])
  pop_y = int(sys.argv[2])
  pop_size = pop_x*pop_y

  data_file = open("test_"+str(seed)+".dat", 'w')
  data_file.write("Avg_Gen Change_Metric Novelty_Metric Complexity_Metric Ecology_Metric\n")
  data_file.close()
  history = []
  population_orgs = Population(pop_size)
  history.append(copy.deepcopy(population_orgs.orgs))
  history_gen = 0
  g = 0
  while g < num_gen:
    population_orgs.update()
    g = population_orgs.avgGen()
    if ((history_gen + coalesce) <= g):
      history.append(copy.deepcopy(population_orgs.orgs))

      history_gen = g

      population_orgs.prev_persist = population_orgs.cur_persist
      population_orgs.cur_persist = set()

      if len(history)>2:
        #Metrics don't make sense until we have three time slices
        change = population_orgs.changeMetric(history)
        novelty = population_orgs.noveltyMetric(history)
        complexity = population_orgs.complexityMetric()
        ecology = population_orgs.ecologyMetric()
        data_file = open("test_"+str(seed)+".dat", 'a')
        data_file.write('{} {} {} {} {}\n'.format(g, change, novelty, complexity, ecology))
        data_file.close()

      elif len(history)==2:
        population_orgs.getPersistentOrgs(history)






