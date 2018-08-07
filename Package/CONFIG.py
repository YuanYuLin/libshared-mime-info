import ops
import iopc

TARBALL_FILE="shared-mime-info-1.9.tar.xz"
TARBALL_DIR="shared-mime-info-1.9"
INSTALL_DIR="shared-mime-info-bin"
pkg_path = ""
output_dir = ""
tarball_pkg = ""
tarball_dir = ""
install_dir = ""
install_tmp_dir = ""
cc_host = ""
dst_include_dir = ""
dst_lib_dir = ""
src_pkgconfig_dir = ""
dst_pkgconfig_dir = ""

def set_global(args):
    global pkg_path
    global output_dir
    global tarball_pkg
    global install_dir
    global install_tmp_dir
    global tarball_dir
    global cc_host
    global dst_include_dir
    global dst_lib_dir
    global src_pkgconfig_dir
    global dst_pkgconfig_dir
    pkg_path = args["pkg_path"]
    output_dir = args["output_path"]
    tarball_pkg = ops.path_join(pkg_path, TARBALL_FILE)
    install_dir = ops.path_join(output_dir, INSTALL_DIR)
    install_tmp_dir = ops.path_join(output_dir, INSTALL_DIR + "-tmp")
    tarball_dir = ops.path_join(output_dir, TARBALL_DIR)
    cc_host_str = ops.getEnv("CROSS_COMPILE")
    cc_host = cc_host_str[:len(cc_host_str) - 1]
    dst_include_dir = ops.path_join("include",args["pkg_name"])
    dst_lib_dir = ops.path_join(install_dir, "lib")
    src_pkgconfig_dir = ops.path_join(pkg_path, "pkgconfig")
    dst_pkgconfig_dir = ops.path_join(install_dir, "pkgconfig")

def MAIN_ENV(args):
    set_global(args)

    ops.exportEnv(ops.setEnv("CC", ops.getEnv("CROSS_COMPILE") + "gcc"))
    ops.exportEnv(ops.setEnv("CXX", ops.getEnv("CROSS_COMPILE") + "g++"))
    ops.exportEnv(ops.setEnv("CROSS", ops.getEnv("CROSS_COMPILE")))
    ops.exportEnv(ops.setEnv("DESTDIR", install_tmp_dir))

    cc_sysroot = ops.getEnv("CC_SYSROOT")

    cflags = ""
    cflags += " -I" + ops.path_join(cc_sysroot, 'usr/include')
    cflags += " -I" + ops.path_join(iopc.getSdkPath(), 'usr/include')
    cflags += " -I" + ops.path_join(iopc.getSdkPath(), 'usr/include/libxml2')

    ldflags = ""
    ldflags += " -L" + ops.path_join(cc_sysroot, 'lib')
    ldflags += " -L" + ops.path_join(cc_sysroot, 'usr/lib')
    ldflags += " -L" + ops.path_join(iopc.getSdkPath(), 'lib')
    ldflags += " -lpcre -lxml2 -lffi -lz -lgmodule-2.0 -lglib-2.0"

    ops.exportEnv(ops.setEnv("LDFLAGS", ldflags))
    ops.exportEnv(ops.setEnv("CFLAGS", cflags))

    #ops.exportEnv(ops.setEnv("PKG_CONFIG_LIBDIR", ops.path_join(iopc.getSdkPath(), "pkgconfig")))
    #ops.exportEnv(ops.setEnv("PKG_CONFIG_SYSROOT_DIR", iopc.getSdkPath()))
    #ops.exportEnv(ops.setEnv("LIBS", libs))
    #extra_conf.append('CFLAGS="-I' + ops.path_join(iopc.getSdkPath(), 'usr/include/libz') + '"')

    return False

def MAIN_EXTRACT(args):
    set_global(args)

    ops.unTarXz(tarball_pkg, output_dir)
    #ops.copyto(ops.path_join(pkg_path, "finit.conf"), output_dir)

    return True

def MAIN_PATCH(args, patch_group_name):
    set_global(args)
    for patch in iopc.get_patch_list(pkg_path, patch_group_name):
        if iopc.apply_patch(tarball_dir, patch):
            continue
        else:
            sys.exit(1)

    return True

def MAIN_CONFIGURE(args):
    set_global(args)

    print "SDK include path:" + iopc.getSdkPath()

    extra_conf = []
    extra_conf.append("--disable-update-mimedb")
    extra_conf.append("--disable-default-make-check")
    extra_conf.append("--host=" + cc_host)

    cflags = ""
    cflags += " -I" + ops.path_join(iopc.getSdkPath(), "usr/include/libxml2")
    cflags += " -I" + ops.path_join(iopc.getSdkPath(), "usr/include/libglib/glib-2.0")
    cflags += " -I" + ops.path_join(iopc.getSdkPath(), "usr/include/libglib/gio-unix-2.0")
    cflags += " -I" + ops.path_join(iopc.getSdkPath(), "usr/include/libglib")
    cflags += " -I" + ops.path_join(iopc.getSdkPath(), "usr/include/libpcre3")
    extra_conf.append("ALL_CFLAGS=" + cflags)

    libs = ""
    libs += " -L" + ops.path_join(iopc.getSdkPath(), "lib")
    libs += " -lxml2 -lglib-2.0"
    extra_conf.append("ALL_LIBS=" + libs)

    print extra_conf
    iopc.configure(tarball_dir, extra_conf)

    return True

def MAIN_BUILD(args):
    set_global(args)

    ops.mkdir(install_dir)
    ops.mkdir(install_tmp_dir)
    iopc.make(tarball_dir)
    iopc.make_install(tarball_dir)
    return False

def MAIN_INSTALL(args):
    set_global(args)

    ops.mkdir(ops.path_join(install_dir, "usr/bin"))
    ops.copyto(ops.path_join(install_tmp_dir, "usr/local/bin/."), ops.path_join(install_dir, "usr/bin"))

    ops.mkdir(ops.path_join(install_dir, "usr/local/share/locale"))
    ops.copyto(ops.path_join(install_tmp_dir, "usr/local/share/locale/."), ops.path_join(install_dir, "usr/local/share/locale"))

    ops.mkdir(ops.path_join(install_dir, "usr/local/share/mime"))
    ops.copyto(ops.path_join(install_tmp_dir, "usr/local/share/mime/."), ops.path_join(install_dir, "usr/local/share/mime"))

    ops.mkdir(dst_pkgconfig_dir)
    ops.copyto(ops.path_join(src_pkgconfig_dir, '.'), dst_pkgconfig_dir)

    iopc.installBin(args["pkg_name"], ops.path_join(install_dir, "usr/."), "usr")
    iopc.installBin(args["pkg_name"], ops.path_join(dst_pkgconfig_dir, '.'), "pkgconfig")

    return False

def MAIN_CLEAN_BUILD(args):
    set_global(args)

    return False

def MAIN(args):
    set_global(args)

