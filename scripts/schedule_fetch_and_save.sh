#!/bin/bash

while true; do
    # Run your task/command/script here
    fetch_save_data data/raw/automated_fetching_v1
    # Sleep for a minute before the next iteration
    sleep 60
done
