#!/usr/bin/env bash

echo "Setting up virtualenv"
virtualenv env > /dev/null
# on Windows: env\Scripts\activate.bat
source env/bin/activate > /dev/null

echo "Installing dependencies"
pip install -r requirements.txt > /dev/null

echo "Done."
echo "Run \"source env/bin/activate\" to use the virtualenv"
