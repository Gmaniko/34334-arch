#/bin/bash

cd ~/34334/Routinglab
if [ -n "$(sudo docker ps -f "name=r14" -q)" ]
then
	sudo docker cp router1/ripd.conf router1:/etc/quagga/ripd.conf
	sudo docker cp router1/zebra.conf router1:/etc/quagga/zebra.conf
	sudo docker cp router2/ripd.conf router2:/etc/quagga/ripd.conf
	sudo docker cp router2/zebra.conf router2:/etc/quagga/zebra.conf
	sudo docker cp router3/ripd.conf router3:/etc/quagga/ripd.conf
	sudo docker cp router3/zebra.conf router3:/etc/quagga/zebra.conf
	sudo docker cp router4/ripd.conf router4:/etc/quagga/ripd.conf
	sudo docker cp router4/zebra.conf router4:/etc/quagga/zebra.conf
else
	echo "RoutingLab is not running"
fi
