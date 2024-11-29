# dds-datamodels-umaa

This datamodel is an enhanced version of the UMAA 6.0.0 datamodel
that you can find here: https://www.auvsi.org/unmanned-maritime-autonomy-architecture
Nothing herein limits your rights under, or grants you rights that supersede,
the applicable license for this datamodel, and it is your responsibility to
ensure that your use of this software complies with that license.

This software is provided "as is", with no warranty of any type, including any
warranty for fitness for any purpose. RTI is under no obligation to maintain or
support the software. RTI shall not be liable for any incidental or
consequential damages arising out of the use or inability to use the software.
This notice must accompany any distributed copies of the software.

## Repo Organization

### Versioning & Branches

This repository stores the different versions of the UMAA datamodel in
different branches. Additionally, it contains `enhanced` versions of the
original datamodel. This enhanced versions modifies the original datamodel
including the latest IDL features and other potential improvements. The
different changes are explained in their own readme file.

The branches in this repo follow this pattern:

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
 - Added `@unit`, `@range` and `@min` annotation based on the comments that a
   specific member or typedef has related to the units used, the range of valid
   values.
 - Added the default value 3 to the type `typedef long SidesCount` which is
   the minimum valid value.
 - Used `@range2` annotation to `typedef double ElectroMagneticFrequencyHertz`
   since the type is used in a sequence.

### Annotation script

The changes to this datamodel have been done using the `annotation_script.py`
under `resource/annotation_script`.

Usage:
```
python3 annotation_script.py -i ../datamodel/idl/ -o output
```

Additionally, there are two changes done manually:
  - Added default value 3 to `SidesCount`
  - Modification of `range` to `range2` in `ElectroMagneticFrequencyHertz`

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
`DDS_DATAMODELS_BUILD_CXX11_LIB=OFF`

## Generating XML files

In order to generate XML files from this datamodel, you need to set the CMake
variable `DDS_DATAMODELS_CONVERT_TO_XML`, for example:

```
mkdir build
cd build
cmake .. -DDDS_DATAMODELS_CONVERT_TO_XML=ON
cmake --build .
```

## Generating Python files

In order to generate Python files from this datamodel, you need to set the CMake
variable `DDS_DATAMODELS_GENERATE_PYTHON_CODE`, for example:

```
mkdir build
cd build
cmake .. -DDDS_DATAMODELS_GENERATE_PYTHON_CODE=ON
cmake --build .
```

**NOTE**: This is only supported when using Connext 7.3.0+
