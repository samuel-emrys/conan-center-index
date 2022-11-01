from conan import ConanFile
from conan.tools.gnu import Autotools, AutotoolsToolchain, AutotoolsDeps
from conan.errors import ConanInvalidConfiguration
from conan.tools.layout import basic_layout
from conan.tools.apple import XCRun
from conan.tools.files import copy, get, replace_in_file, rmdir, rm, collect_libs
from conan.tools.build import cross_building
from conan.tools.env import Environment
import os

#required_conan_version = ">=1.53.0"


class GccConan(ConanFile):
    name = "glibc"
    description = (
        "The GNU C Library provides many of the low-level components used"
        "directly by programs written in the C or C++ languages"
    )
    topics = ("gnu", "libc", "c", "c++")
    homepage = "https://www.gnu.org/software/libc"
    url = "https://github.com/conan-io/conan-center-index"
    license = "GPL-2.0-only (src), LGPL-2.1-only (lib)"
    settings = "os", "compiler", "arch", "build_type"

    def build_requirements(self):
        # Extracted from glibc INSTALL. Commented tool_requires are not available on c3i.
        # NOTE: The system variants of these will be present on most systems, but it would be
        # good to have the entire dependency tree on c3i
        self.tool_requires("make/4.3") # Required for build
        # self.tool_requires("gcc/12.2.0") # Required for build
        self.tool_requires("binutils/2.38") # Required for build
        # self.tool_requires("texinfo/4.7") # Required to translate and install documentation
        # self.tool_requires("gawk/3.1.2") # Required to generate files - gawk extensions are used
        self.tool_requires("bison/3.8.2") # Used to generate the yacc parser code in intl subdir
        # self.tool_requires("perl/5.34.1") # Used to build GNU C Library manual. Optional
        # self.tool_requires("sed/3.02") # Required to generate files
        # self.tool_requires("cpython/3.10.0") # Required for build
        # self.tool_requires("pexpect/4.0") # Required to capture GDB output
        # self.tool_requires("gdb/7.8") # Required for pretty printer tests. Needs python support
        self.tool_requires("autoconf/2.69") # This exact version. Required if configure.ac modified
        self.tool_requires("gettext/0.21") # Required if any message translation files are modified

    def requirements(self):
        # May need to be modified to execute target `make headers_install`
        self.requires("linux-headers-generic/5.14.9")

    def validate(self):
        if self.info.settings.os == "Windows":
            raise ConanInvalidConfiguration(
                "Windows builds aren't currently supported - please contribute if you'd to improve this recipe"
            )

    def layout(self):
        basic_layout(self, src_folder="source")

    def generate(self):
        env = Environment()
        env.define("DESTDIR", self.package_folder)
        env.define("CXX", "invalid") # Required to trick the build system that c++ isn't available (only used for testing)
        tc = AutotoolsToolchain(self)
        # /usr is part of the glibc ABI. See: https://sourceware.org/glibc/wiki/Testing/Builds
        tc.configure_args.append(f"--prefix=/usr")
        tc.configure_args.append(f"--with-gd=no") # Specific to my environment?
        # tc.configure_args.append(f"--with-headers=${self.deps_cpp_info['linux-headers-generic'].include_paths}")
        tc.configure_args.append(f"--with-pkgversion=conan GNU libc {self.version}")
        tc.configure_args.append(f"--with-bugurl={self.url}/issues")
        tc.extra_cflags.append("-nostdinc") # Don't include std includes
        tc.generate(env=env)

        deps = AutotoolsDeps(self)
        deps.generate()

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

    def build(self):
        autotools = Autotools(self)
        autotools.configure()
        autotools.make()
        autotools.make("check")

    def package(self):
        autotools = Autotools(self)
        autotools.install()

        copy(
            self,
            pattern="COPYING*",
            dst=os.path.join(self.package_folder, "licenses"),
            src=self.source_folder,
            keep_path=False,
        )

    def package_info(self):
        # self.cpp_info.libs = collect_libs(self)
        self.cpp_info.includedirs = [os.path.join("usr", "include")]
        self.cpp_info.libdirs = [os.path.join("usr", "lib")]
        self.cpp_info.bindirs = [os.path.join("usr", "bin")]
        self.cpp_info.resdirs = [os.path.join("usr", "share")]

        self.cpp_info.set_property("cmake_target_name", "glibc::glibc")
