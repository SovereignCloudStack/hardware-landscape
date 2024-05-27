
all: A2SDV-4C-LN8F.iso A2SDV-8C-LN8F.iso ARS-110M-NR.iso H12SSL-CT.iso H12SSL-NT.iso
.PHONY: all

A2SDV-4C-LN8F.iso: node-image
	node-image/create-image-flavor.sh --layer3_underlay \
		--config $(PWD)/template.yaml \
		--arg interface1_name=enp2s0f0np0 \
		--arg interface2_name=enp2s0f1np1 \
		--build node-image-build-osism-1
	mv node-image/ubuntu-autoinstall-osism-1.iso A2SDV-4C-LN8F.iso

A2SDV-8C-LN8F.iso: node-image
	node-image/create-image-flavor.sh --layer3_underlay \
		--config $(PWD)/template.yaml \
		--arg interface1_name=enp2s0f0np0 \
		--arg interface2_name=enp2s0f1np1 \
		--build node-image-build-osism-1
	mv node-image/ubuntu-autoinstall-osism-1.iso A2SDV-8C-LN8F.iso


ARS-110M-NR.iso: node-image
	node-image/create-image-flavor.sh --layer3_underlay \
		--config $(PWD)/template.yaml \
		--arg interface1_name=enp1p1s0f0np0 \
		--arg interface2_name=enp1p1s0f1np1 \
		--build node-image-build-osism-1
	mv node-image/ubuntu-autoinstall-osism-1.iso ARS-110M-NR.iso

H12SSL-CT.iso: node-image
	node-image/create-image-flavor.sh --layer3_underlay \
		--config $(PWD)/template.yaml \
		--arg interface1_name=enp66s0f0np0 \
		--arg interface2_name=enp66s0f1np1 \
		--build node-image-build-osism-1
	mv node-image/ubuntu-autoinstall-osism-1.iso H12SSL-CT.iso

H12SSL-NT.iso: node-image
	node-image/create-image-flavor.sh --layer3_underlay \
		--config $(PWD)/template.yaml \
		--arg interface1_name=enp65s0f0np0 \
		--arg interface2_name=enp65s0f1np1 \
		--build node-image-build-osism-1
	mv node-image/ubuntu-autoinstall-osism-1.iso H12SSL-NT.iso


node-image:
	git clone https://github.com/osism/node-image.git

clean:
	rm -rf node-image
	rm -f *.iso
.PHONY: clean
