#!/bin/bash

for file in `ls tests/err*` 
do  
    echo $file && python3 main.py $file ss
done