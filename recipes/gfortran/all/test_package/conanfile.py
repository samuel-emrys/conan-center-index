import os
import shutil
from conan import ConanFile
from conan.tools.build import cross_building
from conan.tools.env import VirtualBuildEnv, VirtualRunEnv

class TestPackageConan(ConanFile):
    settings = "os", "compiler", "build_type", "arch"
    test_type = "explicit"

    @property
    def _input_file(self):
        return os.path.join(self.source_folder, "hello.f90")

    @property
    def _output_file(self):
        return os.path.join(self.build_folder, "hello_f90")

    def build_requirements(self):
        self.tool_requires(self.tested_reference_str)

    def generate(self):
        buildenv = VirtualBuildEnv(self)
        buildenv.generate()

        runenv = VirtualRunEnv(self)
        runenv.generate()

    def build(self):
        self.run("echo PATH: $PATH")
        self.output.info(f"Testing build using gfortran")
        # Confirm compiler is propagated to env
        self.run("echo FC: $FC", env="conanbuild")
        self.run("$FC --version", env="conanbuild")
        self.run("$FC -dumpversion", env="conanbuild")

        # Confirm files can be compiled
        self.run(
            f"$FC {self._input_file} -o {self._output_file}",
            env="conanbuild",
        )
        self.output.info(f"Successfully built {self._output_file}")


    def test(self):
        def chmod_plus_x(name):
            if os.name == "posix":
                os.chmod(name, os.stat(name).st_mode | 0o111)

        self.output.info(f"Testing application built using gfortran")
        if not cross_building(self):
            chmod_plus_x(f"{self._output_file}")

            if self.settings.os == "Linux":
                if shutil.which("readelf"):
                    self.run(f"readelf -l {self._output_file}", env="conanrun")
                else:
                    self.output.info(
                        "readelf is not on the PATH. Skipping readelf test."
                    )

            if self.settings.os == "Macos":
                if shutil.which("otool"):
                    self.run(f"otool -L {self._output_file}", env="conanrun")
                else:
                    self.output.info(
                        "otool is not on the PATH. Skipping otool test."
                    )

            self.run(f"{self._output_file}", env="conanrun")
