#!/usr/bin/env python
# -*- coding: utf-8 -*-

# SPDX-FileCopyrightText: 2019-2021 Alliander N.V.
#
# SPDX-License-Identifier: MPL-2.0

import json
from pathlib import Path

import rpy2
import rpy2.robjects.packages as rpackages
from rpy2.robjects import numpy2ri, pandas2ri, default_converter
from rpy2.robjects.conversion import localconverter
from rpy2.robjects.packages import STAP
from rpy2.robjects.vectors import StrVector


class RSession(object):
    """Creates a new R session using rpy2.

    Note:
        The working directory of the R instance is equal to that of Python.
    """

    def __init__(self):
        self.r = rpy2.robjects.r

    def install_r_packages(self, *packages: str):
        """Install a list of R packages

        Args:
            *packages (str): package names available on CRAN

        Example usage:
            session.install_r_packages('ggplot2', 'dplyr', 'cluster')
        """
        utils = rpackages.importr("utils")
        utils.chooseCRANmirror(ind=1)
        utils.install_packages(StrVector(packages))

    def import_r_packages(self, *packages: str):
        """Import R packages using the *library* function

        Args:
            *packages (str):
        """
        for package in packages:
            self.r["library"](package)

    def source_r_scripts(self, *script_paths):
        """Source R scripts using the *source* function

        Args:
            *script_paths (pathlike): paths of R scripts
        """
        for script_path in script_paths:
            self.r["source"](script_path)

    def call_function(
        self,
        func_name,
        *args,
        enable_output_conversion=True,
        convert_scalars=True,
        **kwargs,
    ):
        """Call a function in the running R session

        Args:
            func_name (str): function name
            *args: function arguments
            enable_output_conversion (bool): convert responses to Python objects
            convert_scalars (bool): convert lists containing a single scalar to a single value
            **kwargs: named function arguments

        Raises:
            LookupError - attribute did not exist

        Returns:
            function result
        """
        with self.input_converter():
            try:
                r_func = self.r[func_name]
                res = r_func(*args, **kwargs)
                if enable_output_conversion:
                    res = self.convert_r_response_to_python(res, convert_scalars)
                return res
            except LookupError:
                raise AttributeError(
                    f'R function "{func_name}" could not be found in R session'
                )

    def get_attribute(
        self, attr_name, enable_output_conversion=True, convert_scalars=True
    ):
        """Retrieve an attribute from the running R session

        Args:
            attr_name (str): name of the attribute
            enable_output_conversion (bool): convert responses to Python objects
            convert_scalars (bool): convert lists containing a single scalar to a single value

        Raises:
            LookupError - attribute did not exist

        Returns:
            requested attribute
        """
        try:
            res = self.r[attr_name]
            if enable_output_conversion:
                res = self.convert_r_response_to_python(res, convert_scalars)
            return res
        except LookupError:
            raise AttributeError(
                f'R attribute "{attr_name}" could not be found in R session'
            )

    def run_r_script_string(
        self, script_string, enable_output_conversion=True, convert_scalars=True
    ):
        """Run an R script string

        This functionality is similar to the *exec* function many programming languages support.
        The input is a string containing one or multiple expressions that need to be ran in the R session.

        Args:
            script_string (str): R code which has to run
            enable_output_conversion (bool): convert responses to Python objects
            convert_scalars (bool): convert lists containing a single scalar to a single value

        Returns:
            result of the last expression in the script string
        """
        res = self.r(script_string)
        if enable_output_conversion:
            res = self.convert_r_response_to_python(res, convert_scalars)
        return res

    @staticmethod
    def convert_r_response_to_python(
        response, convert_scalars=True, to_list=False, native_to_json=False
    ):
        """Converts rpy2 types to Python objects.

        The output is either a Python built-in, NumPy or Pandas object.

        Note:
            Rpy2 returns scalars as vectors. These are converted back to scalars with this conversion, which
            may not be desirable. This behavior can be switched of.

        Args:
            response (rpy2 type): object from the R session to be converted
            convert_scalars (bool): convert vectors with length 1 to scalars

        Returns:
            Converted object
        """
        original_response_type = type(response)

        new_res = response
        if issubclass(original_response_type, rpy2.robjects.vectors.Array):
            new_res = numpy2ri.ri2py(response)
        elif issubclass(original_response_type, rpy2.robjects.vectors.DataFrame):
            new_res = pandas2ri.ri2py(response)
            if native_to_json:
                json_res = new_res.to_json(orient="records")
                json_res = json_res.replace("-2147483648", "null")
                new_res = json.loads(json_res)
        elif issubclass(original_response_type, rpy2.robjects.vectors.Vector):
            if convert_scalars and len(response) == 1:
                new_res = response[0]
            elif to_list:
                new_res = list(response)

        return new_res

    @staticmethod
    def input_converter():
        """Input converter context from Python objects to RPY2 objects."""
        return localconverter(
            default_converter + pandas2ri.converter + numpy2ri.converter
        )


def run_single_r_script_function(
    script_path,
    function_name,
    *args,
    enable_output_conversion=True,
    convert_scalars=True,
    **kwargs,
):
    """Run an R script function in a temporary session

    The specified function from the supplied R script is called and the result is returned.
    The R session isn't persisted.

    Args:
        script_path (pathlike): path to R script
        function_name (str): function names
        *args: function arguments
        enable_output_conversion (bool): convert responses to Python objects
        convert_scalars (bool): convert lists containing a single scalar to a single value
        **kwargs: function keyword arguments

    Returns:
        function result
    """
    # Make sure we are handing a pathlib.Path
    script_path = Path(script_path)

    # Derive a temporary package name from the script_path (= filename without extension)
    package_name = script_path.stem

    # Read the script source
    with open(script_path, "r") as f:
        source_string = f.read()

    with RSession.input_converter():
        package = STAP(source_string, package_name)
        f = getattr(package, function_name)
        res = f(*args, **kwargs)

        if enable_output_conversion:
            res = RSession.convert_r_response_to_python(res, convert_scalars)

    return res


if __name__ == "__main__":
    sess = RSession()
    print(sess.run_r_script_string("matrix(rexp(200), 10)"))
