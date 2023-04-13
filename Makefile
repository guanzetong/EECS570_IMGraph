# Makefile for running ep_test.py

# Set the name of the Python interpreter to use
PYTHON=python

# Define the name of the Python script to run
SCRIPT1=ep_test.py
SCRIPT2=test_sl.py
SCRIPT3=test_ep_delayed.py

DESTINATION1 = test_result_ep.txt
DESTINATION2 = test_result_sl.txt
DESTINATION3 = test_result_ep_x.txt

# Define the default target
all: run

# Define a target to run the Python script
ep:
	$(PYTHON) $(SCRIPT1) > $(DESTINATION1)

ep_x:
	$(PYTHON) $(SCRIPT3) > $(DESTINATION3)

sl:
	$(PYTHON) $(SCRIPT2) > $(DESTINATION2)

clean:
	rm -rf *.txt
	rm -rf .vscode