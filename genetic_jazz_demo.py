import random
from queue import Empty
from collections import Counter
from statistics import mean, median, stdev
from ast import literal_eval
import operator
import math
import pythonosc
from pythonosc import udp_client
from pythonosc import dispatcher
from pythonosc import osc_server
import time
import datetime
from typing import List, Any
from mido import MidiFile, tick2second, bpm2tempo, second2tick


def percentage_pitch(pattern, pitch_options):
    # create dictionary for avail pitches
    pitch_map = dict.fromkeys(pitch_options, 0)
    # count occurance of each note in pattern
    pitch_pattern = pattern.copy()
    pitch_pattern = [pitch[1] % 12 for pitch in pitch_pattern]
    pitch_count = Counter(elem for elem in pitch_pattern)
    # combine dictionaries
    pitch_map = {**pitch_map, **pitch_count}
    pitch_map = {key: pitch_map[key] / len(pitch_pattern) for key in pitch_map.keys()}
    return pitch_map

def percentage_rhythm(pattern, rhythm_options):
    # create dictionary for avail rhythm
    rhythm_map = dict.fromkeys(rhythm_options, 0)
    # count occurance of each note in pattern

    for rhythm in pattern:
        # 32nd note
        if rhythm[0] <= rhythm_options[0]:
            rhythm_map[rhythm_options[0]] += 1
        # cycle through rhythm options and find the one with the smallest difference to the current rhythm
        for note_iter in range(len(rhythm_options)):
            if rhythm[0] <= rhythm_options[note_iter]:
                if abs(rhythm[0] - rhythm_options[note_iter - 1]) <= abs(rhythm[0] - rhythm_options[note_iter]):
                    rhythm_map[rhythm_options[note_iter - 1]] += 1
                else:
                    rhythm_map[rhythm_options[note_iter]] += 1

    rhythm_map = {key: rhythm_map[key] / len(pattern) for key in rhythm_map.keys()}
    return rhythm_map

def percentage_intervals(intervals):
    # create dictionary for avail intervals
    intervals_opt = [-12, -11, -10, -9, -8, -7, -6, -5, -4, -3, -2, -1, 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]
    interval_map = dict.fromkeys(intervals_opt, 0)
    # count occurance of each note in pattern
    interval_count = Counter(elem for elem in intervals)
    # combine dictionaries
    interval_map = {**interval_map, **interval_count}
    interval_map = {key: interval_map[key] / len(intervals) for key in interval_map.keys()}
    return interval_map

def get_total_ticks(pattern):
    total = 0
    for i in range(len(pattern)):
        total += pattern[i][0]
    return total
        
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

def get_intervals(pattern):
    pitch_pattern = pattern.copy()
    pitch_pattern = filter(lambda i: i not in [-1], pitch_pattern)
    first_note = pattern[0][1]
    intervals = []
    for i in range(1, len(pattern)):
        second_note = pattern[i][1]
        intervals.append(second_note - first_note)
        first_note = second_note
    return intervals

def check_if_triplet(pattern, ind, dir):
    try:
        if dir == 'forward':
            if pattern[ind][0] >= rhythm_options[1] - 10 or pattern[ind][0] <= rhythm_options[1] + 10:
                if pattern[ind+1][0] >= rhythm_options[1] - 10 or pattern[ind+1][0] <= rhythm_options[1] + 10:
                    if pattern[ind+2][0] >= rhythm_options[1] - 10 or pattern[ind+2][0] <= rhythm_options[1] + 10:
                        return True
            if pattern[ind][0] >= rhythm_options[3] - 10 or pattern[ind][0] <= rhythm_options[3] + 10:
                if pattern[ind+1][0] >= rhythm_options[3] - 10 or pattern[ind+1][0] <= rhythm_options[3] + 10:
                    if pattern[ind+2][0] >= rhythm_options[3] - 10 or pattern[ind+2][0] <= rhythm_options[3] + 10:
                        return True
            if pattern[ind][0] >= rhythm_options[5] - 10 or pattern[ind][0] <= rhythm_options[5] + 10:
                if pattern[ind+1][0] >= rhythm_options[5] - 10 or pattern[ind+1][0] <= rhythm_options[5] + 10:
                    if pattern[ind+2][0] >= rhythm_options[5] - 10 or pattern[ind+2][0] <= rhythm_options[5] + 10:
                        return True
        else:
            if pattern[ind][0] >= rhythm_options[1] - 10 or pattern[ind][0] <= rhythm_options[1] + 10:
                if pattern[ind-1][0] >= rhythm_options[1] - 10 or pattern[ind-1][0] <= rhythm_options[1] + 10:
                    if pattern[ind-2][0] >= rhythm_options[1] - 10 or pattern[ind-2][0] <= rhythm_options[1] + 10:
                        return True
            if pattern[ind][0] >= rhythm_options[3] - 10 or pattern[ind][0] <= rhythm_options[3] + 10:
                if pattern[ind-1][0] >= rhythm_options[3] - 10 or pattern[ind-1][0] <= rhythm_options[3] + 10:
                    if pattern[ind-2][0] >= rhythm_options[3] - 10 or pattern[ind-2][0] <= rhythm_options[3] + 10:
                        return True
            if pattern[ind][0] >= rhythm_options[5] - 10 or pattern[ind][0] <= rhythm_options[5] + 10:
                if pattern[ind-1][0] >= rhythm_options[5] - 10 or pattern[ind-1][0] <= rhythm_options[5] + 10:
                    if pattern[ind-2][0] >= rhythm_options[5] - 10 or pattern[ind-2][0] <= rhythm_options[5] + 10:
                        return True
    except:
        return False

# attempt to define contour from front and back arcs (disregards middle if one melody is much longer)
def check_order_front_back(patt_1, patt_2):
    front = 0
    back_1 = len(patt_1) - 1
    back_2 = len(patt_2) - 1
    matches_pitch = 0
    matches_rhythm = 0
    while(front < back_1 and front < back_2):
        if ((patt_1[front][0] + 20 <= patt_2[front][0]) and (patt_1[front][0] - 20 >= patt_2[front][0])):
            matches_rhythm += 1
        if (patt_1[front][1] == patt_2[front][1]):
            matches_pitch += 1
        if ((patt_1[back_1][0] + 20 <= patt_2[back_2][0]) and (patt_1[back_1][0] - 20 <= patt_2[back_2][0])):
            matches_rhythm += 1
        if (patt_1[back_1][1] == patt_2[back_2][1]):
            matches_pitch += 1
        front = front + 1
        back_1 = back_1 - 1
        back_2 = back_2 - 1
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
            steps += 1
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
    for i in range(len(pattern)):
        rhythm, pitch = pattern[i]
        expanded_note = [pitch] * int(rhythm)
        expanded_pattern.extend(expanded_note)
    return expanded_pattern

def transpose_to_C(pattern):
    diff = pattern[0] - 60
    transp_patt = []
    for i in range(len(pattern)):
        transp_patt.append(pattern[i] + diff)
    return transp_patt

def get_total_beats(pattern):
    total = 0
    for i in range(0, len(pattern)):
        total = total + pattern[i][0]
    return total


class world:
    def __init__(self, target_pattern, population_file, pitch_options, rhythm_options):
        self.pitch_options = pitch_options
        self.rhythm_options = rhythm_options
        self.target_obj = target(target_pattern, pitch_options, rhythm_options)
        print(target_pattern)
        self.population = self.build_population(population_file)
        self.population.sort(key = lambda x: x.fitness)
        self.population_size = len(self.population)
        # IP = "192.168.1.145"
        IP = "127.0.0.1"

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
        for i in range(1):
            print(self.population[i].get_fitness(), self.population[i].get_pattern())

    def run(self, num_generations=5, survival_rate=.35, mutation_rate=.6):
        for i in range(num_generations): 
        # num_generations = 0       
        # while (self.population[1].fitness > 30):
        #     num_generations += 1
            # check evolution rate
            # print("Generation " + str(i))
            # self.print_population()
            self.population.sort(key = lambda x: x.fitness)
            # cut the population by the survival rate
            ind = int(self.population_size * survival_rate)
            self.population = self.population[:ind]
            # repopulate with the fittest parents
            children = []
            # total_wrong_length = 0
            for parents in range(ind):
                new_gene = self.breed()
                children.append(new_gene)
                # if new_gene.total_beats < num_beats:
                #     total_wrong_length += 1
            self.population.extend(children)
            # # mutate a random amount of genes
            self.mutate(mutation_rate)
            # check evolution rate
            self.population.sort(key = lambda x: x.fitness)
            # self.print_population()
            # if (i > 35):
                # print("Generation " + str(i))
        print("Generation " + str(num_generations))
        self.population.sort(key = lambda x: x.fitness)
        self.print_population()
        return self.population[0].get_pattern()
        # self.play_melodies()
            # input("press enter to continue")
        # print(num_generations)
         
    def breed(self):
        parent1 = (random.choice(self.population))
        parent2 = (random.choice(self.population))
        parent1_total_ticks = parent1.total_ticks
        parent2_total_ticks = parent2.total_ticks
        parent1 = parent1.get_pattern()
        parent2 = parent2.get_pattern()

        total = 0

        new_pattern = []
        front_beats = 0
        back_beats = 0
        front_ind = 0
        back_ind = -1
        length = 0
        while front_beats <= int(parent1_total_ticks / 2):
            try:
                front_beats += parent1[front_ind][0]
            except:
                print(parent1)
                print(front_ind)
                print(front_beats)
            if check_if_triplet(parent1, front_ind, 'forward'):
                for i in range(3):
                    new_pattern.append(parent1[front_ind])
                    front_beats += parent1[front_ind][0]
                    length += 1
                    front_ind += 1
            else:
                new_pattern.append(parent1[front_ind])
                length += 1
                front_ind += 1
            if front_beats > int(parent1_total_ticks / 2):
                break
        while back_beats <= int(parent2_total_ticks / 2):
            try:
                back_beats += parent2[back_ind][0]
            except:
                print(parent2)
                print(back_ind)
                print(back_beats)
            if check_if_triplet(parent2, back_ind, 'back'):
                for i in range(3):
                    new_pattern.insert((length + 1 + back_ind), parent2[back_ind])
                    back_beats += parent2[back_ind][0]
                    length += 1
                    back_ind -= 1
            else:
                new_pattern.insert((length + 1 + back_ind), parent2[back_ind])
                length += 1
                back_ind -= 1
            if back_beats > int(parent2_total_ticks / 2):
                break
        # for i in range(0, len(new_pattern)):
        #     total = total + new_pattern[i][0]
        
        new_gene = gene(new_pattern, self.target_obj, self.pitch_options, self.rhythm_options)
        
        return new_gene

    def mutate(self, mutation_rate):
        for gene in self.population:
            if random.randint(0,99) < (mutation_rate * 100):
                total = 0
                gene_pattern = (gene.get_pattern()).copy()
                gene_total_ticks = gene.total_ticks
                # # decide_mutation = random.randint(0,2)
                if gene_total_ticks > self.target_obj.total_ticks or len(gene_pattern) > len(self.target_obj.pattern):
                    flip_ind = random.randint(0, (len(gene_pattern)-1))
                    del gene_pattern[flip_ind]
                    # gene.reinit(gene_pattern)
                if gene_total_ticks < self.target_obj.total_ticks or len(gene_pattern) < len(self.target_obj.pattern):
                    random_rhythm_ind = random.randint(0, len(rhythm_options)-1)
                    rand_rhythm = rhythm_options[random_rhythm_ind]
                    random_pitch_ind = random.randint(0, len(gene_pattern)-1)
                    rand_pitch = gene_pattern[random_pitch_ind][1]
                    if random_rhythm_ind == 1 or random_rhythm_ind == 3 or random_rhythm_ind == 5:
                        for i in range(3):
                            gene_pattern.insert(random_pitch_ind + i, (rand_rhythm, rand_pitch))
                    else:
                        gene_pattern.insert(random_pitch_ind, (rand_rhythm, rand_pitch))
                    # gene.reinit(gene_pattern)
                # else:
                    # transpose melodies up or down a whole step
                # gene_pattern = (gene.get_pattern()).copy()
                if (random.random() % 2):
                    for i in range(len(gene_pattern)):
                        if gene_pattern[i][1] != -1:
                            gene_pattern[i] = (gene_pattern[i][0], gene_pattern[i][1] + 2)
                else:
                    for i in range(len(gene_pattern)):
                        if gene_pattern[i][1] != -1:
                            gene_pattern[i] = (gene_pattern[i][0], gene_pattern[i][1] - 2)
                gene.reinit(gene_pattern)

    def play_melodies(self, pattern=0):
        # input("press enter to play target")
        # pattern = self.target_obj.pattern
        # for i in range(len(pattern)):
        #     dur_s = tick2second(pattern[i][0], tpb, bpm2tempo(bpm))
        #     self.client.send_message("/max", [pattern[i][1], (dur_s*1000)])
        #     print(pattern[i])
        #     time.sleep(dur_s)
        print("playback")
        if pattern == 0:
            # input("press enter to play next match")
            self.population.sort(key = lambda x: x.fitness)
            pattern = self.population[0].get_pattern()
            i = 0
            total = 0
            while total <= (tpb*num_beats):
                note_dur = pattern[i][0]
                if note_dur < 150:
                    note_dur = note_dur * 2
                total = total + note_dur 
                # if total >= 480*4*16:
                #     return
                dur_s = tick2second(note_dur, tpb, bpm2tempo(bpm))
                self.client.send_message("/max", [pattern[i][1], ((dur_s)*1000)])
                print(pattern[i])
                i = (i + 1) % len(pattern)
                time.sleep(dur_s)
        else:
            i = 0
            total = 0
            # while total <= (tpb*num_beats):
            for i in range(len(pattern)):
                note_dur = pattern[i][0]
                if note_dur < 150:
                    note_dur = note_dur * 2
                total = total + note_dur 
                # if total >= 480*4*16:
                #     return
                dur_s = tick2second(note_dur, tpb, bpm2tempo(bpm))
                self.client.send_message("/max", [pattern[i][1], ((dur_s)*1000)])
                print(pattern[i])
                # i = (i + 1) % len(pattern)
                time.sleep(dur_s)

class target:
    def __init__(self, pattern, pitch_options, rhythm_options):
        self.pattern = pattern
        self.pitch_percentage = percentage_pitch(self.pattern, pitch_options)
        self.rhythm_percentage = percentage_rhythm(self.pattern, rhythm_options)
        self.total_ticks = get_total_ticks(pattern)
        # self.pitch_mct = get_pitch_mct(pattern)
        # self.pitch_range = get_range(pattern)
        self.intervals = get_intervals(pattern)
        self.interval_percentage = percentage_intervals(self.intervals)
        # self.step_to_leap = step_to_leap_ratio(self.intervals)
        # self.abstracted_contour = get_abstracted_contour(pattern)
        self.expanded_patt = expand_pattern(pattern, rhythm_options)
        self.scaled_expanded_patt = transpose_to_C(self.expanded_patt)

class gene:
    def __init__(self, pattern, target, pitch_options, rhythm_options, fitness=0):
        self.pattern = pattern
        self.target = target
        self.pitch_options = pitch_options
        self.rhythm_options = rhythm_options
        self.total_ticks = get_total_ticks(pattern)
        self.pitch_percentage = percentage_pitch(pattern, pitch_options)
        self.rhythm_percentage = percentage_rhythm(pattern, rhythm_options)
        # self.pitch_mct = get_pitch_mct(pattern)
        # self.pitch_range = get_range(pattern)
        self.intervals = get_intervals(pattern)
        self.interval_percentage = percentage_intervals(self.intervals)
        # self.step_to_leap = step_to_leap_ratio(self.intervals)
        # self.abstracted_contour = get_abstracted_contour(pattern)
        self.expanded_patt = expand_pattern(pattern, rhythm_options)
        self.scaled_expanded_patt = transpose_to_C(self.expanded_patt)
        self.fitness = self.get_fitness()

    def reinit(self, pattern):
        self.pattern = pattern
        self.total_ticks = get_total_ticks(pattern)
        self.pitch_percentage = percentage_pitch(self.pattern, self.pitch_options)
        self.rhythm_percentage = percentage_rhythm(self.pattern, self.rhythm_options)
        # self.pitch_mct = get_pitch_mct(self.pattern)
        # self.pitch_range = get_range(self.pattern)
        self.intervals = get_intervals(pattern)
        self.interval_percentage = percentage_intervals(self.intervals)
        # self.step_to_leap = step_to_leap_ratio(self.intervals)
        # self.abstracted_contour = get_abstracted_contour(pattern)
        self.expanded_patt = expand_pattern(pattern, rhythm_options)
        self.scaled_expanded_patt = transpose_to_C(self.expanded_patt)
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

        values = []

        # difference in note density based on vector lengths
        pattern = self.pattern
        target = self.target
        pattern_len = len(pattern)
        target_len = len(target.pattern)

        euclid_sum = .25 * (target_len - pattern_len) ** 2

        # difference in number of beats
        euclid_sum += (self.target.total_ticks - self.total_ticks) ** 2

        # # differences in percentage of each note in the pattern
        # differences = list({k: target.pitch_percentage[k] - self.pitch_percentage[k] for k in target.pitch_percentage}.values())
        # euclid_sum += sum([i ** 2 for i in differences])

        # # differences in percentage of each rhythm in the pattern
        differences = list({k: target.rhythm_percentage[k] - self.rhythm_percentage[k] for k in target.rhythm_percentage}.values())
        # amin, amax = min(differences), max(differences)
        # for i, val in enumerate(differences):
        #     differences[i] = (val-amin) / (amax-amin)
        euclid_sum += sum([5 * i ** 2 for i in differences])

        # differences in central tendency
        # differences = list(map(operator.sub, target.pitch_mct, self.pitch_mct))
        # euclid_sum += sum([i ** 2 for i in differences])

        # differences in pitch range
        # differences = list(map(operator.sub, target.pitch_range, self.pitch_range))
        # euclid_sum += sum([i ** 2 for i in differences])

        # differences in percentage of intervals
        differences = list({k: target.interval_percentage[k] - self.interval_percentage[k] for k in pitch_options}.values())
        # amin, amax = min(differences), max(differences)
        # for i, val in enumerate(differences):
        #     differences[i] = (val-amin) / (amax-amin)
        euclid_sum += sum([10 * (i ** 2) for i in differences])

        # # # differences in order rhythm
        rhythm_contour_sim, melodic_contour_sim = check_order_front_back(target.pattern, self.pattern)
        euclid_sum += ((1 - rhythm_contour_sim) ** 2)
        
        # differences in order pitch
        euclid_sum += ((1 - melodic_contour_sim) ** 2)

        # differences in step/leap
        # euclid_sum = (target.step_to_leap - self.step_to_leap) ** 2

        # differences in direct contour
        differences = list(map(operator.sub, target.scaled_expanded_patt, self.scaled_expanded_patt))
        amin, amax = min(differences), max(differences)
        for i, val in enumerate(differences):
            differences[i] = (val-amin) / (amax-amin)
        euclid_sum += sum([i ** 2 for i in differences])

        # differences in relative contour
        # differences = list(map(operator.sub, target.expanded_patt, self.expanded_patt))
        # euclid_sum += sum([i ** 2 for i in differences])

        return math.sqrt(euclid_sum)
        # could make a line and do a regression for pitch contour - need to preserve the "final note"
        # could do rhythm over time
        # could do the probabilities that a note is followed by another note


def clean_max_input(address: str, *args: List[Any]):
    # print(address)
    # print(args)
    ms = args[0]
    pitch = args[1]

    tempo = bpm2tempo(220)
    # dur_in_ms = 60000 / tempo
    # total_dur = dur_in_ms * num_beats
    # print(ms / 1000)
    note_length = second2tick((ms/1000), tpb, tempo)
    target_patt.append((int(note_length), int(pitch)))
    # print(target_patt)
    

def listen2Max(ip,port,path, serve_time):
    '''
    set up server
    '''
    # dispatcher to receive message
    disp = dispatcher.Dispatcher()
    disp.map(path, clean_max_input)
    # server to listen
    server = osc_server.ThreadingOSCUDPServer((ip,port), disp)
    print("Serving on {}".format(server.server_address))
    print("listening")
    endTime = datetime.datetime.now() + datetime.timedelta(seconds=serve_time)
    while(datetime.datetime.now() <= endTime):
        server.handle_request()

    disp.unmap(path, clean_max_input)
    print("stop listening")



pitch_options = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11]
num_beats = 16
#tick_per_beat from MIDI files
tpb = 480
bpm = 220
# 32nd note, triplet 16th, 16th note, triplet 8th, 8th note, triplet quarter, quarter note, dotted quarter, half note, dotted half, whole
rhythm_options = [tpb/8, int((tpb/4) * .66), tpb/4, int(tpb/2 * .66), tpb/2, int(tpb * .66), tpb, (tpb + tpb/2), tpb * 2, (tpb * 2) + tpb, tpb * 4]

# target_patt = [(1224, -1), (204, 70), (263, 73), (217, 75), (4571, 77), (241, -1), (455, 75), (480, 72)]

global target_patt
target_patt = []
IP = "127.0.0.1"
R_PORT_TO_MAX_NOTES = 1980
global response_patt
response_patt = []
global world_pop
world_pop = []

def listen_and_play(address: str, *args: List[Any]):
    global target_patt
    global response_patt
    global world_pop
    num_beats = args[0]
    ## improv based on head
    if num_beats == 50:
        num_beats = 24
        dur_in_s = 60 / bpm
        total_dur = dur_in_s * num_beats
        # print(total_dur)
        for i in range(6):
            listen2Max(IP, R_PORT_TO_MAX_NOTES, '/max', total_dur)
            print(target_patt)
            world_pop = world(target_patt, "jazz_licks.txt", pitch_options, rhythm_options)
            world_pop.print_population()
            resp = world_pop.run()
            response_patt.extend(resp)
            target_patt = []
            print(response_patt)
        num_beats = 6 * 24
    elif num_beats == 1:
        world_pop.play_melodies(response_patt)
        response_patt = []
    elif num_beats == '127':
        # target is A section
        num_beats = 16
        dur_in_s = 60 / bpm
        total_dur = dur_in_s * num_beats
        saved_target = [(480, 74), (480, 74), (720, 81), (720, 79), (480, 77), (480, 79), (480, 81), (480, 74), (480, 74), (720, 77), (720, 76), (480, 74), (480, 76), (480, 71)]
        world_pop = world(saved_target, "jazz_licks.txt", pitch_options, rhythm_options)
        world_pop.run()
        fitness = 10000
        while fitness > 1000:
            listen2Max(IP, R_PORT_TO_MAX_NOTES, '/max', total_dur)
            new_gene = gene(target_patt, world_pop.target_obj, world_pop.pitch_options, world_pop.rhythm_options)
            fitness = new_gene.get_fitness()
            print(fitness)
            if new_gene.get_fitness() < 1000:
                world_pop.play_melodies()
    else:
        dur_in_s = 60 / bpm
        total_dur = dur_in_s * num_beats
        # print(total_dur)
        listen2Max(IP, R_PORT_TO_MAX_NOTES, '/max', total_dur)
        print(target_patt)
        world_pop = world(target_patt, "jazz_licks.txt", pitch_options, rhythm_options)
        world_pop.print_population()
        response_patt = world_pop.run()
        world_pop.play_melodies(response_patt)
        target_patt = []
        

# dispatcher to receive message
disp = dispatcher.Dispatcher()
disp.map('/listen', listen_and_play)
# server to listen
server = osc_server.ThreadingOSCUDPServer((IP,6000), disp)
print("Serving on {}".format(server.server_address))
server.serve_forever()
# endTime = datetime.datetime.now() + datetime.timedelta(seconds=serve_time)
# while(datetime.datetime.now() <= endTime):
#     server.handle_request()
# # # server.handle_request()
# # # server.server_activate()
# # while()
# # time.sleep(serve_time)
# disp.unmap(path, clean_max_input)