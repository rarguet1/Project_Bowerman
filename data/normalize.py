"""Script for normalizing the webscrapped data. Meant to be used alongside """
from __future__ import annotations

import sys
import json
from os import PathLike
from pathlib import Path
from argparse import ArgumentParser
from datetime import datetime

import pandas as pd

def load_json(fp: PathLike | str) -> dict:
    """Loads JSON Data"""
    try:
        if fp == "-":
            data = json.load(sys.stdin)
        else:
            with open(fp, 'r') as file:
                data = json.load(file)
        return data
    
    except FileNotFoundError:
        print(f"Error: {fp} not found.")
    except json.JSONDecodeError:
        print(f"Error: Invalid JSON format in {fp}.")


def save_data(
        data: dict,
        stdout: bool=False,
) -> None:
    """Saves parquet to normalized directory or writes json to stdout"""
    if stdout:
        json.dump(data, sys.stdout)
        sys.stdout.write("\n")
        sys.stdout.flush()
        return

    # Writes out to normalized/
    cwd = Path(__file__).parent
    (dest_dir := (cwd / "normalized")).mkdir(exist_ok=True)

    existing_indices = (
        int(file.stem.split("_")[1])
        for file in dest_dir.glob("performances_*.parquet")
    )
    idx = max(existing_indices, default=0) + 1
    df = pd.DataFrame(data)
    df.to_parquet(dest_dir / f"performances_{idx:06d}.parquet")


def peeking_at_data(data: dict) -> None:
    """asdf"""
    look_thru = data['100m']
    for i, field in enumerate(look_thru):
        print(f"Entry {i}:\n date: {datetime.strptime(field['meet_date'], '%b %d, %Y').date()}")
        #print(f"Entry {i}:\n{field}")


def performances_norm_df_format(
        data: dict,
        school: str | None = None,
        gender: str | None = None,
) -> dict:
    """Function to normalize the performance list json to DataFrame friendly format for db ingest
    
    Parameters
    ----------
    data : dict
        Unnormalized dict of events w/ list of performance dicts
    
    school : str
        Name of the school or team
    
    Returns
    -------
    norm : dict
        Normalized dict for a pandas.DataFrame

    Notes
    -----
    This is based on the webscrapping scripts made in [INSERT FP LATER]
    """
    ret = {
        "athlete": [],
        "event": [],
        "time": [],
        "wind": [],
        "date": [],
        "school": [], 
        "gender": [],
        "conference_rank": []
    }
    for event in data:
        for record in data[event]:
            ret["time"].append(record['time'])
            ret['wind'].append(record['wind'] if record['wind'] else "UNKNOWN")
            ret["school"].append(school if school else "UNKNOWN")
            ret['date'].append(datetime.strptime(record['meet_date'], '%b %d, %Y').date())
            ret["athlete"].append(record['athlete']['text'])
            ret["event"].append(event)
            ret["gender"].append(gender if gender else "UNKNOWN")
            ret["conference_rank"].append("UKNOWN")
    
    return ret


def conference_norm_df_format(
        data: dict,
) -> dict:
    """asdf"""
    ret = {
        "athlete": [],
        "event": [],
        "time": [],
        "wind": [],
        "date": [],
        "school": [], 
        "gender": [],
        "conference_rank": []
    }
    for event in data:
        for record in data[event]:
            ret["athlete"].append(record["athlete"])
            ret["event"].append(event)
            ret["time"].append(record["time"])
            ret["wind"].append(record["wind"] if record['wind'] else "UNKNOWN")
            ret["date"].append(datetime.strptime(record['meet_date'], '%b %d, %Y').date().isoformat())
            ret["school"].append(record["team"])
            ret["gender"].append(record["gender"] if record["gender"] else "UNKNOWN")
            ret["conference_rank"].append(record["conference_rank"])
    return ret


# def performance_norm(data: dict) -> dict:
#     """Function to normalize the performance list json to the format
#     {athlete: {event: [(time, wind, date),...]}, school:[name]}
#     """
#     ret = {}
#     for event in data:
#         for record in data[event]:
#             info = record['time'], record['wind'], record['meet_date']

#             if (athlete := record['athlete']['text']) not in ret:    
#                 ret[athlete] = {
#                     event: [info]
#                 }
#             elif event not in ret[athlete]:
#                 ret[athlete][event] = [info]
#             else:
#                 ret[athlete][event].append(info)

#     return ret


def main() -> None:
    """Runs Script"""
    parser = ArgumentParser(
        description="Loads and reformats webscraped data",
    )
    parser.add_argument(
        "input_file",
        nargs='?',
        default='-',
        type=lambda f: f if f == "-" else Path(f).expanduser().resolve(),
        metavar="<input_file>",
    )
    parser.add_argument(
        "--stdout",
        action="store_true",
        help="""An option if you want to immediately redirect/pipe a dataframe friendly json \
            otherwise this will write to normalized/ directory."""
    )
    # TODO:
    # 1. Need to add an arg for handling conference performances
    # 2. Need to write something for normalizing conference performances

    args = parser.parse_args()
    data = load_json(args.input_file)
    
    if args.input_file != "-":
        # school_gender_*.json
        school = args.input_file.stem.split("_")[0]
        gender = args.input_file.stem.split("_")[1]
        #data = performances_norm_df_format(data, school, gender)
        data = conference_norm_df_format(data)
    else:
        #data = performances_norm_df_format(data)
        data = conference_norm_df_format(data)

    #peeking_at_data(data)
    save_data(data, args.stdout)


if __name__ == "__main__":
    main()