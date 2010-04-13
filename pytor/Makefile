#! /bin/sh

build:client server
	mkdir bin
	cp build_server/server bin/
	cp build_client/client bin/
client:
	/usr/bin/python freeze.py -q -o  ./build_client ./src/client.py
	cd build_client && make
	cd ..

server:
	/usr/bin/python freeze.py -q -o  ./build_server ./src/server.py
	cd build_server && make
	cd ..

clean:
	rm -rf build* bin*
	find . -name "*.pyc" -exec rm -rf {} \;
