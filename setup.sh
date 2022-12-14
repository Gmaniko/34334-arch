#/bin/bash
cd ~/34334-arch

if [ -z "$(sudo docker images 34334:ids -q)" ] 
then 
	sudo pip install gdown
	gdown --id 1WscKcNj1wNrviL81FZZgnai3NsHzzIle
	tar -vxf ids.tar.gz
	sudo docker load -i ids.tar
	rm ids.tar
	rm ids.tar.gz
fi 
sudo pacman -S --needed bridge-utils
sudo python lab_webapp.py
