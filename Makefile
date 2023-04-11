# Makefile for running ep_test.py

# Set the name of the Python interpreter to use
PYTHON=python

# Define the name of the Python script to run
SCRIPT=ep_test.py

DESTINATION = test_result.txt

# Define the default target
all: run

# Define a target to run the Python script
run:
	$(PYTHON) $(SCRIPT) > $(DESTINATION)