from distutils.command import clean
from queue import Empty
import random
from collections import Counter
from statistics import mean, median, stdev
from ast import literal_eval
import operator
import math
import pythonosc
from pythonosc import udp_client
from pythonosc import dispatcher
from pythonosc import osc_server
from typing import List, Any
import time
import datetime
import keyboard

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

def calculate_intervals(pattern):
    first_note = pattern[0][1]
    intervals = []
    for i in range(1, len(pattern)):
        second_note = pattern[i][1]
        intervals.append(second_note - first_note)
        first_note = second_note
    return intervals

# attempt to define contour from front and back arcs (disregards middle if one melody is much longer)
def check_order_front_back(patt_1, patt_2):
    front = 0
    back_1 = len(patt_1) - 1
    back_2 = len(patt_2) - 1
    matches_pitch = 0
    matches_rhythm = 0
    while(front < back_1 or front < back_2):
        if (patt_1[front][0] == patt_2[front][0]):
            matches_rhythm += 1
        if (patt_1[front][1] == patt_2[front][1]):
            matches_pitch += 1
        if (patt_1[back_1][0] == patt_2[back_2][0]):
            matches_rhythm += 1
        if (patt_1[back_1][1] == patt_2[back_2][1]):
            matches_pitch += 1
        front = front + 1
        back_1 = back_1 + 1
        back_2 = back_2 + 1
    shorter_len = len(patt_1)
    if len(patt_2) < shorter_len:
        shorter_len = len(patt_2)
    percent_pitch = matches_pitch / shorter_len
    percent_rhythm = matches_rhythm / shorter_len
    return (percent_rhythm, percent_pitch)
    
def step_to_leap_ratio(intervals):
    # step defined as minor third and below (everything else is a leap)
    # returns step / leap
    steps = 0
    leaps = 0
    for i in range(len(intervals)):
        if abs(intervals[i]) > 3:
            leaps += 1
        else:
            step += 1
    if leaps == 0:
        return 1
    else:
        return steps / leaps

def get_abstracted_contour(pattern):
    patt_len = len(pattern)
    min_pitch = min(pattern)[1]
    max_pitch = max(pattern)[1]
    first_pitch = pattern[0][1]
    last_pitch = pattern[patt_len - 1][1]
    mid_point = int(patt_len / 2)
    mid_pitch = pattern[mid_point][1]

    if (min_pitch == max_pitch):
        return 'flat'
    elif max_pitch == first_pitch:
        if min_pitch == last_pitch or last_pitch < mid_pitch:
            return 'descend'
        elif max_pitch == last_pitch or last_pitch >= mid_pitch:
            return 'v'
    elif min_pitch == first_pitch:
        if max_pitch == last_pitch or last_pitch >= mid_pitch:
            return 'ascend'
        elif min_pitch == last_pitch or last_pitch < mid_pitch:
            return 'arch'

    return 'undef'

def expand_pattern(pattern, rhythm_options):
    expanded_pattern = []
    min_unit = min(rhythm_options)
    for i in range(len(pattern)):
        rhythm, pitch = pattern[i]
        num_units = rhythm / min_unit
        expanded_note = [pitch] * num_units
        expanded_pattern.extend(expanded_note)
    return expanded_pattern

def transpose_to_C(pattern):
    diff = pattern[0][1] - 60
    transp_patt = []
    for i in range(len(pattern)):
        transp_patt.append(pattern[i][1] + diff)
    return transp_patt


class world:
    def __init__(self, target_pattern, population_file, pitch_options, rhythm_options):
        self.pitch_options = pitch_options
        self.rhythm_options = rhythm_options
        self.target_obj = target(target_pattern, pitch_options, rhythm_options)
        self.population = self.build_population(population_file)
        self.population.sort(key = lambda x: x.fitness)
        self.population_size = len(self.population)
        IP = "143.215.114.123"
        PORT_TO_MAX = 7980
        self.client = udp_client.SimpleUDPClient(IP, PORT_TO_MAX)
    
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
        # for gene in self.population:
        #     print(gene.get_fitness(), gene.get_pattern())
        for i in range(5):
            print(self.population[i].get_fitness(), self.population[i].get_pattern())

    def run(self, num_generations=10, survival_rate=.3, mutation_rate=.3):
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
            # self.population.sort(key = lambda x: x.fitness)
            # self.print_population()
            self.play_melodies()
            input("press enter to continue")
         

    def breed(self):
        parent1 = (random.choice(self.population)).get_pattern()
        parent2 = (random.choice(self.population)).get_pattern()

        # weave together pattern from random parents by alternating between patterns
        total = 0
        ind_1 = 0
        ind_2 = 0
        switch = False
        new_pattern = []
        while total <= num_beats and (ind_1 < len(parent1) or ind_2 < len(parent2)):
            if switch:
                if ind_1 < len(parent1) and parent1[ind_1][0] + total <= num_beats:
                    new_pattern.append(parent1[ind_1])
                    total += parent1[ind_1][0]
                    # ind_1 = ind_1 + 1
                elif ind_2 < len(parent2) and parent2[ind_2][0] + total <= num_beats:
                    new_pattern.append(parent2[ind_2])
                    total += parent2[ind_2][0]
                    # ind_2 = ind_2 + 1
            else:
                if ind_2 < len(parent2) and parent2[ind_2][0] + total <= num_beats:
                    new_pattern.append(parent2[ind_2])
                    total = total + parent2[ind_2][0]
                    # ind_2 = ind_2 + 1
                elif ind_1 < len(parent1) and parent1[ind_1][0] + total <= num_beats:
                    new_pattern.append(parent1[ind_1])
                    total = total + parent1[ind_1][0]
                    # ind_1 = ind_1 + 1
            ind_1 = ind_1 + 1
            ind_2 = ind_2 + 1
            switch = not switch
        total = 0
        for i in range(0, len(new_pattern)):
            total = total + new_pattern[i][0]
        if total < num_beats:
            last_beat = num_beats - total
            new_pattern.append((last_beat, parent1[0][1]))
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
                elif len(gene_pattern) < num_beats / 0.25:
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

    def play_melodies(self):
        input("press enter to play target")
        pattern = self.target_obj.pattern
        for i in range(len(pattern)):
            tempo = 200
            duration_mult = 60000 / tempo
            dur = pattern[i][0] * duration_mult
            self.client.send_message("/max", [pattern[i][1], dur])
            print(pattern[i])
            time.sleep(dur / 1000)
        for p in range(1):
            input("press enter to play next match")
            pattern = self.population[p].get_pattern()
            for i in range(len(pattern)):
                tempo = 200
                duration_mult = 60000 / tempo 
                dur = pattern[i][0] * duration_mult
                self.client.send_message("/max", [pattern[i][1], dur])
                print(pattern[i])
                time.sleep(dur / 1000)

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


# def clean_max_input(address: str, *args: List[Any]):
#     print(address)
#     print(args)
#     ms = args[0]
#     pitch = args[1]

#     tempo = 200
#     dur_in_ms = 60000 / tempo
#     total_dur = dur_in_ms * num_beats * 4
#     note_length = ms / total_dur
#     target_patt.append((note_length, pitch))
#     print(target_patt)
    

# def listen2Max(ip,port,path):
#     '''
#     set up server
#     '''
#     # dispatcher to receive message
#     disp = dispatcher.Dispatcher()
#     disp.map(path, clean_max_input)
#     # server to listen
#     server = osc_server.ThreadingOSCUDPServer((ip,port), disp)
#     print("Serving on {}".format(server.server_address))
#     server.serve_forever()
#     # server.handle_request()
#     # server.serve()

# target_patt = [(2, 60), (2, 62), (2, 64), (2, 65), (2, 67), (2, 69), (1, 71), (1, 72), (1, 71), (1, 72)]
target_patt = [(1, 71), (2, 60), (4, 62), (4, 64), (4, 69), (1, 67)]

# pitch_options = [-1, 60, 62, 64, 65, 67, 69, 71, 72]
pitch_options = [60, 62, 64, 65, 67, 69, 71, 72]
num_beats = 16
rhythm_options = [0.25, 0.5, 1, 1.5, 2, 3, 4]

# target_patt = []

# tempo = 60
# dur_in_ms = 60000 / tempo
# total_dur = dur_in_ms * num_beats * 4
# print(total_dur)
# IP = "143.215.114.123"
# R_PORT_TO_MAX = 4980
# endTime = datetime.datetime.now() + datetime.timedelta(milliseconds=total_dur)
# while(True): 
#     listen2Max(IP, R_PORT_TO_MAX, '/max')
#     # if keyboard.is_pressed("s"):
#     #     break  
# print(target_patt)


world = world(target_patt, "melodies.txt", pitch_options, rhythm_options)
world.print_population()
world.run()
