#!/bin/bash

pip &>/dev/null

if [ $? -eq 2 ]
then
	apt-get install python-pip
fi

packages=$(pip list)

deps="beautifulsoup4 requests selenium"

for dep in $deps
do
	test=$(echo "$packages" | grep "$dep")
	if [ -z "$test" ]
	then
		pip install $dep
	fi
done
