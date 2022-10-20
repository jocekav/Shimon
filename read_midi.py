from mido import MidiFile, tick2second, bpm2tempo
import os
import time
from pythonosc import udp_client
from pythonosc import dispatcher
from pythonosc import osc_server

def play_melodies(pattern):
    IP = "143.215.121.24"
    PORT_TO_MAX = 7980
    client = udp_client.SimpleUDPClient(IP, PORT_TO_MAX)
    for i in range(len(pattern)):
        # tempo = 200
        # duration_mult = 60000 / tempo
        # dur = pattern[i][0] * duration_mult
        client.send_message("/max", [pattern[i][1], (pattern[i][0]*1000)])
        print(pattern[i])
        time.sleep(pattern[i][0])

def get_data(mid):
    mid = MidiFile(mid)
    for i, track in enumerate(mid.tracks):
        print('Track {}: {}'.format(i, track.name))
        parsed = []
        prev_note = 0
        prev_vel = 0
        prev_time = 0
        tpb = mid.ticks_per_beat
        print(tpb)
        for msg in track:
            print(msg)
            if not msg.is_meta and msg.type != 'control_change' and msg.type != 'program_change':
                if msg.velocity != 0:
                    if msg.time > 40:
                        # parsed.append((tick2second(msg.time, tpb, bpm2tempo(220)), 'r'))
                        parsed.append((msg.time, 'r'))
                        prev_time = 0
                    else:
                        # prev_time = tick2second(msg.time, tpb, bpm2tempo(220))
                        prev_time = msg.time
                    prev_note = msg.note
                    prev_vel = msg.velocity
                else:
                    if msg.velocity == 0 and msg.note == prev_note:
                        # parsed.append((tick2second(msg.time, tpb, bpm2tempo(220)) + prev_time, msg.note))
                        parsed.append((msg.time + prev_time, msg.note))
        print(parsed)
        # play_melodies(parsed)
        return parsed

# with open('jazz_licks.txt', 'w') as f:
#     for (root,dirs,files) in os.walk('/Users/jocekav/Documents/GitHub/Shimon/Ebm7', topdown=True):
#         # print (root)
#         # print (dirs)
#         # print (files)
#         # print ('--------------------------------')
#         if not root.endswith('.mscbackup'):
#             for file in files:
#                 if file.endswith('.mid'):
#                     parsed = get_data(root + '/' + file)
#                     f.write(str(parsed) + '\n')

get_data('/Users/jocekav/Documents/GitHub/Shimon/Ebm7/Lick 87/Lick 87 jazz mapping database Ebm7.mid')

