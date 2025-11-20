"""Script for handling database ingest"""
from __future__ import annotations

import os
import sys
import json
from os import PathLike
from pathlib import Path
from argparse import ArgumentParser

import pandas as pd
from dotenv import load_dotenv
from supabase import create_client
from supabase import Client

load_dotenv()
url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(url, key)

def build_payload(fp: PathLike | str) -> list[dict]:
    """Builds payload for bulk insert to db"""
    if fp == "-":
        data = json.load(sys.stdin)
    else:
        data = pd.read_parquet(fp)
    
    records = [
        {
            "full_name": athlete,
            "school": school,
            "event_class": event, 
            "time": time,
            "wind": wind,
            "meet_date": str(meet_date),
            "gender":gender,
            "conference_rank":rank
        }
        for athlete, school, event, time, wind, meet_date, gender, rank in zip(
            data['athlete'],
            data['school'],
            data['event'],
            data['time'],
            data['wind'],
            data['date'],
            data['gender'],
            data['conference_rank']
        )
    ]
    return records


def ingest(payload: list[dict]) -> None:
    """asdf"""
    response = (
        supabase.rpc("ingest_performances", {"payload": payload})
        .execute()
    )
    if response.data:
        print(f"Successfully inserted {response.data} records.")        
    else:
        print(f"Error executing INGEST_PERFORMANCES")
    

def main() -> None:
    """Runs script"""
    parser = ArgumentParser()
    parser.add_argument(
        "input_file",
        nargs='?',
        default='-',
        type=lambda f: f if f == "-" else Path(f).expanduser().resolve(),
        metavar="<input_file>",
    )
    args = parser.parse_args()
    payload = build_payload(args.input_file)
    ingest(payload)


if __name__ == "__main__":
    main()