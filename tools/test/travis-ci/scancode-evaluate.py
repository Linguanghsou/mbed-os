"""
SPDX-License-Identifier: Apache-2.0

Copyright (c) 2020 Arm Limited. All rights reserved.

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations 
"""

import argparse
import json
import logging
import os.path
import re
import sys
from enum import Enum

MISSING_LICENSE_TEXT = "Missing license header"
MISSING_PERMISSIVE_LICENSE_TEXT = "Non-permissive license"
MISSING_SPDX_TEXT = "Missing SPDX license identifier"

userlog = logging.getLogger("scancode-evaluate")

class ReturnCode(Enum):
    """Return codes."""

    SUCCESS = 0
    ERROR = -1


def init_logger():
    """Initialise the logger."""
    userlog.setLevel(logging.INFO)
    userlog.addHandler(
        logging.FileHandler(
            os.path.join(os.getcwd(), 'scancode-evaluate.log'), mode='w'
        )
    )


def path_leaf(path):
    """Return the leaf of a path."""
    head, tail = os.path.split(path)
    # Ensure the correct file name is returned if the file ends with a slash
    return tail or os.path.basename(head)


def has_permissive_text_in_scancode_output(scancode_output_data_file_licenses):
    """Returns true if at list one license in the scancode output is permissive."""
    return any(
        scancode_output_data_file_license['category'] == 'Permissive'
        for scancode_output_data_file_license in scancode_output_data_file_licenses
    )


def has_spdx_text_in_scancode_output(scancode_output_data_file_licenses):
    """Returns true if at least one license in the scancode output has the spdx identifier."""
    return any(
        'spdx' in scancode_output_data_file_license['matched_rule']['identifier']
        for scancode_output_data_file_license in scancode_output_data_file_licenses
    )


def has_spdx_text_in_analysed_file(scanned_file_content):
    """Returns true if the file analysed by ScanCode contains SPDX identifier."""
    return bool(re.findall("SPDX-License-Identifier:?", scanned_file_content))


def license_check(scancode_output_path):
    """Check licenses in the scancode json file for specified directory.

    This function does not verify if file exists, should be done prior the call.

    Args:
    scancode_output_path: path to the scancode json output file (output from scancode --license --json-pp)

    Returns:
    0 if nothing found
    >0 - count how many license isses found
    ReturnCode.ERROR.value if any error in file licenses found
    """

    offenders = []
    try:
        with open(scancode_output_path, 'r') as read_file:
            scancode_output_data = json.load(read_file)
    except json.JSONDecodeError as jex:
        userlog.warning("JSON could not be decoded, Invalid JSON in body: %s", jex)
        return ReturnCode.ERROR.value

    if 'files' not in scancode_output_data:
        userlog.warning("Missing `files` attribute in %s" % (scancode_output_path))
        return ReturnCode.ERROR.value

    for scancode_output_data_file in scancode_output_data['files']:
        if scancode_output_data_file['type'] != 'file':
            continue

        if not scancode_output_data_file['licenses']:
            scancode_output_data_file['fail_reason'] = MISSING_LICENSE_TEXT
            offenders.append(scancode_output_data_file)
            # check the next file in the scancode output
            continue

        if not has_permissive_text_in_scancode_output(scancode_output_data_file['licenses']):
            scancode_output_data_file['fail_reason'] = MISSING_PERMISSIVE_LICENSE_TEXT
            offenders.append(scancode_output_data_file)

        if not has_spdx_text_in_scancode_output(scancode_output_data_file['licenses']):
            # Scancode does not recognize license notice in Python file headers.
            # Issue: https://github.com/nexB/scancode-toolkit/issues/1913
            # Therefore check if the file tested by ScanCode actually has a licence notice.
            file_path = os.path.abspath(scancode_output_data_file['path'])
            try:
                with open(file_path, 'r') as read_file:
                    scanned_file_content = read_file.read()
            except UnicodeDecodeError:
                userlog.warning("Unable to look for SPDX text in `{}`:".format(file_path))
                # Ignore files that cannot be decoded
                # check the next file in the scancode output
                continue

            if not has_spdx_text_in_analysed_file(scanned_file_content):
                scancode_output_data_file['fail_reason'] = MISSING_SPDX_TEXT
                offenders.append(scancode_output_data_file)

    if offenders:
        userlog.warning("Found files with missing license details, please review and fix")
        for offender in offenders:
            userlog.warning("File: %s reason: %s" % (path_leaf(offender['path']), offender['fail_reason']))
    return len(offenders)


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="License check.")
    parser.add_argument(
        'scancode_output_path',
        help="scancode-toolkit output json file"
    )
    return parser.parse_args()


if __name__ == "__main__":
    init_logger()
    args = parse_args()
    if os.path.isfile(args.scancode_output_path):
        sys.exit(
            ReturnCode.SUCCESS.value
            if license_check(args.scancode_output_path) == 0
            else ReturnCode.ERROR.value
        )
    else:
        userlog.warning("Could not find the scancode json file")
        sys.exit(ReturnCode.ERROR.value)
