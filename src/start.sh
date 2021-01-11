FILE=$(pwd)/FabricaideUI/data/packed
if test -d "$FILE"; then
    echo "$FILE exists"
else
	echo "$FILE does not exist"
	mkdir -p $(pwd)/FabricaideUI/data/packed
	python3.7 $(pwd)/initmatdb.py MatDB.svg
	mkdir -p $(pwd)/cuts
	mkdir -p $(pwd)/placeholder
fi
flask run --host 0.0.0.0 --port 3000