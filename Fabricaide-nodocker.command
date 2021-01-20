#!/bin/bash
cd -- "$(dirname "$BASH_SOURCE")"

rm -f src/easycutdoc.svg src/cacheddoc.svg
touch src/easycutdoc.svg src/cacheddoc.svg
cd src
python3 fabricade_service.py --port 3000 &
sleep 1
processing-java --sketch=$(pwd)/EasyCutIllustratorUI --run