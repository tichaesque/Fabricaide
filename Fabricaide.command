#!/bin/bash
cd -- "$(dirname "$BASH_SOURCE")"

rm -f src/fabricaidedoc.svg src/cacheddoc.svg
touch src/fabricaidedoc.svg src/cacheddoc.svg
docker run --rm -d -p 3000:3000 --memory=2g --name fabricaideServer -v $(pwd)/src:/Fabricaide intellipack:1.0
sleep 1
processing-java --sketch=$(pwd)/src/FabricaideUI --run