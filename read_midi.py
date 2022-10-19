from mido import MidiFile
import os

def get_data(mid):
    mid = MidiFile(mid)
    for i, track in enumerate(mid.tracks):
        print('Track {}: {}'.format(i, track.name))
        parsed = []
        prev_note = 0
        prev_vel = 0
        prev_time = 0
        tpb = mid.ticks_per_beat
        for msg in track:
            print(msg)
            if not msg.is_meta and msg.type != 'control_change' and msg.type != 'program_change':
                if msg.velocity != 0:
                    if msg.time > 30:
                        parsed.append((msg.time, 'r'))
                        prev_time = 0
                    else:
                        prev_time = msg.time
                    prev_note = msg.note
                    prev_vel = msg.velocity
                else:
                    if msg.velocity == 0 and msg.note == prev_note:
                        parsed.append(((msg.time + prev_time), msg.note))
        print(parsed)
        return parsed

with open('jazz_licks.txt', 'w') as f:
    for (root,dirs,files) in os.walk('/Users/jocekav/Documents/GitHub/Shimon/Ebm7', topdown=True):
        # print (root)
        # print (dirs)
        # print (files)
        # print ('--------------------------------')
        if not root.endswith('.mscbackup'):
            for file in files:
                if file.endswith('.mid'):
                    parsed = get_data(root + '/' + file)
                    f.write(str(parsed) + '\n')
