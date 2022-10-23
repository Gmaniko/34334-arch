#/bin/bash

cd ~/34334-arch/RoutingLab
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

	sudo docker exec -ti router1 service quagga restart
	sudo docker exec -ti router2 service quagga restart
	sudo docker exec -ti router3 service quagga restart
	sudo docker exec -ti router4 service quagga restart
else
	echo "RoutingLab is not running"
fi
