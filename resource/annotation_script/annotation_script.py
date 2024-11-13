###############################################################################
#  (c) 2024 Copyright, Real-Time Innovations, Inc. (RTI) All rights reserved. #
#                                                                             #
#  RTI grants Licensee a license to use, modify, compile, and create          #
#  derivative works of the software solely for use with RTI Connext DDS.      #
#  Licensee may redistribute copies of the software provided that all such    #
#  copies are subject to this license.                                        #
#  The software is provided "as is", with no warranty of any type, including  #
#  any warranty for fitness for any purpose. RTI is under no obligation to    #
#  maintain or support the software.  RTI shall not be liable for any         #
#  incidental or consequential damages arising out of the use or inability to #
#  use the software.                                                          #
#                                                                             #
###############################################################################

import os
import shutil
import argparse
import re
from enum import Enum

# Sample IDL string for testing
test_idl = """
// This is content before #ifndef and it should be kept as it is
#define MY_CONSTANT 42

#ifndef MY_IDL
#define MY_IDL

//@copy this annotation should be kept as it is


    /**
     * 
     */

    // This is a single line comment for an enum
    enum MyEnum {
        // This is a comment before the enum element
        Element1, // Inline comment for enum element
        // This is before the element
        // and multiline
        Element2, // Mixing the previous comment with inline
        /* comment multiline
        for element 3*/
        Element3 // Comment with no comma at the end
    };

    // This is a comment with chars that
    // need to be escaped "
    // these are not escaped ( ) \\ ,
    module TestModuleName1
    {
        enum AnotherEnum
        {
            Element1, // This is an inline long comment with comma - long comment long comment long comment long comment long comment long comment long comment long comment long comment long comment long comment long comment
            Element2 //This is an inline long comment without comma - long comment long comment long comment long comment long comment long comment long comment long comment long comment long comment long comment long comment
        };
    };

    // this is a multiline comment
    // with more than 1 line
    // Elements here contain max, min, range and unit annotations
    struct testStruct1 {
        // element that includes a range
        double test1; // maxInclusive=500 minInclusive=0 units=meters
        // element that includes only max
        double test2; // maxInclusive=500 units=meters
        // element that includes only min
        double test3; // minInclusive=0 units=meters
        // element that includes unit with more than 1 word before other element in the comment
        double test4; // minInclusive=0 units=square meters otherElement=angel
        // element that includes unit with more than 1 word at the end
        double test3; // minInclusive=0 units=square meters
    };

    // comment for typedef including inline comment
    typedef double test2; // maxInclusive=500 units=meters

    // Inline comments for struct members
    struct testStruct2 {
        // comment for member
        double test1; // this is an inline comment for struct member
        // comment for member
        double test2; //inline comment without space
        // comment for member
        double test3; /*C-style inline comment*/
        // Adding one comment before C-style inline comment
        int32 test3; /* C-style inline comment */
    };

    /*
     * This is a block comment
     * that spans multiple lines.
     */
    struct testStruct3 {
        int32 x;
    };

    /**
     * This is a block comment with
     * 
     * an empty line
     */
    struct testStruct4 {
        // minInclusive=0.0 units=Nephelometric Turbidity Units (NTU) referenceFrame=Environment
        int32 x;
    };

    /* c comment block starting in the same line and
    containing multiline comment */
    struct testStruct5 {
        int32 x;
    }

    /* single line c style */
    struct testStruct5 {
        int32 x;
    }

    //C++ style comment without space
    struct testStruct7 {
        // the max includes a scientific notation
        int32 x; // maxInclusive=1e25 minInclusive=-20000000 units=Meter axisAbbrev=Y axisDirection=port axisUnit=Meter rangeMeaning=exact resolution=0.001
    }

#endif

// This is content after #endif
#define ANOTHER_CONSTANT 100

// This comment only tries to break the #ifndef condition
#define DO_SOMETHING
// This comment should not be added as a @doc annotation

#ifndef MY_IDL
#define MY_IDL

//@copy keep this

    // This repeat some tests to check that comments are generated
    enum MyEnum {
        // This is a comment before the enum element
        Element1, // Inline comment for enum element
        // This is before the element
        // and multiline
        Element2, // Mixing the previous comment with inline
        /* comment multiline
        for element 3*/
        Element3 // Comment with no comma at the end
    };

#endif // test
"""

# This is used to indent multiline comments properly
TAB_STR = '    '
TAB_LEN = len(TAB_STR)

# an easy way of removing the format=markdown parameter
MD_PARAMETER = ''
#MD_PARAMATER = ', "markdown"'
# an easy way of adding/removing @doc(value=
DOC_VALUE = '@doc('
#DOC_VALUE = '@doc(value='

# enum to determine the block the script is processing
class BlockType(Enum):
    SINGLE_LINE_COMMENT = 'single_line_comment'
    INLINE_COMMENT = 'inline_comment'
    BLOCK_COMMENT_START = 'block_comment_start'
    BLOCK_COMMENT_END = 'block_comment_end'
    IFNDEF = 'ifndef'
    ENDIF = 'endif'
    NONE = 'none'

# add a doc annotation to result_lines from comment_buffer
#   - leading_spaces_offset: specific offset to the leading spaces
#     for the doc annotation
#   - fixed_indentation: if negative, no fixed indentation applied, if positive
#     it defines the indentation of the @doc annotation
def add_doc_annotation_from_comment(
        result_lines,
        comment_buffer,
        leading_spaces_offset=0,
        fixed_indentation=-1):
    if comment_buffer:
        comment = ' \\\n'.join(comment_buffer)
        if fixed_indentation < 0:
            leading_spaces = len(comment) - len(comment.lstrip()) + leading_spaces_offset
        else:
            leading_spaces = fixed_indentation
        result_lines.append(leading_spaces * ' '
                            + f'{DOC_VALUE}"{escape_characters(comment.strip())}"{MD_PARAMETER})')
        comment_buffer.clear()

# function to scape characters
def escape_characters(input_string):
    # Characters to escape
    characters_to_escape = ['"']

    # Escape each character by replacing it with a backslash followed by itself
    for char in characters_to_escape:
        input_string = input_string.replace(char, f"\\{char}")

    return input_string

# function to replace single line comments by @doc annotation
def handle_single_line_comment(line, comment_buffer):
    # calculate the leading spaces and indent all lines because we don't know
    # wether `line` is the first line in the comment or not. The indentation
    # should not be present in the first line
    leading_spaces = len(line) - len(line.lstrip())
    comment_spaces_str = (leading_spaces + TAB_LEN) * ' '

    # keep comments that start with //@
    if line.lstrip().startswith("//@"):
        return False

    # C++ style comment
    single_line_comment = re.match(r'^\s*//\s*(.*)', line)
    if single_line_comment:
        # add the content to the output parameter comment_buffer
        comment_buffer.append(comment_spaces_str + single_line_comment.group(1).strip())
        return True

    # C style single line comment
    single_line_comment = re.match(r'^\s*/\*(.+)\*/', line)
    if single_line_comment:
        # add the content to the output parameter comment_buffer
        comment_buffer.append(comment_spaces_str + single_line_comment.group(1).strip())
        return True
    return False

# function to replace inline comments with a doc annotation. These inline
# comments will appear attached to the element in the same line, for example:
#   struct test {
#     int32 x; // this is an inline comment
#   }
# will be replaced by:
#   struct test {
#     @doc("this is an inline comment")
#     int32 x;
#   }
def handle_inline_comment(line, result_lines, comment_buffer):
    # calculate leading spaces to align @doc with the element itself
    leading_spaces = len(line) - len(line.lstrip())
    leading_spaces_str = leading_spaces * ' '

    # regular expression to catch inline comments with // or /* */
    # inline_comment_cpp = re.match(r'^\s*(.+;)\s*//\s*(.*)', line)
    # inline_comment_c = re.match(r'^\s*(.+;)\s*/\*\s*(.*)\s*\*/', line)

    inline_comment_cpp = re.match(r'^\s*(.+[;,]?)\s*//\s*(.*)', line)
    inline_comment_c = re.match(r'^\s*(.+[;,]?)\s*/\*\s*(.*)\s*\*/', line)

    inline_comment_text = None

    # get the element and the inline comment
    if inline_comment_cpp:
        element_name = inline_comment_cpp.group(1)
        inline_comment_text = inline_comment_cpp.group(2).strip()
    elif inline_comment_c:
        element_name = inline_comment_c.group(1)
        inline_comment_text = inline_comment_c.group(2).strip()

    if inline_comment_text is not None:
        # if there is already a comment in comment_buffer, add it to the result
        # lines. This separates in two different @doc annotation if the member
        # has an inline comment and a previous comment
        add_doc_annotation_from_comment(result_lines, comment_buffer)

        # append the inline @doc annotation and the element (after it)
        result_lines.append(leading_spaces_str
                + f'{DOC_VALUE}"{escape_characters(inline_comment_text)}"{MD_PARAMETER})'.strip())
        result_lines.append(leading_spaces_str + f'{element_name}'.strip())
    else:
        result_lines.append(line)

# translate some comments to specific annotations, such as:
#  - min
#  - max
#  - range
#  - unit
def handle_additional_annotations(line):
    """Handles additional annotations such as max, min, range or unit."""
    leading_spaces = len(line) - len(line.lstrip())
    max = None
    min = None
    unit = None
    annotation_line = ''

    # Regular expression patterns
    max_pattern = r'maxInclusive=([-+]?\d*\.?\d+(?:[eE][-+]?\d+)?)'
    min_pattern = r'minInclusive=([-+]?\d*\.?\d+(?:[eE][-+]?\d+)?)'
    # units may be composed of more than one word, so match till the next element
    # in the comment `nextElement=`, or the end of the string if units is the
    # last element
    units_pattern = r'units=([^/]*?)(?=\s*(?="\s*\)|\w+=|$))'

    # Search for maxInclusive in the input string
    max_match = re.search(max_pattern, line)
    if max_match:
        max = max_match.group(1)

    # Search for minInclusive in the input string
    min_match = re.search(min_pattern, line)
    if min_match:
        min = min_match.group(1)

    # Search for units in the input string
    units_match = re.search(units_pattern, line)
    if units_match:
        unit = units_match.group(1).strip()  # Remove any leading/trailing whitespace

    # if there is max and min, that is translate to @range
    if max and min:
        annotation_line += f'@range(min={min}, max={max})'
    elif max:
        annotation_line += f'@max({max})'
    elif min:
        annotation_line += f'@min({min})'

    # write @unit annotation if it is specified. If units is `N/A` or `None`, do
    # no add anything
    if unit and unit != 'N/A' and unit != "None":
        annotation_line += ' ' if annotation_line else ''
        annotation_line += f'@unit("{unit}")'

    # add a new line with the corresponding annotations
    if annotation_line:
        annotation_line = leading_spaces * ' ' + annotation_line

    return annotation_line

# start of the block comment /* */
def handle_block_comment_start(line, comment_buffer, leading_spaces):
    """Handles the start of block comments."""
    # get the leading spaces and modify `leading_spaces` accordingly
    leading_spaces.append(len(line) - len(line.lstrip()))
    if re.match(r'^\s*/\*', line):
        # remove opening /*
        line = re.sub(r'/\*+\s*', '', line)
        # if there is a comment in the first line where the /* starts, add it to
        # the comment_buffer
        if line.strip() != '':
            comment_buffer.append((leading_spaces[0] * ' ') + line)

# documentation inside the block comment /* */
def handle_block_comment(line, comment_buffer):
    # find starts at the beginning of the line and remove them
    if re.match(r'^\s*\*+\s*', line):
        line = re.sub(r'\*+\s*', '', line)

    # copy the rest of the comment to comment_buffer if it is not empty
    if line.strip() != '':
        comment_buffer.append(TAB_STR + line)

# handles the end of a block comment
def handle_block_comment_end(
        line,
        comment_buffer,
        result_lines,
        leading_spaces,
        add_empty_comments=False):
    """Handles the end of block comments."""
    # find the end of a block comment `*/`
    if re.match(r'.*\*/', line):
        # remove it from the text of the annotation
        line = re.sub(r'\s*\*/', '', line)
        # if the rest of the line is not empty, add it
        if line.strip() != '':
            comment_buffer.append(TAB_STR + line)

        # as this is the end of the comment block, add it to the result_lines
        if len(comment_buffer) == 0 and add_empty_comments:
            comment_buffer.append('')
        add_doc_annotation_from_comment(
            result_lines,
            comment_buffer,
            fixed_indentation=leading_spaces[0])

# determine the block type we are processing
def determine_block_type(line, inside_multiline_comment):
    # check if the line starts with #ifndef
    if re.match(r'^\s*#ifndef', line):
        return BlockType.IFNDEF

    # check if the line starts with #endif
    if re.match(r'^\s*#endif', line):
        return BlockType.ENDIF

    # single line comment in C or Cpp style
    if re.match(r'^\s*//\s*', line) or re.match(r'^\s*/\*.+\*/', line):
        return BlockType.SINGLE_LINE_COMMENT

    # inline comment in C or Cpp Style
    if re.match( r'^\s*.+[;,]?\s*//\s*(.*)\s*', line) or \
        re.match(r'^\s*.+[;,]?\s*/\*\s*(.*)\s*\*/', line):
        return BlockType.INLINE_COMMENT

    # starting a C comment block
    if re.match(r'^\s*/\*', line):
        return BlockType.BLOCK_COMMENT_START

    # If we are already processing a multiline C comment, check for the end
    # of that comment block
    if inside_multiline_comment:
        if re.match(r'.*\*/', line):
            return BlockType.BLOCK_COMMENT_END

    # different line, no action required
    return BlockType.NONE

def parse_idl_string_to_doc(idl_string, debug=False):
    """Parse idl files to translate comments to @doc annotations."""
    lines = idl_string.splitlines()
    result_lines = []
    modified_lines = []
    inside_ifndef = False
    inside_multiline_comment = False
    comment_buffer = []
    previous_block_type = None
    multiline_comment_leading_spaces = []

    for line in lines:
        line = line.rstrip()  # Remove trailing whitespace

        block_type = determine_block_type(line, inside_multiline_comment)

        # only write data if processing content inside an ifndef
        if block_type == BlockType.IFNDEF:
            result_lines.append(line) # Preserve content
            inside_ifndef = True
            continue

        if block_type == BlockType.ENDIF and inside_ifndef:
            result_lines.append(line) # Preserve content
            inside_ifndef = False
            continue

        # Preserve content not in #ifndef
        if not inside_ifndef:
            result_lines.append(line) # Preserve content
            continue

        # Process current line based on block type
        if block_type == BlockType.SINGLE_LINE_COMMENT:
            if handle_single_line_comment(line, comment_buffer):
                previous_block_type = block_type
                continue
            else:
                previous_block_type = block_type
        elif previous_block_type == BlockType.SINGLE_LINE_COMMENT:
            # As we don't know when a single line comment ends (whether it has
            # one or multiple lines). Then, only after not having any other
            # single line comment, copy the comment_buffer as a @doc annotation.

            # TAB_LEN was already added previously to all lines, but there
            # is no need to indent the first line of a multiline comment
            add_doc_annotation_from_comment(result_lines, comment_buffer, -TAB_LEN)

        if block_type == BlockType.INLINE_COMMENT:
            handle_inline_comment(line, result_lines, comment_buffer)
            previous_block_type = block_type
            continue

        if block_type == BlockType.BLOCK_COMMENT_START:
            handle_block_comment_start(line, comment_buffer, multiline_comment_leading_spaces)
            inside_multiline_comment = True
            previous_block_type = block_type
            continue

        if inside_multiline_comment:
            if block_type == BlockType.BLOCK_COMMENT_END:
                handle_block_comment_end(
                        line,
                        comment_buffer,
                        result_lines,
                        multiline_comment_leading_spaces,
                        add_empty_comments=True)
                inside_multiline_comment = False
                multiline_comment_leading_spaces.clear()
                previous_block_type = block_type
                continue
            # content of the comment block
            handle_block_comment(line, comment_buffer)
            previous_block_type = block_type
            continue

        # If no comments are found, check if we have collected any comments
        add_doc_annotation_from_comment(result_lines, comment_buffer)

        # Append non-comment lines (like members, other annotations, etc.)
        result_lines.append(line)
        previous_block_type = BlockType.NONE  # Reset to unknown for non-comment lines

    # post-process the files to retrieve additional annotations
    for line in result_lines:
        modified_lines.append(line)
        extra_annotation = handle_additional_annotations(line)
        if extra_annotation != '':
            modified_lines.append(extra_annotation)

    # return the file with the annotations applied
    transformed_file = '\n'.join(modified_lines)
    if debug:
        print(transformed_file)
    return transformed_file

def process_files(input_folder, output_folder):
    """Processes .idl files in input folder, applies transformations, and saves them in output folder."""
    # process all files
    for root, dirs, files in os.walk(input_folder):
        for file_name in files:
            input_file = os.path.join(root, file_name)
            # relative path of the file from input_folder
            relative_path = os.path.relpath(root, input_folder)
            # create output directory
            output_dir = os.path.join(output_folder, relative_path)
            os.makedirs(output_dir, exist_ok=True)
            output_file = os.path.join(output_dir, file_name)

            # process only idl files
            if file_name.endswith('.idl'):
                with open(input_file, 'r') as file:
                    idl_content = file.read()

                print(f"Processing {input_file}...")

                with open(output_file, 'w') as file:
                    result_lines = parse_idl_string_to_doc(idl_content)
                    file.write(result_lines + '\n')
            else:
                # if not idl file, then just copy it
                print(f"Copying {input_file}...")
                shutil.copy(input_file, output_file)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Parse IDL files to generate @doc annotations.")
    parser.add_argument("-i", "--input", help="Path to the input folder containing .idl files.")
    parser.add_argument("-o", "--output", help="Path to the output folder where the results will be saved.")
    parser.add_argument("--test", action="store_true", help="Run the test mode with a sample IDL string.")

    args = parser.parse_args()

    if args.test:
        # Run the test with the predefined test_idl string
        print("Running in test mode...\n")
        parse_idl_string_to_doc(test_idl, debug=True)
    elif args.input and args.output:
        # Process actual files from input and output folders
        process_files(args.input, args.output)
    else:
        print("Please provide both input and output directories, or use the --test option.")
