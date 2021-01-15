#!/bin/zsh

pip3 install -r requirements.txt
git clone https://github.com/vidits-kth/py-itpp.git 
./py-itpp/install_prerequisites_python3.sh
make install  
pip3 install -e .  
rm -rf py-itpp 