#!/bin/bash

pip3 install -r requirements.txt
git clone https://github.com/vidits-kth/py-itpp.git 
cd py-itpp 
ls .
./install_prerequisites_python3.sh
make install  
pip3 install -e .
cd ..
rm -rf py-itpp 
