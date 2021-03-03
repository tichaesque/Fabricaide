:: Assumes that processing-java is on the system path
:: Assumes that Packaide and other Python dependencies have
:: been installed on WSL

:: Create data directories
IF NOT EXIST "src/cuts" md "src/cuts"
IF NOT EXIST "src/FabricaideUI/data/packed" md "src/FabricaideUI/data/packed"

:: Reset temporary document files to blank
TYPE NUL > "src/fabricaidedoc.svg"
TYPE NUL > "src/cacheddoc.svg"

:: Warm up WSL so that it doesn't take too long to start
:: up, which might cause Fabricaide to crash
wsl pwd

:: Start the Fabricaide server in another window
:: Use PING to sleep while we wait for the server
:: to start up
CD src
START wsl python3 fabricade_service.py --port 3000
PING 127.0.0.1 -n 3 > nul

:: Start the Fabricaide UI in Processing
processing-java --sketch=%cd%/FabricaideUI --run
