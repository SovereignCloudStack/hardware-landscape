modification_time(){
  python3 -c "import os; print(int(os.path.getmtime('$1')))"
}

create_env(){
   set -e
   rm -rf "${rundir}/venv"
   python3 -m venv "${rundir}/venv"
   source "${rundir}/venv/bin/activate"
   pip install -r "${rundir}/requirements.txt"
   URL="https://www.supermicro.com/Bios/sw_download/633/sum_2.13.0_Linux_x86_64_20230825.tar.gz"
   mkdir "${rundir}/venv/sum"
   cd  "${rundir}/venv/"
   wget -c -O sum.tar.gz "$URL"
   tar zxvf sum.tar.gz --strip-components=1 -C sum
   rm -f sum.tar.gz
   touch -r "${rundir}/requirements.txt" "${rundir}/venv/bin/activate"
   set +e
}


if ! [ -d "${rundir}/venv" ] ;then
   echo "Creating venv: ${rundir}/venv"
   echo
   create_env
elif ( [[ "$(modification_time "${rundir}/requirements.txt")" -gt "$(modification_time "${rundir}/venv/bin/activate")" ]] ||
       [[ "$(modification_time "${rundir}/venv/sum/sum")" -gt  "$(modification_time "${rundir}/venv/bin/activate")" ]]
     );
then
   echo "Recreating venv: ${rundir}/venv"
   echo
   create_env
else
   source "${rundir}/venv/bin/activate"
fi

