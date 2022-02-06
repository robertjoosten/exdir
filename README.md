# Experimental Directory Structure
The hierarchical format based on open standards. It is inspired by already 
existing formats, such as [ExDir](https://github.com/CINPLA/exdir) and HDF5. 
What sets this implementation of ExDir apart is that all the data is stored
in memory and only saved to disk when the file is committed.

## Install
The package can be installed by running the install command on the setup.py
in the root of the package, the example below also shows how to run the test
suite to make sure everything is working as expected.
```
python setup.py install
python -m unittest discover tests -v
```

## Usage
The directory structure and data are stored in memory when requiring the
directories and adjusting their internal data, the examples below show how 
to directly interact with the data structure objects and commit its data to 
disk.

```python
import exdir

# initialize object, create a group and add data
file_object = exdir.File("example.rdf")
dir_object = file_object.require_group("group")
dir_object.attr["side"] = "l"
dir_object.attr["name"] = "leg"
dir_object.meta["user"] = "rjoosten"
dir_object.data_set["weights"] = [0] * 1000000

# retrieve weights
dir_object = file_object["group"]
weights = dir_object.data_set["weights"]
print(weights)

# commit changes
print(file_object.has_unsaved_changes())
file_object.commit()
```

### Structure
A Directory including the initialized File allow for access to meta data,
attributes and data sets. The directories are only created when its files
require their data committed to disk. When working with data sets the meta
data is stored in the .data_sets file and the heavy data in individual files
like in the hierarchy below.

```
example.rdf (File, directory)
│   .attributes (Attribute, file)
│
├── group (Directory, directory)
│   ├── .meta (Attribute, file)
│   ├── .attributes (Attribute, file)
│   ├── .data_sets (DataSet, file)
│   └── weights (Serializer, file)
```

### Memory
Any data read from disk is cached. This will allow access to the data to
be instantaneous once read the first time. Caching can be controlled by the
user as heavy data sets might want to be wiped to clear it from memory after
usage.
