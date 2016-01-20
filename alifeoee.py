#!/usr/bin/env python

import random
import numpy
import sys
import copy

class Organism:
  '''A class to contain an organism'''
  def __init__(self, cellID, genome=[], parent=False, empty=False):
    self.age = 0
    self.generation = 0
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
        self.generation = parent.generation + 1
        parent.generation = self.generation
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
    self.cur_persist = []
    self.prev_persist = []
    

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
    cur_pop = history[-1]
    cur_coal = history[-2]
    prev_pop = history[-2]
    if len(history)>2:
      prev_coal = history[-3]
    else:
      prev_coal = history[-2]

    for org_1 in cur_pop:
      for org_2 in cur_coal:
        if numpy.array_equal(org_1.genome, org_2.genome):
          self.cur_persist.append(org_1)
          break
    for org_3 in prev_pop:
      for org_4 in prev_coal:
        if numpy.array_equal(org_3.genome, org_4.genome):
          self.prev_persist.append(org_3)
          break

  

  def changeMetric(self, history):
    '''Measuring the change potential in the population.'''
    self.getPersistentOrgs(history)

    new_count = 0
    for org_1 in self.cur_persist:
      match = False
      for org_2 in self.prev_persist:
        if numpy.array_equal(org_1.genome, org_2.genome):
          match = True
          break
      if not match:
        new_count += 1
    return new_count

  def noveltyMetric(self, history, gen_persist = True):
    '''Measuring the novelty potential in the population.'''
    #There should probably be a coalescence calculation in here, but I have no idea how to do it.
    cur_pop = history[-1]
    new_count = 0
    for org_1 in cur_pop:
      match = False
      for pop in range(len(history)-2, -1, -1):
        prev_pop = history[pop]
        for org_2 in prev_pop:
          if numpy.array_equal(org_1.genome, org_2.genome):
            match=True
            break
        if match:
          break
      if not match:
        new_count +=1
    return new_count

  def complexityMetric(self):
    '''Measuring the complexity potential in the population.'''
    #Normally we would count the length of skeletons, but that doesn't quite work with this system.
    #Instead, I am going to count the number of 1's for now because they are what contributes to fitness.
    #We can switch to true knockouts once we make a more complicated fitness structure.
    most_complex = 0
    for org in self.orgs:
      total = numpy.sum(org.genome)
      if total > most_complex:
        most_complex = total
    return total

  def ecologyMetric(self):
    '''Measuring the ecology potential in the population.'''
    distinct_orgs = {}
    for org in self.orgs:
      string_genome = numpy.array_str(org.genome)
      if string_genome not in distinct_orgs:
        distinct_orgs[string_genome] = 1
      else:
        distinct_orgs[string_genome] += 1
    return len(distinct_orgs)

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
    

  def noveltyTest(self):
    '''Verifies that Novelty Metrics are working. 
    Should print n: 1, n: 0, , n: 0'''
    sample = [Organism(0,genome=numpy.array([0,0]))]
    sample_2 = [Organism(0,genome=numpy.array([1,0]))]
    sample_3 = [Organism(0,genome=numpy.array([0,0]))]
    sample_4 = [Organism(0,genome=numpy.array([1,0]))]

    history = [sample, sample_2, sample_3, sample_4]

    test_pop = Population(0)
    for j in range(2,5):
      print "Novelty: ", test_pop.noveltyMetric(history[:j])



if len(sys.argv) == 1 or sys.argv[1] == "--help":
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
      change = population_orgs.changeMetric(history)
      novelty = population_orgs.noveltyMetric(history)
      complexity = population_orgs.complexityMetric()
      ecology = population_orgs.ecologyMetric()
      data_file = open("test_"+str(seed)+".dat", 'a')
      data_file.write('{} {} {} {} {}\n'.format(g, change, novelty, complexity, ecology))
      data_file.close()





