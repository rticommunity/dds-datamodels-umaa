# dds-datamodels-umaa

This repository contains the UMAA datamodel https://www.auvsi.org/unmanned-maritime-autonomy-architecture

## Repo Organization

### Versioning & Branches

This repository stores the different versions of the UMAA datamodel in
different branches. Additionally, it contains `enhanced` versions of the
original datamodel. This enhanced versions modifies the original datamodel
including the latest IDL features and other potential improvements. The
different changes are explained in their own readme file.

The branches in this repo follow this pattern:

 - main: this contains the latest enhanced version
 - version/x.y\[.z\]\[-(version_specifier)\]\[-enhanced\]

For example, `version/2.0-beta-enhanced`

The `version_specifier` is added if a non-final version is being used. This
information appears in the datamodel website.

The `-enhanced` indicates that it contains the enhanced version of the specified
datamodel version.

### Folders

This repository contains one folder called `datamodel` that contains the
representation of this datamodel. Internally, that folder contains the different
files that implement the datamodel. It must contain an `idl` folder that
includes the IDL files of the datamodel. Additionally, other folders with the
name of the technology used for the representation of the datamodel may be
present. For example: `xml`, `json`...

## Changes on the Datamodel

This enhanced version contains several changes in the datamodel for the
UMAA version 6.0.0:

 - Replaced the comments in the IDL files with a custom annotation `@doc("")`.

## Testing

In order to test this datamodel after the applied changes, `rtiddsgen` from
RTI Connext 7.3.0 has been used. A convenient CMake script has been used to
generate code and build a library with all the types included in this datamodel.

In order to generate such library:
```
mkdir build
cd build
cmake ..
cmake --build .
```

This CMake script downloads the
[dds-datamodels-utils](https://github.com/rticommunity/dds-datamodels-utils)
repository. You can also provide a local copy of that repository by setting the
cmake variable `DDS_DATAMODELS_UTILS_DIR`. This variable must point to the
absolute path where the `dds-datamodels-utils` repo is located, for example:

```
cmake .. -DDDS_DATAMODELS_UTILS_DIR=/Users/angel/datamodels/dds-datamodels-utils
```

**NOTE**: you can disable the generation of the library by setting
`DDS_DATAMODELS_BUILD_LIB=OFF`

## Generating XML files

In order to generate XML files from this datamodel, you need to set the CMake
variable `DDS_DATAMODELS_CONVERT_TO_XML`, for example:
```
mkdir build
cd build
cmake .. -DDDS_DATAMODELS_CONVERT_TO_XML=ON
cmake --build .
```
