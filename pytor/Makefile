#! /bin/sh

build:
	mkdir -p bin build
	cat src/pytor.py | sed -e "s/private={.*}/private='stripped'/g" > build/client.py
	# We have stripped the private key from the client
	sleep 10
	/usr/bin/python freeze.py -q -o  ./build -x readline ./build/client.py
	#cd build && make CC="gcc -pthread -static"
	cd build && make
	strip -s -v  build/client
	cp -p build/client bin/


clean:
	rm -rf build bin
	find . -name "*.pyc" -exec rm -rf {} \;
