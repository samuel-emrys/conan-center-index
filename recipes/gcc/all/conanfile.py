from conan import ConanFile, conan_version
from conan.tools.gnu import Autotools, AutotoolsToolchain
from conan.tools.gnu.get_gnu_triplet import _get_gnu_triplet
from conan.errors import ConanInvalidConfiguration
from conan.tools.layout import basic_layout
from conan.tools.apple import XCRun
from conan.tools.files import copy, get, replace_in_file, rmdir, rm, collect_libs
from conan.tools.build import cross_building
from conan.tools.env import VirtualBuildEnv
from conan.tools.microsoft import is_msvc
from conan.tools.build.cross_building import get_cross_building_settings
import os

required_conan_version = ">=1.53.0"


class GccConan(ConanFile):
    name = "gcc"
    description = (
        "The GNU Compiler Collection includes front ends for C, "
        "C++, Objective-C, Fortran, Ada, Go, and D, as well as "
        "libraries for these languages (libstdc++,...). "
    )
    topics = ("gcc", "gnu", "compiler", "c", "c++")
    homepage = "https://gcc.gnu.org"
    url = "https://github.com/conan-io/conan-center-index"
    license = "GPL-3.0-only"
    settings = "os", "compiler", "arch", "build_type"

    def configure(self):
        if self.settings.compiler in ["clang", "apple-clang"]:
            # Can't remove this from cxxflags with autotools - so get rid of it
            del self.settings.compiler.libcxx


    def build_requirements(self):
        if self.settings.os == "Linux":
            # binutils recipe is broken for Macos, and Windows uses tools
            # distributed with msys/mingw
            self.tool_requires("binutils/2.38")
        self.tool_requires("flex/2.6.4")

    def requirements(self):
        self.requires("mpc/1.2.0")
        self.requires("mpfr/4.1.0")
        self.requires("gmp/6.2.1")
        self.requires("zlib/1.2.13")
        self.requires("isl/0.24")

    def package_id(self):
        del self.info.settings.compiler

    def validate_build(self):
        if is_msvc(self):
            raise ConanInvalidConfiguration("GCC can't be built with MSVC")

    def validate(self):
        if self.settings.os == "Windows":
            raise ConanInvalidConfiguration(
                "Windows builds aren't currently supported. Contributions to support this are welcome."
            )
        if self.settings.os == "Macos":
            # FIXME: This recipe should largely support Macos, however the following
            # errors are present when building using the c3i CI:
            # clang: error: unsupported option '-print-multi-os-directory'
            # clang: error: no input files
            raise ConanInvalidConfiguration(
                "Macos builds aren't currently supported. Contributions to support this are welcome."
            )
        if cross_building(self):
            raise ConanInvalidConfiguration(
                "Cross builds are not current supported. Contributions to support this are welcome"
            )

    def layout(self):
        basic_layout(self, src_folder="src")

    def generate(self):
        # Ensure binutils and flex are on the path.
        # TODO: Remove when conan 2.0 is released as this will be default behaviour
        buildenv = VirtualBuildEnv(self)
        buildenv.generate()

        tc = AutotoolsToolchain(self)
        tc.configure_args.append("--enable-languages=c,c++,fortran")
        tc.configure_args.append("--disable-nls")
        tc.configure_args.append("--disable-multilib")
        tc.configure_args.append("--disable-bootstrap")
        # TODO: Remove --prefix and --libexecdir args when c3i supports conan 1.55.0.
        # This change should only happen in conjunction with a move to
        # autotools.install("install-strip")
        tc.configure_args.append(f"--prefix={self.package_folder}")
        tc.configure_args.append(f"--libexecdir={os.path.join(self.package_folder, 'bin', 'libexec')}")
        tc.configure_args.append(f"--with-zlib={self.dependencies['zlib'].package_folder}")
        tc.configure_args.append(f"--with-isl={self.dependencies['isl'].package_folder}")
        tc.configure_args.append(f"--with-gmp={self.dependencies['gmp'].package_folder}")
        tc.configure_args.append(f"--with-mpc={self.dependencies['mpc'].package_folder}")
        tc.configure_args.append(f"--with-mpfr={self.dependencies['mpfr'].package_folder}")
        tc.configure_args.append(f"--with-pkgversion=conan GCC {self.version}")
        tc.configure_args.append(f"--program-suffix=-{self.version}")
        tc.configure_args.append(f"--with-bugurl={self.url}/issues")

        if self.settings.os == "Macos":
            xcrun = XCRun(self)
            tc.configure_args.append(f"--with-sysroot={xcrun.sdk_path}")
            # Set native system header dir to ${{sysroot}}/usr/include to
            # isolate installation from the system as much as possible
            tc.configure_args.append("--with-native-system-header-dir=/usr/include")
            tc.make_args.append("BOOT_LDFLAGS=-Wl,-headerpad_max_install_names")
        tc.generate()

        # Don't use AutotoolsDeps here - deps are passed directly in configure_args.
        # Using AutotoolsDeps causes the compiler tests to fail by erroneously adding
        # additional $LIBS to the test compilation

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

    def build(self):
        # If building on x86_64, change the default directory name for 64-bit libraries to "lib":
        replace_in_file(
            self,
            os.path.join(self.source_folder, "gcc", "config", "i386", "t-linux64"),
            "m64=../lib64",
            "m64=../lib",
            strict=False,
        )

        # Ensure correct install names when linking against libgcc_s;
        # see discussion in https://github.com/Homebrew/legacy-homebrew/pull/34303
        replace_in_file(
            self,
            os.path.join(self.source_folder, "libgcc", "config", "t-slibgcc-darwin"),
            "@shlib_slibdir@",
            os.path.join(self.package_folder, "lib"),
            strict=False,
        )

        autotools = Autotools(self)
        autotools.configure()
        autotools.make()

    def package(self):
        autotools = Autotools(self)
        # TODO: Use more modern autotools.install(target="install-strip") when c3i supports
        # conan client version of 1.55.0. Make sure that the minimum conan version is also bumped
        # when this is changed.
        autotools.make(target="install-strip")

        rmdir(self, os.path.join(self.package_folder, "share"))
        rm(self, "*.la", self.package_folder, recursive=True)
        copy(
            self,
            pattern="COPYING*",
            dst=os.path.join(self.package_folder, "licenses"),
            src=self.source_folder,
            keep_path=False,
        )

    def package_info(self):
        # os_build, arch_build, os_host, arch_host = get_cross_building_settings(self)
        # compiler = self.settings.get_safe("compiler")
        # # e.g., x86_64-pc-linux-gnu
        # triplet = _get_gnu_triplet(os_host, arch_host, compiler=compiler)
        triplet = "x86_64-pc-linux-gnu"
        # self.cpp_info.libdirs = [
        #     "lib",
        #     "lib64",
        #     os.path.join("libexec", "gcc", triplet, self.version),
        #     os.path.join("lib", "gcc", triplet, self.version, "plugin"),
        # ]
        # self.cpp_info.libs = collect_libs(self) # asan, atomic, gcc_s, gfortran, gomp, itm, lsan, quadmath, ssp, stdc++, tsan, ubsan

        self.cpp_info.components["gcc_s"].set_property("cmake_target_name", "gcc::gcc_s")
        self.cpp_info.components["gcc_s"].libdirs = ["lib"]
        self.cpp_info.components["gcc_s"].libs = ["gcc_s"]
        if self.settings.os in ("Linux", "FreeBSD"):
            self.cpp_info.components["gcc_s"].system_libs.append("m")
            self.cpp_info.components["gcc_s"].system_libs.append("rt")
            self.cpp_info.components["gcc_s"].system_libs.append("pthread")
            self.cpp_info.components["gcc_s"].system_libs.append("dl")

        self.cpp_info.components["gfortran"].set_property("cmake_target_name", "gcc::gfortran")
        self.cpp_info.components["gfortran"].libdirs = ["lib"]
        self.cpp_info.components["gfortran"].libs = ["gfortran"]
        self.cpp_info.components["gfortran"].requires = ["gcc_s", "quadmath"]
        if self.settings.os in ("Linux", "FreeBSD"):
            self.cpp_info.components["gfortran"].system_libs.append("m")

        self.cpp_info.components["quadmath"].set_property("cmake_target_name", "gcc::quadmath")
        self.cpp_info.components["quadmath"].libdirs = ["lib"]
        self.cpp_info.components["quadmath"].libs = ["quadmath"]
        if self.settings.os in ("Linux", "FreeBSD"):
            self.cpp_info.components["quadmath"].system_libs.append("m")

        self.cpp_info.components["itm"].set_property("cmake_target_name", "gcc::itm")
        self.cpp_info.components["itm"].libdirs = ["lib"]
        self.cpp_info.components["itm"].libs = ["itm"]
        if self.settings.os in ("Linux", "FreeBSD"):
            self.cpp_info.components["itm"].system_libs.append("pthread")

        self.cpp_info.components["tsan"].set_property("cmake_target_name", "gcc::tsan")
        self.cpp_info.components["tsan"].libdirs = ["lib"]
        self.cpp_info.components["tsan"].libs = ["tsan"]
        self.cpp_info.components["tsan"].requires = ["gcc_s", "stdc++"]
        if self.settings.os in ("Linux", "FreeBSD"):
            self.cpp_info.components["tsan"].system_libs.append("pthread")
            self.cpp_info.components["tsan"].system_libs.append("m")
            self.cpp_info.components["tsan"].system_libs.append("dl")

        self.cpp_info.components["stdc++"].set_property("cmake_target_name", "gcc::stdcpp")
        self.cpp_info.components["stdc++"].libdirs = ["lib"]
        self.cpp_info.components["stdc++"].libs = ["stdc++"]
        self.cpp_info.components["stdc++"].requires = ["gcc_s"]
        if self.settings.os in ("Linux", "FreeBSD"):
            self.cpp_info.components["stdc++"].system_libs.append("m")

        self.cpp_info.components["ssp"].set_property("cmake_target_name", "gcc::ssp")
        self.cpp_info.components["ssp"].libdirs = ["lib"]
        self.cpp_info.components["ssp"].libs = ["ssp"]

        self.cpp_info.components["atomic"].set_property("cmake_target_name", "gcc::atomic")
        self.cpp_info.components["atomic"].libdirs = ["lib"]
        self.cpp_info.components["atomic"].libs = ["atomic"]
        if self.settings.os in ("Linux", "FreeBSD"):
            self.cpp_info.components["atomic"].system_libs.append("pthread")

        self.cpp_info.components["gomp"].set_property("cmake_target_name", "gcc::gomp")
        self.cpp_info.components["gomp"].libdirs = ["lib"]
        self.cpp_info.components["gomp"].libs = ["gomp"]
        if self.settings.os in ("Linux", "FreeBSD"):
            self.cpp_info.components["gomp"].system_libs.append("pthread")
            self.cpp_info.components["gomp"].system_libs.append("dl")

        self.cpp_info.components["asan"].set_property("cmake_target_name", "gcc::asan")
        self.cpp_info.components["asan"].libdirs = ["lib"]
        self.cpp_info.components["asan"].libs = ["asan"]
        self.cpp_info.components["asan"].requires = ["gcc_s", "stdc++"]
        if self.settings.os in ("Linux", "FreeBSD"):
            self.cpp_info.components["asan"].system_libs.append("pthread")
            self.cpp_info.components["asan"].system_libs.append("m")
            self.cpp_info.components["asan"].system_libs.append("dl")

        self.cpp_info.components["ubsan"].set_property("cmake_target_name", "gcc::ubsan")
        self.cpp_info.components["ubsan"].libdirs = ["lib"]
        self.cpp_info.components["ubsan"].libs = ["ubsan"]
        self.cpp_info.components["ubsan"].requires = ["gcc_s", "stdc++"]
        if self.settings.os in ("Linux", "FreeBSD"):
            self.cpp_info.components["ubsan"].system_libs.append("pthread")
            self.cpp_info.components["ubsan"].system_libs.append("dl")
            self.cpp_info.components["ubsan"].system_libs.append("rt")

        self.cpp_info.components["lsan"].set_property("cmake_target_name", "gcc::lsan")
        self.cpp_info.components["lsan"].libdirs = ["lib"]
        self.cpp_info.components["lsan"].libs = ["lsan"]
        self.cpp_info.components["lsan"].requires = ["gcc_s", "stdc++"]
        if self.settings.os in ("Linux", "FreeBSD"):
            self.cpp_info.components["lsan"].system_libs.append("pthread")
            self.cpp_info.components["lsan"].system_libs.append("dl")
            self.cpp_info.components["lsan"].system_libs.append("rt")

        self.cpp_info.components["cc1"].set_property("cmake_target_name", "gcc::cc1")
        self.cpp_info.components["cc1"].libdirs = ["lib"]
        self.cpp_info.components["cc1"].libs = ["cc1"]
        self.cpp_info.components["cc1"].requires = ["gcc_s", "stdc++"]



        bindir = os.path.join(self.package_folder, "bin")

        cc = os.path.join(bindir, f"gcc-{self.version}")
        self.output.info("Creating CC env var with: " + cc)
        self.buildenv_info.define("CC", cc)

        cxx = os.path.join(bindir, f"g++-{self.version}")
        self.output.info("Creating CXX env var with: " + cxx)
        self.buildenv_info.define("CXX", cxx)

        fc = os.path.join(bindir, f"gfortran-{self.version}")
        self.output.info("Creating FC env var with: " + fc)
        self.buildenv_info.define("FC", fc)

        ar = os.path.join(bindir, f"gcc-ar-{self.version}")
        self.output.info("Creating AR env var with: " + ar)
        self.buildenv_info.define("AR", ar)

        nm = os.path.join(bindir, f"gcc-nm-{self.version}")
        self.output.info("Creating NM env var with: " + nm)
        self.buildenv_info.define("NM", nm)

        ranlib = os.path.join(bindir, f"gcc-ranlib-{self.version}")
        self.output.info("Creating RANLIB env var with: " + ranlib)
        self.buildenv_info.define("RANLIB", ranlib)

        # TODO: Remove after conan 2.0 is released
        self.env_info.CC = cc
        self.env_info.CXX = cxx
        self.env_info.FC = fc
        self.env_info.AR = ar
        self.env_info.NM = nm
        self.env_info.RANLIB = ranlib
