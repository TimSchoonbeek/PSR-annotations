# %%
from pathlib import Path
import time
import json
import os
import csv
# ------------------------- Global varaible setting ------------------------#
rec_path = Path("./")
# ------------------------- Global varaible setting ------------------------#


def load_raw_psr_csv(file: Path) -> list:
    with open(file) as fp:
        reader = csv.reader(fp, delimiter=",", quotechar='"')
        # next(reader, None)  # skip the headers
        data_read = []
        for i, row in enumerate(reader):
            frame_name = row[0]
            state_str = row[1:]
            state = [int(k) for k in state_str]
            data_read.append([frame_name, state])
    return data_read


def only_positive_states(states):
    return [0 if num == -1 else num for num in states]


def make_entry(frame: int, action_id: int, proc_info: list, conf=1) -> dict:
    """ Conf of 1 indicates observed, conf of 0 indicates implied action step. """
    return {"frame": frame, "id": action_id, "description": proc_info[action_id]["description"], "conf": conf}


def convert_all_states_to_steps(observed, proc_info, include_errors=False):
    n_errors = 0
    actions = []
    for i in range(1, len(observed)):
        frame = observed[i][0]
        prev_states = observed[i-1][1]
        curr_states = observed[i][1]
        if not include_errors:
            prev_states = only_positive_states(prev_states)
            curr_states = only_positive_states(curr_states)
        entries, n = convert_states_to_steps(
            prev_states, curr_states, frame, proc_info)
        n_errors += n
        for entry in entries:
            actions.append(entry)
    return actions, n_errors


def convert_states_to_steps(prev: list, curr: list, frame: int, proc_info: list, conf=None) -> list:
    actions = []
    n_error_steps = 0
    for k, (prev_state, curr_state) in enumerate(zip(prev, curr)):
        if prev_state == curr_state:
            continue
        elif prev_state == -1 and curr_state == 0:  # ignore: undoing something wrong is not completing a step
            continue
        elif prev_state == -1 and curr_state == 1:  # correctly assembled from error state
            action_id = k * 3 + 0
        elif prev_state == 0 and curr_state == -1:  # incorrectly assembling something
            action_id = k * 3 + 1
            n_error_steps += 1
        # correctly assembling something from normal state (V
        elif prev_state == 0 and curr_state == 1:
            action_id = k * 3 + 0
        elif prev_state == 1 and curr_state == -1:  # incorrectly assembly/removing from correct state
            print(f"Warning: did not expect someone going from 1 to -1!!")
            n_error_steps += 1
            action_id = k * 3 + 1
        # correctly removing something (V)
        elif prev_state == 1 and curr_state == 0:
            action_id = k * 3 + 2
        entry = make_entry(frame, action_id, proc_info, conf)
        actions.append(entry)
    return actions, n_error_steps


def save_psr_labels(labels, file_path):
    file = open(str(file_path), 'w')
    for entry in labels:
        line = f"{entry['frame']},{entry['id']},{entry['description']}\n"
        file.write(line)
    file.close()
    print(f"Successfully wrote the PSR labels to {file_path}")


def flatten_list(l):
    return [item for sublist in l for item in sublist]


def get_recording_list(folder: Path, train=False, val=False, test=False) -> list:
    assert [train, val, test].count(True) < 2, f"You can currently only retrieve one set or all sets, not two. For " \
                                               f"all sets, simply do not specify a set."
    if train:
        sets = ['train']
    elif val:
        sets = ['val']
    elif test:
        sets = ['test']
    else:
        sets = ['train', 'val', 'test']
    recordings = []
    for set in sets:
        recordings.append([Path(f.path)
                          for f in os.scandir(folder / set) if f.is_dir()])
    return flatten_list(recordings)


def get_procedure_info(file) -> list:
    with open(str(file), "r") as read_file:
        procedure_info = json.load(read_file)
    return procedure_info


if __name__ == '__main__':
    recordings = get_recording_list(rec_path)
    procedure_info = get_procedure_info("procedure_info.json")
    n_error_completions = 0
    for rec in recordings:
        raw_labels_path = rec / "PSR_labels_raw.csv"
        psr_labels_raw = load_raw_psr_csv(raw_labels_path)
        psr_labels, n = convert_all_states_to_steps(
            psr_labels_raw, procedure_info, include_errors=False)
        n_error_completions += n
        print(f"Rec {rec}:\t {n} errors \tTotal errors: \t{n_error_completions}")
        # Be careful when you uncomment this line!!, Make sure you are not overwrite other's files.
        # save_psr_labels(psr_labels, rec / "PSR_labels_with_errors.csv")
        save_psr_labels(psr_labels, rec / "PSR_labels.csv")
