import random

# generates random 8 beat melodies
# output format [(beat_location, beat_dur, pitch)]

# pitch_options = [-1, 60, 62, 64, 65, 67, 69, 71, 72]
pitch_options = [60, 62, 64, 65, 67, 69, 71, 72]
num_beats = 16
rhythm_options = [0.25, 0.5, 1, 1.5, 2, 3, 4]

def gen_melody(num_beats, rhythm_options, pitch_options):
    beats_used = 0
    out = []
    while beats_used < num_beats:
        rand_ind = random.randint(0, (len(rhythm_options) - 1))
        rhy_sel = rhythm_options[rand_ind]
        rand_ind = random.randint(0, (len(rhythm_options) - 1))
        pitch =  pitch_options[rand_ind]
        beats_used, rhy_sel = gen_rhythm(beats_used, rhy_sel, num_beats)
        out.append((rhy_sel, pitch))
    random.shuffle(out)
    return out

def gen_rhythm(beats_used, rhy_sel, num_beats):
        if beats_used + rhy_sel <= num_beats:
            beats_used = beats_used + rhy_sel
            return (beats_used, rhy_sel)
        else:
            if rhy_sel == 1.5:
                rhy_sel = 1
            else:
                rhy_sel /= 2
            return gen_rhythm(beats_used, rhy_sel, num_beats)

# def gen_melody(num_beats, rhythm_options, pitch_options):
#     beats_used = 0
#     out = []
#     while beats_used < num_beats:
#         rand_ind = random.randint(0, 6)
#         rhy_sel = rhythm_options[rand_ind]
#         rand_ind = random.randint(0, num_beats)
#         pitch =  pitch_options[rand_ind]
#         beats_used, rhy_sel = gen_rhythm(beats_used, rhy_sel, num_beats)
#         out.append(((beats_used - rhy_sel), rhy_sel, pitch))
#     # random.shuffle(out)
#     return out

# def gen_rhythm(beats_used, rhy_sel, num_beats):
#         if beats_used + rhy_sel <= num_beats:
#             beats_used = beats_used + rhy_sel
#             return (beats_used, rhy_sel)
#         else:
#             if rhy_sel == 1.5:
#                 rhy_sel = 1
#             else:
#                 rhy_sel /= 2
#             return gen_rhythm(beats_used, rhy_sel, num_beats)


with open('melodies.txt', 'w') as f:
    for x in range(1000):
       out = gen_melody(num_beats, rhythm_options, pitch_options)
       f.write(str(out) + '\n')