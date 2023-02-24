import random
from collections import Iterable

import numpy as np
from deap import creator, base, tools
from deap.algorithms import eaMuPlusLambda


NUMBER_OF_GENERATIONS = 100
MU, LAMBDA = 10, 10
CROSSOVER_PROBABILITY, MUTATION_PROBABILITY = .9, .1


def to_pairs(it: Iterable) -> list[tuple]:
    it = iter(it)
    return list(zip(it, it))


def find_maximum_assignment(matrix: np.ndarray) -> list[tuple[int, int]]:
    individual_size = np.shape(matrix)[0]

    creator.create('FitnessMin', base.Fitness, weights=(1.0,))
    creator.create('Individual', list, fitness=creator.FitnessMin)

    toolbox = base.Toolbox()
    toolbox.register("indices", random.sample, range(individual_size), individual_size)
    toolbox.register('individual', tools.initIterate, creator.Individual, toolbox.indices)
    toolbox.register("population", tools.initRepeat, list, toolbox.individual)

    def evaluate(ind: list[int]) -> tuple[int]:
        ind_iter = iter(ind)
        pairs = zip(ind_iter, ind_iter)
        return int(sum(matrix[pair] for pair in pairs)),

    toolbox.register("evaluate", evaluate)
    toolbox.register("mate", tools.cxPartialyMatched)
    toolbox.register("mutate", tools.mutShuffleIndexes, indpb=0.05)
    toolbox.register("select", tools.selTournament, tournsize=3)
    population = toolbox.population(n=20)

    hall_of_fame = tools.HallOfFame(1)
    eaMuPlusLambda(population, toolbox, MU, LAMBDA, CROSSOVER_PROBABILITY, MUTATION_PROBABILITY, NUMBER_OF_GENERATIONS,
                   halloffame=hall_of_fame, verbose=True)
    winner = hall_of_fame[0]

    return to_pairs(winner)
