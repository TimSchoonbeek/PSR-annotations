# %%
"""This is a template description for the file

Please fill out a description
"""

__version__ = '0.1'
__author__ = 'Tim Schoonbeek'

import os
import sys
import numpy as np
from pathlib import Path
import cv2
import time


data_folder = Path()  # TODO: Put path of your video directory here
save_folder = Path()  # TODO: Put path of your output directory here
FPS = 10  # FPS of the videos

# these are the IndustReal PSR state names. Modify for your own dataset
state_names = ['(0) base', '(1) front chassis', '(2) front chassis pin', '(3) rear chassis', '(4) short rear chassis',
               '(5) front rear chassis pin', '(6) rear rear chassis pin', '(7) front bracket', '(8) front bracket screw',
               '(9) front wheel assy', '(10) rear wheel assy']


step = 10  # number of frames per step when skipping or rewinding
red = (0, 0, 200)
gray = (50, 50, 50)
green = (0, 200, 0)
font = cv2.FONT_HERSHEY_SIMPLEX
label_file_name = "psr_labels.csv"


def plot_status(state):
    h = 600
    w = 500
    y = 40
    y_factor = 20
    x = 3
    guide = ['hotkey:', '(space) enter change of state', 'w: print labels', 'x: del last PSR entry.', 'a: backword',
             'd: forward', 'f: faster forward', 's: recording name'
             'r: restart labeling.']

    canvas = np.zeros((h, w, 3), np.uint8) + 220

    for i, s in enumerate(state):
        if s == -1:
            text = "!! - " + state_names[i]
            col = red
        elif s == 0:
            text = "   - " + state_names[i]
            col = gray
        elif s == 1:
            text = "> - " + state_names[i]
            col = green
        else:
            raise ValueError(f"State can only be in {-1,0,1} but is {s}")
        cv2.putText(canvas, text, (x, y), font, 0.5, col, thickness=2)
        y += y_factor

    return canvas


def print_labels(labels):
    for entry in labels:
        print(f"{entry[0]}: \t {entry[1]}")
    print()


def save_psr_labels(labels, file_path):
    file = open(str(file_path), 'w')
    for entry in labels:
        state_string = ','.join(map(str, entry[1]))
        csv_entry = str(entry[0]) + "," + state_string + "\n"
        file.write(csv_entry)

    file.close()
    print(f"Successfully wrote the PSR labels to {file_path}")


def determine_initial_state(name):
    """ Here, you can set initial states based on some filename rules. In case of IndustReal, assembly and maintenance have different initial states. """
    if "assy" in name:
        return [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
    elif "main" in name:
        return [1, 1, 1, 1, 0, 1, 1, 1, 1, 1, 1]
    else:
        print("**** -- CAUTION: Could not initialize state based on file name. Initiating all zeros.")
        return [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]


def process_state_change(state, idx):
    update = input(
        "What is the new state (-1: wrong, 0: not done (remove), 1: correctly done (install), q: ignore)?: ")
    if update == "q":
        print("Skipping this entry")
    else:
        update = int(update)
        if update in [-1, 0, 1] and idx in [x for x in range(len(state))]:
            if state[idx] == update:
                print(
                    f"Ignoring entry: idx {idx} already has status {update}!")
            else:
                state[idx] = update
        else:
            print(
                f"**** -- CAUTION: Illegal update {update} for index {idx} attempted --> ignoring this entry")
    return state


if __name__ == '__main__':
    print("Procedure State Recognition -- Labeler")
    split = ['train']
    for set in split:
        recordings = [Path(f.path)
                      for f in os.scandir(data_folder / set) if f.is_dir()]
        for i, rec_path in enumerate(recordings):
            labeling = True

            save_path = save_folder / f"{rec_path.name}_PSR_labels.csv"
            if save_path.exists():
                print(f"Recording {str(rec_path)} already labeled!")
                continue
            print(
                f"{i/len(recordings)*100:.2f}% --> {i}/{len(recordings)}. {rec_path.name}\t Saving labels to {save_path}")

            frame_names = os.listdir(rec_path)
            frame_names.sort()

            del_idxes = []
            for i, name in enumerate(frame_names):
                if not name.endswith('.jpg'):
                    print(
                        f"Warning: found a file {name}. Excluding this from the frames!")
                    del_idxes.append(i)
            for i in sorted(del_idxes, reverse=True):
                del frame_names[i]

            n_frames = len(frame_names)

            psr_labels = []
            current_frame = 0
            hard_quit = False

            # state = determine_initial_state(rec_path.name)
            NUM_DIG_PSR = 17
            state = [0 for _ in range(NUM_DIG_PSR)]
            psr_labels.append([frame_names[current_frame], state.copy()])

            while labeling:
                # 1080 x 720 => 540 x 360
                frame = cv2.imread(
                    str(rec_path / frame_names[current_frame]))
                frame = cv2.resize(frame, (800, 600))

                status_plot = plot_status(state)
                visualize = np.concatenate((frame, status_plot), axis=1)
                cv2.putText(visualize, str(current_frame) + str('/')+str(n_frames), (10, 50), font, 2, (0, 0, 200),
                            thickness=4)
                cv2.imshow("Feed", visualize)
                time.sleep(1 / FPS)
                c = cv2.waitKey(1)
                if c == 27:  # 27 = ESC
                    labeling = False
                    hard_quit = True
                    break
                elif c == ord(' '):
                    inputting = True
                    prev_state = state.copy()
                    while inputting:
                        idx = input(
                            "What is the index of the state change? (0-10, q): ")  # Change is either install or remove
                        if idx.isdigit():
                            state = process_state_change(state, int(idx))
                        else:
                            inputting = False
                    if state != prev_state:
                        # update labels only if there was an actual change
                        psr_labels.append(
                            [frame_names[current_frame], state.copy()])
                elif c == ord('w'):
                    print_labels(psr_labels)
                elif c == ord('x'):
                    if len(psr_labels) > 1:
                        psr_labels = psr_labels[:-1]
                        print(f"Removed last PSR entry. Now the labels are:")
                        print_labels(psr_labels)
                        state = psr_labels[-1][1].copy()
                elif c == ord('a'):
                    # max to prevent going back beyond start
                    current_frame = max(1, current_frame - step)
                elif c == ord('z'):
                    # min to prevent skipping beyond end
                    current_frame = max(1, current_frame - int(10*step))
                elif c == ord('d'):
                    # min to prevent skipping beyond end
                    current_frame = min(n_frames - 1, current_frame + step)
                elif c == ord('f'):
                    # min to prevent skipping beyond end
                    current_frame = min(
                        n_frames - 1, current_frame + int(10*step))

                elif c == ord('s'):
                    print(f"Recording name = {rec_path.name}")
                elif c == ord('r'):
                    ans = input(
                        f"Are you sure you want to restart this recording? (y/n)")
                    if ans == 'y':
                        print(f"Resetting all labels for this recording")
                        current_frame = 0
                        psr_labels = []
                        # state = determine_initial_state(rec_path.name)
                        state = [0 for _ in range(NUM_DIG_PSR)]
                    else:
                        print("not resetting anything.")

                current_frame += 1
                if current_frame == n_frames:
                    labeling = False

            if hard_quit:
                print(
                    f"Hard quit on this video: not saving any frames on {rec_path.name}! Goes to the next recording.")
            else:
                print(f"PSR labels:")
                print_labels(psr_labels)
                save_psr_labels(psr_labels.copy(), save_path)

                print(
                    f"Congratulations! You have labeled recording {rec_path}. On to the next!")
                time.sleep(2)

# %%
