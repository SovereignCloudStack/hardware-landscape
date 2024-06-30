#!/bin/bash

for vg in $(vgs | awk '$1 ~ /^ceph-/ {print $1}'); do
    echo "** VOLUME GROUP ${vg}"
    echo
    echo "Deactivate all logical volumes in the volume group ${vg}"

    lvchange -an ${vg}
    if [ "$?" != "0" ];then
	    echo "NOT SUCCESFUL"
	    exit 1
    fi	    

    echo "Remove all logical volumes in the volume group ${vg}"
    for lv in $(lvs --noheadings -o lv_name ${vg}); do
	echo " -> Remove volume ${vg}/${lv}"
        lvremove -f ${vg}/${lv}
    done

    echo "Remove the volume group ${vg}"
    vgremove -f ${vg}
done

