#!/bin/bash

pip &>/dev/null

if [ $? -eq 127 ]
then
	sudo apt-get install python-pip
fi

packages=$(pip list)

deps="beautifulsoup4 requests selenium"

for dep in $deps
do
	test=$(echo "$packages" | grep "$dep")
	if [ -z "$test" ]
	then
		sudo pip install $dep
	fi
done
