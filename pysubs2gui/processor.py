#!/usr/bin/env python

import os.path

import pysubs2

# ----------------------------------------------------------------------------------------------------------------------

FORMAT_IDENTIFIER_TO_FILE_EXTENSION = {v: k for k, v in pysubs2.formats.FILE_EXTENSION_TO_FORMAT_IDENTIFIER.items()}


class Processor(object):
    def __init__(self, input_encoding, output_encoding):
        self.steps = []
        self.input_encoding = input_encoding
        self.output_encoding = output_encoding
        self.output_dir = None
        self.output_format = None
        self.output_fps = None

    def add_step(self, f):
        """f(subs: SSAFile) -> None"""
        self.steps.append(f)

    def get_output_path(self, input_path, subs):
        input_dir, tmp = os.path.split(input_path)
        filename, _ = os.path.splitext(tmp)

        output_dir = self.output_dir or input_dir
        output_format = self.output_format or subs.format
        output_ext = FORMAT_IDENTIFIER_TO_FILE_EXTENSION[output_format]

        return os.path.join(output_dir, filename + output_ext)

    def process_path(self, input_path):
        #import time; time.sleep(1) # XXX

        subs = pysubs2.load(input_path, self.input_encoding)

        for f in self.steps:
            f(subs)

        output_path = self.get_output_path(input_path, subs)
        subs.save(output_path,
                  self.output_encoding,
                  self.output_format or subs.format,
                  self.output_fps)

        return output_path
