venv = . venv/bin/activate
export PATH := ${PATH}:${PWD}/venv/bin

.PHONY: deps
deps: venv/bin/activate ## Install software preconditions to `venv`.

.PHONY: prune
prune:
	rm -rf venv

venv/bin/activate: Makefile requirements.txt
	@which python3 > /dev/null || { echo "Missing requirement: python3" >&2; exit 1; }
	@[ -e venv/bin/python ] || python3 -m venv venv --prompt osism-$(shell basename ${PWD})
	@${venv} && pip3 install -r requirements.txt
	touch venv/bin/activate

.PHONY: deps
sync: deps
	@[ "${BRANCH}" ] && sed -i -e "s/version: .*/version: ${BRANCH}/" gilt.yml || exit 0
	@${venv} && gilt overlay && gilt overlay


.PHONY: check_vault_pass
check_vault_pass:
	@test -r secrets/vaultpass  || ( echo "the file secrets/vaultpass does not exist"; exit 1)
	@if ! git diff-index --quiet HEAD --; then \
	    echo "Error: Uncommitted changes found in the repository."; \
		 git diff; \
	    exit 1; \
	fi


.PHONY: ansible_vault_rekey
ansible_vault_rekey: deps check_vault_pass
	git diff
	bash -c 'echo $RANDOM$RANDOM$RANDOM$RANDOM$RANDOM$RANDOM$RANDOM|base64|head -c 32 > secrets/vaultpass.new
	echo "CREATING A BACKUP"
	cp secrets/vaultpass secrets/vaultpass_backup_$(shell date --date="today" "+%Y-%m-%d_%H-%M-%S")
	${venv} && find environments/ inventory/ -name "*.yml" -not -path "*/.venv/*" -exec grep -l ANSIBLE_VAULT {} \+|\
		sort -u|\
		xargs -n 1 --verbose ansible-vault rekey  -v \
		--vault-password-file secrets/vaultpass \
		--new-vault-password-file secrets/vaultpass.new
	mv secrets/vaultpass.new secrets/vaultpass

.PHONY: ansible_vault_show
ansible_vault_show: deps check_vault_pass
	${venv} && find environments/ inventory/ -name "*.yml" -and -not -path "*/.venv/*" -exec grep -l ANSIBLE_VAULT {} \+|\
		sort -u|\
		xargs -n 1 --verbose ansible-vault view --vault-password-file secrets/vaultpass 2>&1 | less


.PHONY: ansible_vault_edit
ansible_vault_edit: deps check_vault_pass
ifndef FILE
	$(error FILE variable is not set)
endif
	${venv} && ansible-vault edit --vault-password-file secrets/vaultpass ${FILE}
