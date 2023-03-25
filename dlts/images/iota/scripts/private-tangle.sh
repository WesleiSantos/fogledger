#!/bin/bash

# Script to run a new Private Tangle
# private-tangle.sh install .- Installs a new Private Tangle
# private-tangle.sh start   .- Starts a new Private Tangle
# private-tangle.sh stop    .- Stops the Tangle

set -e

chmod +x ./utils.sh
source ./utils.sh

help () {
  echo "Installs Private Tangle based on Hornet"
  echo "usage: private-tangle.sh [install]"
}

if [ $#  -lt 1 ]; then 
  echo "Illegal number of parameters"
  help
  exit 1
fi

command="$1"

ip_address=$(echo $(dig +short myip.opendns.com @resolver1.opendns.com))
COO_BOOTSTRAP_WAIT=10

if [ -n "$2" ]; then
  COO_BOOTSTRAP_WAIT="$2"
fi

clean () {
  # We need sudo here as the files are going to be owned by the hornet user
  if [ -f ./db/private-tangle/coordinator.state ]; then
    sudo rm ./db/private-tangle/coordinator.state
  fi

  if [ -d ./db/private-tangle ]; then
    cd ./db/private-tangle
    removeSubfolderContent "coo.db" "node1.db" "spammer.db" "node-autopeering.db"
    cd ../..
  fi

  if [ -d ./p2pstore ]; then
    cd ./p2pstore
    removeSubfolderContent coo node1 spammer "node-autopeering"
    cd ..
  fi

  if [ -d ./snapshots/private-tangle ]; then
    sudo rm -Rf ./snapshots/private-tangle/*
  fi

  # We need to do this so that initially the permissions are user's permissions
  resetPeeringFile config/peering-node.json
  resetPeeringFile config/peering-spammer.json
}

# Sets up the necessary directories if they do not exist yet
volumeSetup () {
  ## Directories for the Tangle DB files
  cd ../../../iota
  if ! [ -d ./db ]; then
    mkdir ./db
  fi

  if ! [ -d ./db/private-tangle ]; then
    mkdir ./db/private-tangle
  fi

  cd ./db/private-tangle
  createSubfolders coo.db spammer.db node1.db node-autopeering.db
  cd ../..

  # Snapshots
  if ! [ -d ./snapshots ]; then
    mkdir ./snapshots
  fi

  if ! [ -d ./snapshots/private-tangle ]; then
    mkdir ./snapshots/private-tangle
  fi

  # P2P
  if ! [ -d ./p2pstore ]; then
    mkdir ./p2pstore
  fi

  cd ./p2pstore
  createSubfolders coo spammer node1 node-autopeering
  cd ..

  ## Change permissions so that the Tangle data can be written (hornet user)
  ## TODO: Check why on MacOS this cause permission problems
  if ! [[ "$OSTYPE" == "darwin"* ]]; then
    echo "Setting permissions for Hornet..."
    sudo chown -R 65532:65532 db 
    sudo chown -R 65532:65532 snapshots 
    sudo chown -R 65532:65532 p2pstore
  fi 
}

### 
### Generates the initial snapshot
### 
generateSnapshot () {
  echo "Generating an initial snapshot..."

  # First a key pair is generated
  docker run -t -i --rm iotaledger/hornet tool ed25519-key > key-pair.txt
  
  # Extract the public key use to generate the address
  local public_key="$(getPublicKey key-pair.txt)"

  # Generate the address
  cat key-pair.txt | awk -F : '{if ($1 ~ /ed25519 address/) print $2}' \
  | sed "s/ \+//g" | tr -d "\n" | tr -d "\r" > address.txt

  # Generate the snapshot
  cd snapshots/private-tangle
  docker run --rm -v "$PWD:/output_dir" -w /output_dir iotaledger/hornet tool snap-gen \
   --networkID "private-tangle" --mintAddress "$(cat ../../address.txt)" \
   --treasuryAllocation 1000000000 --outputPath /output_dir/full_snapshot.bin

  echo "Initial Ed25519 Address generated. You can find the keys at key-pair.txt and the address at address.txt"

  cd .. && cd ..
}

updateContainers () {
  docker pull iotaledger/hornet
}


installTangle () {
  # First of all volumes have to be set up
  volumeSetup

  clean

  # When we install we ensure container images are updated
  updateContainers

  # Initial snapshot
  generateSnapshot
}

case "${command}" in
	"help")
    help
    ;;
	"install")
    installTangle
    ;;
  "stop")
		stopContainers
		;;
  *)
		echo "Command not Found."
		help
		exit 127;
		;;
esac
