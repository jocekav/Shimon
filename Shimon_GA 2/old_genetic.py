from queue import Empty
import random
from collections import Counter
from statistics import mean, median, stdev
from ast import literal_eval
import operator
import math

def percentage_pitch(pattern, pitch_options):
    # create dictionary for avail pitches
    pitch_map = dict.fromkeys(pitch_options, 0)
    # count occurance of each note in pattern
    pitch_count = Counter(elem[1] for elem in pattern)
    # combine dictionaries
    pitch_map = {**pitch_map, **pitch_count}
    pitch_map = {key: pitch_map[key] / len(pattern) for key in pitch_map.keys()}
    return pitch_map

def percentage_rhythm(pattern, rhythm_options):
    # create dictionary for avail rhythm
    rhythm_map = dict.fromkeys(rhythm_options, 0)
    # count occurance of each note in pattern
    rhythm_count = Counter(elem[0] for elem in pattern)
    # combine dictionaries
    rhythm_map = {**rhythm_map, **rhythm_count}
    rhythm_map = {key: rhythm_map[key] / len(pattern) for key in rhythm_map.keys()}
    return rhythm_map

def get_range(pattern):
    min_pitch = min(pattern)[1]
    max_pitch = max(pattern)[1]
    range = max_pitch - min_pitch
    return (range, min_pitch, max_pitch)

def get_pitch_mct(pattern):
    mean_pitch = mean(elem[1] for elem in pattern)
    median_pitch = median(elem[1] for elem in pattern)
    stdev_pitch = stdev(elem[1] for elem in pattern)
    return (mean_pitch, median_pitch, stdev_pitch)

class world:
    def __init__(self, target_pattern, population_file, pitch_options, rhythm_options):
        self.pitch_options = pitch_options
        self.rhythm_options = rhythm_options
        self.target_obj = target(target_pattern, pitch_options, rhythm_options)
        self.population = self.build_population(population_file)
        self.population.sort(key = lambda x: x.fitness)
        self.population_size = len(self.population)

    def build_population(self, input_file):
        population = []
        file = open(input_file)
        line = file.readline()
        while line is not Empty:
        # for i in range(50):
            pattern = literal_eval(line)
            population.append(gene(pattern, self.target_obj, self.pitch_options, self.rhythm_options))
            line = file.readline()
            if not line:
                break
        file.close()
        return population

    def print_population(self):
        for gene in self.population:
            print(gene.get_fitness(), gene.get_pattern())

    def run(self, num_generations=10, survival_rate=.5, mutation_rate=.2):
        for i in range(num_generations):
            # check evolution rate
            print("Generation " + str(i-1))
            self.print_population()
            self.population.sort(key = lambda x: x.fitness)
            # cut the population by the survival rate
            ind = int(self.population_size * survival_rate)
            self.population = self.population[:ind]

            # repopulate with the fittest parents
            children = []
            for parents in range(ind):
                new_gene = self.breed()
                children.append(new_gene)
            self.population.extend(children)

            # # mutate a random amount of genes
            self.mutate(mutation_rate)
        # check evolution rate
        self.population.sort(key = lambda x: x.fitness)
        print("Generation " + str(num_generations))
        self.print_population()


    def breed(self):
        parent1 = (random.choice(self.population)).get_pattern()
        parent2 = (random.choice(self.population)).get_pattern()

        new_pattern = []
        total = 0
        front_beats = 0
        back_beats = 0
        front_ind = 0
        back_ind = -1
        length = 0
        while front_beats <= int(num_beats / 2):
            try:
                front_beats += parent1[front_ind][0]
            except:
                print(parent1)
                print(front_ind)
                print(front_beats)
            if front_beats > int(num_beats / 2):
                break
            new_pattern.append(parent1[front_ind])
            length += 1
            front_ind += 1
        while back_beats <= int(num_beats / 2):
            back_beats += parent2[back_ind][0]
            if back_beats > int(num_beats / 2):
                break
            new_pattern.insert((length + 1 + back_ind), parent2[back_ind])
            length += 1
            back_ind -= 1
        for i in range(0, len(new_pattern)):
            total = total + new_pattern[i][0]
        if total < num_beats:
            last_beat = num_beats - total
            new_pattern.append((last_beat, parent1[0][1]))
        if total > num_beats:
            left_over = 16 - 13.5
            back_ind = -1
            rhythm_options = [0.25, 0.5, 1, 1.5, 2, 3, 4]
            add = 0
            while left_over != 0:
                rhythm = rhythm_options[back_ind]
                if left_over >= rhythm:
                    left_over = left_over - rhythm
                    new_pattern.append((rhythm, new_pattern[-1][1]))
                back_ind -= 1
        new_gene = gene(new_pattern, self.target_obj, self.pitch_options, self.rhythm_options)

        return new_gene

    def mutate(self, mutation_rate):
        for gene in self.population:
            if random.randint(0,99) < (mutation_rate * 100):
                gene_pattern = gene.get_pattern()
                orig_gene_pattern = gene_pattern
                if random.random() % 2 and len(gene_pattern) > 2:
                    flip_ind = random.randint(0, (len(gene_pattern)-1))
                    change_note_dur = gene_pattern[flip_ind][0]
                    del gene_pattern[flip_ind]
                    inserted = False
                    ind = 0
                    while not inserted and ind < len(gene_pattern):
                        try_rhy = gene_pattern[ind][0] + change_note_dur
                        if try_rhy in rhythm_options:
                            pitch = gene_pattern[ind][1]
                            gene_pattern[ind] = (try_rhy, pitch)
                            inserted = True
                        ind += 1
                    if not inserted:
                        gene_pattern = orig_gene_pattern
                    gene.reinit(gene_pattern)
                elif len(gene_pattern) < 64:
                    inserted = False
                    ind = random.randint(0, (len(gene_pattern)-1))
                    while not inserted:
                        try_rhy = gene_pattern[ind][0] / 2
                        if try_rhy in rhythm_options:
                            pitch = gene_pattern[ind][1]
                            gene_pattern[ind] = (try_rhy, pitch)
                            gene_pattern.append((try_rhy, pitch))
                            inserted = True
                        ind = (ind + 1) % len(gene_pattern)
                    if not inserted:
                        gene_pattern = orig_gene_pattern
                    gene.reinit(gene_pattern)


class target:
    def __init__(self, pattern, pitch_options, rhythm_options):
        self.pattern = pattern
        self.pitch_percentage = percentage_pitch(self.pattern, pitch_options)
        self.rhythm_percentage = percentage_rhythm(self.pattern, rhythm_options)
        self.pitch_mct = get_pitch_mct(pattern)
        self.pitch_range = get_range(pattern)

class gene:
    def __init__(self, pattern, target, pitch_options, rhythm_options, fitness=0):
        self.pattern = pattern
        self.target = target
        self.pitch_options = pitch_options
        self.rhythm_options = rhythm_options
        self.pitch_percentage = percentage_pitch(pattern, pitch_options)
        self.rhythm_percentage = percentage_rhythm(pattern, rhythm_options)
        self.pitch_mct = get_pitch_mct(pattern)
        self.pitch_range = get_range(pattern)
        self.fitness = self.get_fitness()

    def reinit(self, pattern):
        self.pattern = pattern
        self.pitch_percentage = percentage_pitch(self.pattern, self.pitch_options)
        self.rhythm_percentage = percentage_rhythm(self.pattern, self.rhythm_options)
        self.pitch_mct = get_pitch_mct(self.pattern)
        self.pitch_range = get_range(self.pattern)
        self.fitness = self.get_fitness()

    def get_pattern(self):
        return self.pattern

    def get_fitness(self):
        # computes Euclidian distance of dimensionality according to target vector
        # compares difference in note density
        # find percentage of each note in the pattern
        # find percentage of each rhythm in the pattern
        # find range - difference between min/max
        # find avg note
        # find std 

        # difference in note density based on vector lengths
        pattern = self.pattern
        target = self.target
        pattern_len = len(pattern)
        target_len = len(target.pattern)

        euclid_sum = (target_len - pattern_len) ** 2

        # differences in percentage of each note in the pattern
        differences = list({k: target.pitch_percentage[k] - self.pitch_percentage[k] for k in target.pitch_percentage}.values())
        euclid_sum += sum([i ** 2 for i in differences])

        # differences in percentage of each rhythm in the pattern
        differences = list({k: target.rhythm_percentage[k] - self.rhythm_percentage[k] for k in target.rhythm_percentage}.values())
        euclid_sum += sum([i ** 2 for i in differences])

        # differences in central tendency
        differences = list(map(operator.sub, target.pitch_mct, self.pitch_mct))
        euclid_sum += sum([i ** 2 for i in differences])

        # differences in pitch range
        differences = list(map(operator.sub, target.pitch_range, self.pitch_range))
        euclid_sum += sum([i ** 2 for i in differences])

        return math.sqrt(euclid_sum)
        # could make a line and do a regression for pitch contour - need to preserve the "final note"
        # could do rhythm over time
        # could do the probabilities that a note is followed by another note

        # difference in notes and rhythms used (in order)
        # only uses matching notes of the shorter pattern
        # TODO: figure out a better way to solve this metric
        # if target_len <= pattern_len:
        #     for i in range(target_len):
        #         # get pitch difference
        #         euclid_sum += ((target[i][2] - pattern[i][2]) ** 2)
        #         # get rhythm difference
        #         euclid_sum += ((target[i][1] - pattern[i][1]) ** 2)
        # else:
        #     for i in range(pattern_len):
        #         # get pitch difference
        #         euclid_sum += ((target[i][2] - pattern[i][2]) ** 2)
        #         # get rhythm difference
        #         euclid_sum += ((target[i][1] - pattern[i][1]) ** 2)

target_patt = [(4, 60), (4, 60)]

pitch_options = [-1, 60, 62, 64, 65, 67, 69, 71, 72]
num_beats = 8
rhythm_options = [0.25, 0.5, 1, 1.5, 2, 3, 4]

world = world(target_patt, "melodies.txt", pitch_options, rhythm_options)
world.print_population()
world.run()