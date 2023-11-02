from conan import ConanFile, conan_version
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
        "with_cli_executables": [True, False],
        "with_openmp": [True, False],
    }
    default_options = {
        "shared": False,
        "fPIC": True,
        "with_cli_executables": False,
        "with_openmp": False,
    }

    # def package_id(self):
    #     self.info.clear()

    def layout(self):
        cmake_layout(self, src_folder="src")

    def requirements(self):
        self.requires("armadillo/12.2.0")
        self.requires("ensmallen/2.19.1")
        self.requires("cereal/1.3.2")
        self.requires("stb/cci.20220909")
        # self.requires("pkgconf/2.0.3")
        # if self.settings.os == "Linux":
        #     self.requires("libbfd/2.4.1") # available in binutils??
        #     self.requires("libdl/x.y.z") # not avilable?

    def build_requirements(self):
        self.tool_requires("pkgconf/2.0.3")

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
        deps.set_property("armadillo", "cmake_config_version_compat", "AnyNewerVersion")
        deps.set_property("ensmallen", "cmake_file_name", "Ensmallen")
        deps.set_property("ensmallen", "cmake_target_name", "Ensmallen::Ensmallen")
        deps.set_property("ensmallen", "cmake_config_version_compat", "AnyNewerVersion")
        deps.set_property("cereal", "cmake_config_version_compat", "AnyNewerVersion")
        deps.generate()
        tc = CMakeToolchain(self)
        tc.variables["DEBUG"] = self.settings.build_type == "Debug"
        tc.variables["DOWNLOAD_DEPENDENCIES"] = False
        tc.variables["BUILD_CLI_EXECUTABLES"] = self.options.with_cli_executables
        tc.variables["BUILD_SHARED_LIBS"] = self.options.shared
        tc.generate()


    def build(self):
        replace_in_file(
            self,
            os.path.join(self.source_folder, "CMakeLists.txt"),
            "ARMADILLO_INCLUDE_DIRS",
            "armadillo_INCLUDE_DIRS",
        )
        replace_in_file(
            self,
            os.path.join(self.source_folder, "CMakeLists.txt"),
            "ARMADILLO_LIBRARIES",
            "armadillo_LIBRARIES",
        )
        replace_in_file(
            self,
            os.path.join(self.source_folder, "CMakeLists.txt"),
            "ENSMALLEN_INCLUDE_DIR",
            "Ensmallen_INCLUDE_DIR",
        )
        replace_in_file(
            self,
            os.path.join(self.source_folder, "CMakeLists.txt"),
            "CEREAL_INCLUDE_DIR",
            "cereal_INCLUDE_DIR",
        )
        replace_in_file(
            self,
            os.path.join(self.source_folder, "CMakeLists.txt"),
            "find_package(StbImage)",
            "find_package(stb)",
        )
        replace_in_file(
            self,
            os.path.join(self.source_folder, "CMakeLists.txt"),
            "STB_IMAGE_INCLUDE_DIR",
            "stb_INCLUDE_DIR",
        )
        #replace_in_file(
        #    self,
        #    os.path.join(self.source_folder, "CMakeLists.txt"),
        #    "add_custom_target(pkgconfig ALL",
        #    "message(\"CMAKE_COMMAND: ${CMAKE_COMMAND}\")\n    message(\"CMAKE_SOURCE_DIR: ${CMAKE_SOURCE_DIR}\")\n    message(\"CMAKE_CURRENT_SOURCE_DIR: ${CMAKE_CURRENT_SOURCE_DIR}\")\n    message(\"CMAKE_CURRENT_BINARY_DIR: ${CMAKE_CURRENT_BINARY_DIR}\")\n    message(\"CMAKE_INSTALL_LIBDIR: ${CMAKE_INSTALL_LIBDIR}\")\n    add_custom_target(pkgconfig ALL",
        #)
        # replace_in_file(
        #     self,
        #     os.path.join(self.source_folder, "CMakeLists.txt"),
        #     "install(FILES",
        #     "# install(FILES",
        # )
        # replace_in_file(
        #     self,
        #     os.path.join(self.source_folder, "CMakeLists.txt"),
        #     "DESTINATION \"${CMAKE_INSTALL_LIBDIR}",
        #     "# DESTINATION \"${CMAKE_INSTALL_LIBDIR}",
        # )
        # TODO: Remove this when conan 1.x compatibility is dropped. The need for patching these
        # is removed through the introduction of the AnyNewerVersion compatibilty policy introduced
        # in conan 2.0.12
        if conan_version < Version("2.0.12"):
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
                "find_package(cereal \"${CEREAL_VERSION}\" REQUIRED)",
                "find_package(cereal REQUIRED)",
            )
            replace_in_file(
                self,
                os.path.join(self.source_folder, "CMakeLists.txt"),
                "find_package(Ensmallen \"${ENSMALLEN_VERSION}\" REQUIRED)",
                "find_package(Ensmallen REQUIRED)",
            )

        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def package(self):
        cmake = CMake(self)
        cmake.install()

        copy(self, "LICENSE.txt", dst=os.path.join(self.package_folder, "licenses"), src=self.source_folder)
        rmdir(self, os.path.join(self.package_folder, "lib"))
        rmdir(self, os.path.join(self.package_folder, "share"))

    def package_info(self):
        self.cpp_info.bindirs = []
        self.cpp_info.libdirs = []
