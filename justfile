set dotenv-load

ns := "peoplewa-import"

# Choose a task to run
default:
  just --choose

# Install project tools
prereqs:
  uv sync
  wget "https://s3.amazonaws.com/mountpoint-s3-release/latest/{{arch()}}/mount-s3.deb"
  sudo apt-get -y update && sudo apt-get install -y ./mount-s3.deb
  rm ./mount-s3.deb
  uv run quarto install tinytex
  # curl -sL "https://yihui.org/tinytex/install-bin-unix.sh" | sh


  minikube config set memory no-limit
  minikube config set cpus no-limit

clean:
  kubectl delete ns {{ns}}

# Show local/env secrets for injecting into other tools
@show-secrets:
  jq -n 'env | {VARIABLE_NAME1, VARIABLE_NAME2}'

# Setup minikube
minikube:
  which k9s || just prereqs
  kubectl get nodes || minikube status || minikube start # if kube configured use that cluster, otherwise start minikube

# Configures harvest-secret using kubectl
#install-harvest-secret:
#  cat kustomize/secrets-template.yaml | NAME=harvest-secret SECRET_JSON=$(just show-secrets) envsubst | kubectl apply -n {{ns}} -f -

# Forward mysql from k8s cluster
#mysql-svc: minikube
#  kubectl apply -k kustomize/minikube
#  just install-harvest-secret
#  ss -ltpn | grep 3306 || kubectl port-forward service/mysqldb 3306:3306 -n {{ns}} & sleep 1

# Generate test data
md:
  # bash -c "source .venv/bin/activate"
  bash -c "uv run data/make_data.py --spec data/test_data.yml --dest seeds/test_data_good.csv"
  bash -c "uv run data/make_data.py --spec data/test_data.yml --dest seeds/test_data_bad.csv --add-dirt"
  bash -c "uv run data/make_synth.py --nrow 1000000"

# Connect to the local postgres db
psql:
  psql -h localhost -U peoplewa -d peoplewa

# SQLMesh ui for local dev
#dev: mysql-svc
dev:
  uv run sqlmesh ui --port 8080

# Run SQLMesh plan in DEV
pd:
  uv run sqlmesh plan dev 

# Run SQLMesh plan in PROD
pp:
  uv run sqlmesh plan

# Run all SQLMesh audits
audit:
  uv run sqlmesh audit

# # View latest log
log:
  bat --theme='ansi' $(ls -t logs/ | head -n 1 | sed 's/^/logs\//')
