from conan import ConanFile
from conan.tools.cmake import CMakeToolchain, CMake, cmake_layout, CMakeDeps
from conan.tools.files import get, replace_in_file, rmdir, copy
from conan.tools.scm import Version

import os

required_conan_version = ">=1.55.0"

class mlpackRecipe(ConanFile):
    name = "mlpack"
    description = "mlpack is an intuitive, fast, and flexible header-only C++ machine learning library with bindings to other languages."
    license = "BSD-3-Clause"
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://github.com/mlpack/mlpack"
    topics = ("machine", "learning", "header-only")

    package_type = "header-library"
    settings = "os", "compiler", "build_type", "arch"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
        "with_python_bindings": [True, False],
        "with_julia_bindings": [True, False],
        "with_go_bindings": [True, False],
        "with_r_bindings": [True, False],
        "with_openmp": [True, False],
    }
    default_options = {
        "shared": False,
        "fPIC": True,
        "with_python_bindings": False,
        "with_julia_bindings": False,
        "with_go_bindings": False,
        "with_r_bindings": False,
        "with_openmp": False,
    }

    def package_id(self):
        self.info.clear()

    def layout(self):
        cmake_layout(self, src_folder="src")

    def requirements(self):
        self.requires("armadillo/12.2.0")
        self.requires("ensmallen/2.19.1")
        self.requires("cereal/1.3.2")
        self.requires("stb/cci.20220909")
        # if self.settings.os == "Linux":
        #     self.requires("libbfd/2.4.1") # available in binutils??
        #     self.requires("libdl/x.y.z") # not avilable?

    #@property
    #def _minimum_compiler_version(self):
    #    return {
    #        "gcc": "5",
    #        "clang": "3.5",
    #    }

    #def validate(self):
    #    if Version(self.settings.compiler.version) <= self._minimum_compiler_version[self.settings.compiler]:
    #        raise ConanInvalidConfiguration(f"{self.settings.compiler} version {self.settings.compiler.version} is too old! {self._minimum_compiler_version[self.settings.compiler]} or newer is required.")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

    def generate(self):
        deps = CMakeDeps(self)
        deps.set_property("armadillo", "cmake_file_name", "Armadillo")
        deps.set_property("armadillo", "cmake_target_name", "Armadillo::Armadillo")
        deps.generate()
        tc = CMakeToolchain(self)
        tc.variables["DEBUG"] = self.settings.build_type == "Debug"
        tc.variables["DOWNLOAD_DEPENDENCIES"] = False
        tc.generate()


    def build(self):
        # Remove hard requirement on armadillo 9.800.0
        # This is a minimum requirement, use latest
        replace_in_file(
            self,
            os.path.join(self.source_folder, "CMakeLists.txt"),
            "find_package(Armadillo \"${ARMADILLO_VERSION}\" REQUIRED)",
            "find_package(Armadillo REQUIRED)",
        )
        replace_in_file(
            self,
            os.path.join(self.source_folder, "CMakeLists.txt"),
            "find_package(Ensmallen \"${ENSMALLEN_VERSION}\" REQUIRED)",
            "find_package(Ensmallen REQUIRED)",
        )
        replace_in_file(
            self,
            os.path.join(self.source_folder, "CMakeLists.txt"),
            "find_package(cereal \"${CEREAL_VERSION}\" REQUIRED)",
            "find_package(cereal REQUIRED)",
        )
        replace_in_file(
            self,
            os.path.join(self.source_folder, "CMakeLists.txt"),
            "find_package(StbImage)",
            "find_package(stb)",
        )
        cmake = CMake(self)
        cmake.configure()

    def package(self):
        cmake = CMake(self)
        cmake.install()

        copy(self, "LICENSE.txt", dst=os.path.join(self.package_folder, "licenses"), src=self.source_folder)
        rmdir(self, os.path.join(self.package_folder, "lib"))
        rmdir(self, os.path.join(self.package_folder, "share"))

    def package_info(self):
        self.cpp_info.bindirs = []
        self.cpp_info.libdirs = []
        self.cpp_info.set_property("cmake_file_name", "Ensmallen")
        self.cpp_info.set_property("cmake_target_name", "Ensmallen::Ensmallen")
