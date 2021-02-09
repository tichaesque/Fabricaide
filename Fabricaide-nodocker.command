#!/bin/bash
cd -- "$(dirname "$BASH_SOURCE")"

rm -f src/fabricaidedoc.svg src/cacheddoc.svg
touch src/fabricaidedoc.svg src/cacheddoc.svg
cd src
python3 fabricade_service.py --port 3000 &
sleep 1
processing-java --sketch=$(pwd)/FabricaideUI --run