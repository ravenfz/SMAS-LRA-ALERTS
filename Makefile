all: install tweepy

install:
	chmod +x process_occurrences.py
	chmod +x run_smas_lra.sh

tweepy:
	pip3 install tweepy
