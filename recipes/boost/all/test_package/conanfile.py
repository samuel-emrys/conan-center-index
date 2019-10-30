from conans.model.conan_file import ConanFile, tools
from conans import CMake
import os
import sys


class DefaultNameConan(ConanFile):
    settings = "os", "compiler", "arch", "build_type"
    generators = "cmake"

    def build(self):
        cmake = CMake(self)
        if self.options["boost"].header_only:
            cmake.definitions["HEADER_ONLY"] = "TRUE"
        else:
            cmake.definitions["Boost_USE_STATIC_LIBS"] = not self.options["boost"].shared
        if self.options["boost"].python:
            cmake.definitions["WITH_PYTHON"] = "TRUE"

        cmake.configure()
        cmake.build()

    def test(self):
        if tools.cross_building(self.settings):
            return
        bt = self.settings.build_type
        self.run('ctest --output-on-error -C %s' % bt, run_environment=True)
        if self.options["boost"].python:
            os.chdir("bin")
            sys.path.append(".")
            import hello_ext
            hello_ext.greet()
