#!/bin/bash
sed -i 's/\r$//' setup.sh

echo "Installing dependencies..."
pip install -r requirements.txt

echo "Setting up database migrations..."
python manage.py makemigrations
python manage.py migrate

echo "Importing data..."
python manage.py import-mep-data
python manage.py import-mep-membership-data
python manage.py import_votes

echo "Setup complete! Before you run the server, make sure to add the required CSV files to your database as instructed in the README"
