#!/bin/zsh

ZPODFACTORY_CONFIG_FILE="/etc/zpodfactory.config"

log() {
    local message="$1"                           # The message to log
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S') # Current timestamp

    echo "$message"
    # Append the timestamp and message to the CONFIG_FILE

    echo "[$timestamp] $message" >>$ZPODFACTORY_CONFIG_FILE
}

appliance_install_uv() {
    # uv is the Python package & toolchain manager used by every zpodcore
    # subproject (replaces the old pyenv + poetry combo). We install it
    # here so it is available early in the boot sequence for every
    # subsequent function that needs Python tooling (zpodcore itself,
    # zpod-vcf-deployer, etc.). Requires internet access — call after
    # appliance_check_internet_access.
    #
    # IMPORTANT: this function is called at firstboot from a systemd
    # unit with a sparse environment. $HOME may be unset, and the
    # interactive shell init files (~/.zshrc, ~/.bashrc) that the uv
    # installer patches are NOT sourced by this non-interactive script.
    # The function must therefore guarantee that `uv` is on PATH and
    # callable in the current process before returning.

    local uv_bin_dir="$HOME/.local/bin"
    local uv_bin="$uv_bin_dir/uv"

    if command -v uv &>/dev/null; then
        log "uv already installed ($(uv --version 2>/dev/null)). Skipping install."
    else
        log "Installing uv..."
        # Pin the install location explicitly — the installer respects
        # UV_INSTALL_DIR and XDG_BIN_HOME. Being explicit means we know
        # exactly where the binary lands regardless of the invoking
        # user's XDG env (or lack thereof).
        UV_INSTALL_DIR="$uv_bin_dir" \
            curl -LsSf https://astral.sh/uv/install.sh | sh &>> "$ZPODFACTORY_CONFIG_FILE" || {
            log "Failed to install uv."
            exit 1
        }
    fi

    # Verify the binary actually landed on disk before we touch PATH —
    # this catches a silent installer failure that `command -v` wouldn't
    # catch until after we rehash.
    if [[ ! -x "$uv_bin" ]]; then
        log "uv binary not found at $uv_bin after install. Aborting."
        exit 1
    fi

    # Prepend the install dir to PATH for the current process so every
    # subsequent function in this script sees `uv`.
    case ":$PATH:" in
        *":$uv_bin_dir:"*) ;;
        *) export PATH="$uv_bin_dir:$PATH" ;;
    esac

    # Flush zsh's command hash table — without this, a later bare `uv`
    # call can still resolve to a stale "command not found" cache entry
    # even though PATH is now correct.
    rehash 2>/dev/null || hash -r 2>/dev/null || true

    # Also persist PATH into ~/.zshrc for future interactive shells on
    # the appliance (post-firstboot operator logins). The uv installer
    # usually handles this itself, but we make it explicit and
    # idempotent so it survives re-runs and older installer scripts.
    if [[ -f "$HOME/.zshrc" ]] && ! grep -q 'HOME/.local/bin' "$HOME/.zshrc"; then
        echo 'export PATH="$HOME/.local/bin:$PATH"' >> "$HOME/.zshrc"
    fi

    # Final sanity check — uv must be callable via PATH lookup, not just
    # via absolute path, because later code uses bare `uv` invocations.
    if ! command -v uv &>/dev/null; then
        log "uv is not on PATH after install (PATH=$PATH). Aborting."
        exit 1
    fi

    log "uv installed and on PATH: $(uv --version) at $(command -v uv)"
}

# Function to configure zPodFactory
appliance_config_zpodfactory() {
    log "Configuring zPodFactory..."
    # Your zPodFactory configuration commands here

    # Update apt repositories
    apt-get -qq update &>> $ZPODFACTORY_CONFIG_FILE

    # Install docker and docker compose plugins for zPodFactory App stack
    apt-get -qq install \
     -o Dpkg::Progress-Fancy="0" \
     -o APT::Color="0" \
     -o Dpkg::Use-Pty="0" \
     -y docker-ce docker-compose-plugin &>> $ZPODFACTORY_CONFIG_FILE

    # Install system packages needed by zPodFactory:
    #  - git: cloning zpodcore
    #  - gcc + libpq-dev: required by `uv sync` on the host when
    #    psycopg2 (used by zpodapi and zpodengine) resolves to a source
    #    distribution. psycopg2's setup.py invokes `cc` directly;
    #    installing gcc creates the /usr/bin/cc alternative link.
    #  - just, bc: justfile runner + column math in the justfile itself
    apt-get -qq install \
     -o Dpkg::Progress-Fancy="0" \
     -o APT::Color="0" \
     -o Dpkg::Use-Pty="0" \
     -y git gcc libpq-dev just bc &>> $ZPODFACTORY_CONFIG_FILE

    # NOTE: uv is installed earlier in main() by appliance_install_uv.
    # uv manages the Python toolchain itself (no pyenv, no system-level
    # python3-dev build chain), so build-essential/libssl-dev/etc. are
    # no longer needed on the appliance.

    # Create root directory for project
    mkdir -p ~/git

    # Clone zPodFactory main repository
    log "Cloning zPodFactory main repository ($OVF_GIT_REPOSITORY, branch: $OVF_GIT_BRANCH)..."
    git clone -q "$OVF_GIT_REPOSITORY" --branch "$OVF_GIT_BRANCH" ~/git/zpodcore &>/dev/null

    # Create one uv-managed virtualenv per subproject. Each subproject
    # is released independently and pins its own Python interpreter via
    # `requires-python`; `uv sync --frozen` downloads the matching
    # CPython build automatically (no pyenv compile step).
    for i in zpodsdk zpodapi zpodengine zpodcli; do
        cd ~/git/zpodcore/$i
        log "Running uv sync for $i..."
        uv sync --frozen &>> "$ZPODFACTORY_CONFIG_FILE"
    done

    cd ~/git/zpodcore

    # Set default env to VM settings
    log "Setting up default environment for docker compose stack..."

    cp .env.default .env
    sed -i "s/X.X.X.X/$OVF_IPADDRESS/g" .env

    # Start the zPodFactory services
    log "Building Docker Compose images..."
    docker compose build -q

    log "Starting Docker Compose zPodFactory stack..."

    # Set terminal width to acceptable size for clean logs as this is launched in a script
    export COLUMNS=140
    just -q zpodcore-start-background

    sleep 10

    # Set zcli default entry/token for potential early troubleshooting.
    TOKEN=$(docker compose logs | grep zpodapi | grep 'API Token:' | awk '{ print $5 }' | tr -d '\r')

    just zcli factory add zpodfactory -s http://$OVF_IPADDRESS:8000 -t $TOKEN -a &>> $ZPODFACTORY_CONFIG_FILE


    # Execute first flow to prep prefect
    # This avoids the unique key error "uq_configuration__key" problem when scheduling a lot of deployments to run at the same time
    log "Executing first deployment workflow to prep prefect..."
    just -q zpodengine-cmd python src/zpodengine/flow_init.py

    log "Creating zPodFactory Engine deployments workflows in Prefect..."
    just -q zpodengine-deploy-all


    just zcli setting update zpodfactory_host -v $OVF_IPADDRESS &>> $ZPODFACTORY_CONFIG_FILE
    just zcli setting update zpodfactory_default_domain -v $OVF_DOMAIN &>> $ZPODFACTORY_CONFIG_FILE

    # zpodfactory_ssh_key: use OVF value if set, otherwise generate a key pair for the current user
    mkdir -p "$HOME/.ssh"
    chmod 700 "$HOME/.ssh"
    if [[ -n "$OVF_SSHKEY" ]]; then
        zpodfactory_ssh_key="$OVF_SSHKEY"
    else
        keytype="rsa"
        priv_key="$HOME/.ssh/zpodfactory_$keytype"
        pub_key="$HOME/.ssh/zpodfactory_$keytype.pub"
        if [[ ! -f "$priv_key" ]]; then
            ssh-keygen -t "$keytype" -b 4096 -f "$priv_key" -N "" -q
            log "Generated zPodFactory SSH key at $priv_key"
        fi
        zpodfactory_ssh_key=$(cat "$pub_key")

        # SSH config: use generated zpodfactory key for hosts in the default domain
        {
            [[ -f "$HOME/.ssh/config" ]] && echo ""
            echo "Host *.$OVF_DOMAIN"
            echo "    StrictHostKeyChecking no"
            echo "    IdentityFile $priv_key"
        } >> "$HOME/.ssh/config"
        chmod 600 "$HOME/.ssh/config"
        log "Updated \$HOME/.ssh/config for *.$OVF_DOMAIN"
    fi
    just zcli setting update zpodfactory_ssh_key -v "$zpodfactory_ssh_key" &>> $ZPODFACTORY_CONFIG_FILE

    # Add Default library
    just zcli library create default -u https://github.com/zpodfactory/zpodlibrary -d "Default zPodFactory library" &>> $ZPODFACTORY_CONFIG_FILE

    # Enable component zcore
    just zcli component enable zcore-13.5 &>> $ZPODFACTORY_CONFIG_FILE

    # Store API token for zpodweb and zpod-vcf-deployer (from .zclirc written by zcli factory add)
    local zclirc="$HOME/.config/zcli/.zclirc"
    if [[ -f "$zclirc" ]]; then
        ZPOD_API_TOKEN=$(grep 'zpod_api_token' "$zclirc" 2>/dev/null | cut -d "=" -f 2 | tr -d '\r' | xargs)
    fi

    log "zPodFactory setup complete."
}

appliance_config_zpodweb_ui() {
    log "Configuring zPodFactory Web UI (zpodweb)..."

    local repo_dir=~/git/zpodweb

    if [[ ! -d "$repo_dir/.git" ]]; then
        log "Cloning zpodweb repository..."
        git clone -q https://github.com/zPodFactory/zpodweb "$repo_dir" &>> "$ZPODFACTORY_CONFIG_FILE" || {
            log "Failed to clone zpodweb repository."
            return 1
        }
    else
        log "zpodweb repository already present. Skipping clone."
    fi

    cd "$repo_dir" || {
        log "Failed to enter zpodweb directory."
        return 1
    }

    if [[ ! -f ".env" && -f ".env.example" ]]; then
        log "Creating .env from .env.example for zpodweb..."
        cp .env.example .env
    elif [[ ! -f ".env" ]]; then
        log "Creating empty .env for zpodweb (no .env.example found)..."
        touch .env
    fi

    # Configure API URL
    if grep -q '^ZPODWEB_DEFAULT_ZPODFACTORY_API_URL=' .env; then
        sed -i "s|^ZPODWEB_DEFAULT_ZPODFACTORY_API_URL=.*$|ZPODWEB_DEFAULT_ZPODFACTORY_API_URL=http://$OVF_IPADDRESS:8000|" .env
    fi

    # Set API token (from ZPOD_API_TOKEN set by appliance_config_zpodfactory)
    if [[ -n "$ZPOD_API_TOKEN" ]]; then
        if grep -q '^ZPODWEB_DEFAULT_ZPODFACTORY_API_TOKEN=' .env; then
            sed -i "s|^ZPODWEB_DEFAULT_ZPODFACTORY_API_TOKEN=.*$|ZPODWEB_DEFAULT_ZPODFACTORY_API_TOKEN=$ZPOD_API_TOKEN|" .env
        else
            echo "ZPODWEB_DEFAULT_ZPODFACTORY_API_TOKEN=$ZPOD_API_TOKEN" >> .env
        fi
        log "Set ZPODWEB_DEFAULT_ZPODFACTORY_API_TOKEN from ZPOD_API_TOKEN."
    fi

    # Start zpodweb Docker Compose stack
    if [[ -f "docker-compose.yml" ]]; then
        log "Starting zpodweb Docker Compose stack..."
        docker compose up -d &>> "$ZPODFACTORY_CONFIG_FILE" || log "Failed to start zpodweb Docker Compose stack."
    else
        log "No docker-compose.yml found for zpodweb, skipping stack startup."
    fi
}

appliance_config_vcf_offline_depot() {
    log "Preparing VCF offline depot..."

    local repo_dir=~/git/doc-vcf-offlinedepot

    if [[ ! -d "$repo_dir/.git" ]]; then
        log "Cloning doc-vcf-offlinedepot repository..."
        git clone -q https://github.com/tsugliani/doc-vcf-offlinedepot "$repo_dir" &>> "$ZPODFACTORY_CONFIG_FILE" || {
            log "Failed to clone doc-vcf-offlinedepot repository."
            return 1
        }
    else
        log "doc-vcf-offlinedepot repository already present. Skipping clone."
    fi


    # Ensure depot root directory exists (used later by UMDS / VCF tooling)
    mkdir -p /depot

    # Ensure the service-network exists for external compose stacks in the repo
    if ! docker network ls --format '{{.Name}}' | grep -q '^service-network$'; then
        log "Creating Docker network service-network..."
        docker network create service-network &>> "$ZPODFACTORY_CONFIG_FILE" || log "Failed to create Docker network service-network."
    else
        log "Docker network service-network already exists."
    fi

    log "VCF offline depot repository ready."
}

appliance_config_zpod_vcf_deployer() {
    log "Configuring zPod VCF Deployer..."

    local repo_dir=~/git/zpod-vcf-deployer

    if [[ ! -d "$repo_dir/.git" ]]; then
        log "Cloning zpod-vcf-deployer repository..."
        git clone -q https://github.com/zPodFactory/zpod-vcf-deployer "$repo_dir" &>> "$ZPODFACTORY_CONFIG_FILE" || {
            log "Failed to clone zpod-vcf-deployer repository."
            return 1
        }
    else
        log "zpod-vcf-deployer repository already present. Skipping clone."
    fi

    cd "$repo_dir" || {
        log "Failed to enter zpod-vcf-deployer directory."
        return 1
    }

    if [[ ! -f ".env" && -f "env_example.txt" ]]; then
        log "Creating .env from env_example.txt for zpod-vcf-deployer..."
        cp env_example.txt .env
    fi

    # Configure base URL to local zPodFactory
    if grep -q '^ZPODFACTORY_BASE_URL=' .env; then
        sed -i "s|^ZPODFACTORY_BASE_URL=.*$|ZPODFACTORY_BASE_URL=http://$OVF_IPADDRESS:8000|" .env
    fi

    # Configure offline depot hostname (FQDN)
    local depot_fqdn="$OVF_HOSTNAME.$OVF_DOMAIN"
    if grep -q '^VCF_OFFLINE_DEPOT_HOSTNAME=' .env; then
        sed -i "s|^VCF_OFFLINE_DEPOT_HOSTNAME=.*$|VCF_OFFLINE_DEPOT_HOSTNAME=$depot_fqdn|" .env
    fi

    # Configure offline depot username (static)
    if grep -q '^VCF_OFFLINE_DEPOT_USERNAME=' .env; then
        sed -i "s|^VCF_OFFLINE_DEPOT_USERNAME=.*$|VCF_OFFLINE_DEPOT_USERNAME=secure|" .env
    fi

    # Set API token (from ZPOD_API_TOKEN set by appliance_config_zpodfactory)
    if [[ -n "$ZPOD_API_TOKEN" ]]; then
        if grep -q '^ZPODFACTORY_ACCESS_TOKEN=' .env; then
            sed -i "s|^ZPODFACTORY_ACCESS_TOKEN=.*$|ZPODFACTORY_ACCESS_TOKEN=$ZPOD_API_TOKEN|" .env
        fi
        log "Set ZPODFACTORY_ACCESS_TOKEN from ZPOD_API_TOKEN."
    fi

    # Start deployer stack if docker-compose is present
    if [[ -f "docker-compose.yml" ]]; then
        log "Starting zpod-vcf-deployer Docker Compose stack..."
        docker compose up -d &>> "$ZPODFACTORY_CONFIG_FILE" || log "Failed to start zpod-vcf-deployer Docker Compose stack."
    else
        log "No docker-compose.yml found for zpod-vcf-deployer, skipping stack startup."
    fi
}

appliance_config_wireguard() {
    if [[ "${OVF_SETUP_WIREGUARD:l}" != "true" ]]; then
        log "Wireguard setup disabled..."
        return 1
    fi

    log "Setting up Wireguard..."

    mkdir -p ~/wireguard
    cp ~/docker-compose.wireguard.yml ~/wireguard/docker-compose.yml

    sed -i "s/HOSTNAME/$OVF_HOSTNAME/g" ~/wireguard/docker-compose.yml
    sed -i "s/IPADDRESS/$OVF_IPADDRESS/g" ~/wireguard/docker-compose.yml
    sed -i "s/DOMAIN/$OVF_DOMAIN/g" ~/wireguard/docker-compose.yml

    # log "Launching Wireguard Docker Compose Stack..."
    # cd ~/wireguard
    # docker compose up -d

    rm -f ~/docker-compose.wireguard.yml
}

# Main execution logic
main() {
    appliance_install_uv
    appliance_config_zpodfactory
    appliance_config_zpodweb_ui
    appliance_config_vcf_offline_depot
    appliance_config_zpod_vcf_deployer
    appliance_config_wireguard

    log "zPodFactory setup complete"
}

# Invoke the main function
main
