#!/bin/bash

# Ensure that the Python environment is set up correctly
echo "Starting the create_db function from db.py..."

# Run the Python script and execute the specific function
python3 -c "from create_db import create_db_for_data_path; create_db_for_data_path()"

echo "Database creation completed."
