
all: A2SDV-4C-LN8F.iso A2SDV-8C-LN8F.iso ARS-110M-NR.iso H12SSL-CT.iso H12SSL-NT.iso install
.PHONY: all

SERVER_MEDIA_PATH = /srv/www

A2SDV-4C-LN8F.iso: node-image
	node-image/create-image.sh \
		--config $(PWD)/template.yaml \
		--arg interface1_name=enp2s0f0np0 \
		--arg interface2_name=enp2s0f1np1 \
		--arg layer3_underlay=true \
		--build node-image-build-osism-1
	mv node-image/ubuntu-autoinstall-osism-1.iso A2SDV-4C-LN8F.iso
	touch A2SDV-4C-LN8F.iso

A2SDV-8C-LN8F.iso: node-image
	node-image/create-image.sh \
		--config $(PWD)/template.yaml \
		--arg interface1_name=enp2s0f0np0 \
		--arg interface2_name=enp2s0f1np1 \
		--arg layer3_underlay=true \
		--build node-image-build-1
	mv node-image/ubuntu-autoinstall-osism-1.iso A2SDV-8C-LN8F.iso
	touch A2SDV-8C-LN8F.iso


ARS-110M-NR.iso: node-image
	node-image/create-image.sh \
		--config $(PWD)/template.yaml \
		--arg interface1_name=enp1p1s0f0np0 \
		--arg interface2_name=enp1p1s0f1np1 \
		--arg layer3_underlay=true \
		--build node-image-build-osism-1
	mv node-image/ubuntu-autoinstall-osism-1.iso ARS-110M-NR.iso
	touch ARS-110M-NR.iso

H12SSL-CT.iso: node-image
	node-image/create-image.sh \
		--config $(PWD)/template.yaml \
		--arg interface1_name=enp66s0f0np0 \
		--arg interface2_name=enp66s0f1np1 \
		--arg layer3_underlay=true \
		--build node-image-build-osism-1
	mv node-image/ubuntu-autoinstall-osism-3.iso H12SSL-CT.iso
	touch H12SSL-CT.iso

H12SSL-NT.iso: node-image
	node-image/create-image.sh \
		--config $(PWD)/template.yaml \
		--arg interface1_name=enp65s0f0np0 \
		--arg interface2_name=enp65s0f1np1 \
		--arg layer3_underlay=true \
		--build node-image-build-osism-1
	mv node-image/ubuntu-autoinstall-osism-1.iso H12SSL-NT.iso
	touch H12SSL-NT.iso


node-image:
	git clone https://github.com/osism/node-image.git
	node-image/create-image.sh --show

install:
	cp -lf *.iso ${SERVER_MEDIA_PATH}/
	chmod 644 ${SERVER_MEDIA_PATH}/*.iso
.PHONY: clean

clean:
	rm -rf node-image
	rm -f *.iso
.PHONY: clean
