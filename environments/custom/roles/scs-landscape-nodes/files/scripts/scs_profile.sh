umask 0007


__lazy_load_completion(){
   if [ "$1" = "kubectl" ] && ! type -t __start_kubectl &>/dev/null ;then
      logger -t bashrc "init kubectl completion"
      source <(kubectl completion bash)
   elif [ "$1" = "stern" ] && ! type -t __start_stern &>/dev/null ;then
      logger -t bashrc "init stern completion"
      source <(stern --completion=bash)
   elif [ "$1" = "helm" ] && ! type -t __start_helm &>/dev/null ;then
      logger -t bashrc "init helm completion"
      source <(helm completion bash)
   fi
}


KUBE_CONFIG_HASH=""
KUBE_CONFIG_PROMPT=""

get_prompt_kubernetes(){

   local kube_config="$HOME/.kube/config"
   if ! (type -a kubectl &>/dev/null) || ! [[ -f $kube_config ]] ;then
      return 0
   fi

   local kube_current_config_hash="$(md5sum "$kube_config")"

   if [[ -z "$KUBE_CONFIG_HASH" ]] || [[ "$KUBE_CONFIG_HASH" != "$kube_current_config_hash" ]];then
      local kube_access_current="$(kubectl config view --minify --output 'jsonpath={.current-context}%s{..namespace}' 2>/dev/null)"
      if [[ "${kube_access_current}" =~ 'prod' ]];then
         KUBE_CONFIG_PROMPT="$(printf " $kube_access_current" "🔥")"
      else
         KUBE_CONFIG_PROMPT="$(printf " $kube_access_current" "⚡")"
      fi
      export KUBE_CONFIG_PROMPT
      export KUBE_CONFIG_HASH="$kube_current_config_hash"
   fi
   echo -n "$KUBE_CONFIG_PROMPT"
}

get_git_prompt(){
   local the_branch="$(git branch 2>/dev/null | awk '/^\*/{print $2}')"
   if [[ -n "$the_branch" ]];then
      echo -e -n "\\E[3m [${the_branch}] \\E[23m ";
   fi
}


get_error_prompt(){
   local code="$1"
   if [[ $code != 0 ]];then
      printf '\e[1;31m%-6s\e[m' "ERR $code"
   fi
}


if [ -f "${KUBECONFIG:-$HOME/.kube/config}" ] && (type -t kubectl &>/dev/null) ;then
   complete -F __lazy_load_completion kubectl
fi

if type -t stern &>/dev/null;then
   #source <(stern --completion=bash)
   complete -F __lazy_load_completion stern
fi

if type -t helm &>/dev/null;then
   #source <(helm completion bash)
   complete -F __lazy_load_completion helm
fi



if [[ "${TERM}" =~ xterm|linux ]];then
   export PS1='$(get_error_prompt $?)\[\e[32m\]\u@\H(\D{%Y-%m-%d} \t)\[\e[31m\]$(get_prompt_kubernetes)\[\e[33m\] \w\[\e[0m\]$(get_git_prompt) \n\$ \[\e]2;\H \w\a\]'
fi

if [ -d /opt/configuration ];then
   cd /opt/configuration
fi

export PATH="/usr/local/scripts:$PATH"
