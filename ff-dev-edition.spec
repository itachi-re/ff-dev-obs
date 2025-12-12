#
# spec file for package ff-dev-edition
#
# Copyright (c) 2025 itachi_re
#

Name:           ff-dev-edition
Release:        0
License:        MPL-2.0
Summary:        Mozilla Firefox Web Browser (Developer Edition)
URL:            https://www.firefox.com/en-US/channel/desktop/developer
Group:          Productivity/Networking/Web/Browsers
# --- 🦊 FIREFOX VERSION ---
Version:        147.0b3
# --------------------------

# --- 🦀 CBINDGEN VERSION ---
# Update these two lines when a new version is available on Arch Linux Archive
%define cbin_ver  0.29.2
%define cbin_rel  1
# ---------------------------
Source0:       https://ftp.mozilla.org/pub/devedition/releases/%{version}/source/firefox-%{version}.source.tar.xz
Source1:       https://ftp.mozilla.org/pub/devedition/releases/%{version}/source/firefox-%{version}.source.tar.xz.asc
Source2:       https://ftp.mozilla.org/pub/devedition/releases/%{version}/KEY#/mozilla.keyring
Source10:      ff-dev-edition.desktop
# Please create your own keys should you need them :)
Source20:       google-geolocation-api-key
Source30:       google-safe-browsing-api-key
Source99:       https://archive.archlinux.org/packages/c/cbindgen/cbindgen-%{cbin_ver}-%{cbin_rel}-x86_64.pkg.tar.zst


%define major_version %{lua: print((string.gsub(rpm.expand("%{version}"), "b%d+$", "")))}
BuildRequires:  alsa-devel
BuildRequires:  clang-devel
BuildRequires:  cargo
BuildRequires:  curl
BuildRequires:  fdupes
BuildRequires:  gcc-c++
BuildRequires:  gnupg
BuildRequires:  libXt-devel
BuildRequires:  libproxy-devel
BuildRequires:  nasm
BuildRequires:  nodejs >= 12.22.12
BuildRequires:  pkgconfig(gtk+-3.0)
BuildRequires:  pkgconfig(libpulse)
BuildRequires:  python3
BuildRequires:  python3-curses
BuildRequires:  python3-devel
BuildRequires:  rust
# BuildRequires:  rust-cbindgen
BuildRequires:  sccache
BuildRequires:  unzip
BuildRequires:  zstd
Requires(post):   desktop-file-utils
Requires(postun): desktop-file-utils

%description
Firefox Developer Edition provides early access to the latest web development
features and tools.

%define progdir %{_prefix}/%_lib/ff-dev-edition

%prep
# 1. SECURITY CHECK: Verify the tarball manually
# Create a temporary GPG home so we don't need root access
export GNUPGHOME=$(mktemp -d)
# Import the Mozilla keyring (Source2)
gpg --import %{SOURCE2}
# Verify the Signature (Source1) against the Tarball (Source0)
gpg --verify %{SOURCE1} %{SOURCE0}
# Clean up
rm -rf "$GNUPGHOME"
%autosetup -p1 -n firefox-%{major_version}
# FIX WM CLASS (Keep this!)
sed -i '/MOZ_APP_REMOTINGNAME=firefox-dev/d' browser/branding/aurora/configure.sh

%build
# --- AUTOMATED CBINDGEN SETUP ---
# 1. Extract the Arch Linux package (it contains usr/bin/cbindgen)
tar --use-compress-program=unzstd -xf %{SOURCE99}
# 2. Move binary to current folder and make executable
cp usr/bin/cbindgen .
chmod +x ./cbindgen
# 3. Add to PATH
export PATH=$PWD:$PATH

echo "Using bootstrapped cbindgen version:"
./cbindgen --version
# -----------------------------
# Recursion Fix: Filter flags safely using shell
cat << EOF > .obsenv.sh
export CFLAGS=\$(echo "%{optflags}" | sed -e 's/-flto=auto//')
export CXXFLAGS="\$CFLAGS"
export LDFLAGS="\$LDFLAGS -fPIC -Wl,-z,relro,-z,now"

export MACH_BUILD_PYTHON_NATIVE_PACKAGE_SOURCE=system
export MOZCONFIG=$RPM_BUILD_DIR/mozconfig
export MOZILLA_OFFICIAL=1
export MOZ_TELEMETRY_REPORTING=1
EOF
source ./.obsenv.sh

cat << EOF > $MOZCONFIG
export MOZ_APP_REMOTINGNAME=ff-dev-edition

mk_add_options BUILD_OFFICIAL=1
mk_add_options MOZILLA_OFFICIAL=1
mk_add_options MOZ_DEV_EDITION=1
mk_add_options MOZ_MAKE_FLAGS=%{?_smp_mflags}
mk_add_options MOZ_OBJDIR=@TOPSRCDIR@/../obj

. \$topsrcdir/browser/config/mozconfig

ac_add_options --disable-bootstrap
ac_add_options --prefix=%{_prefix}
ac_add_options --libdir=%{_libdir}
ac_add_options --includedir=%{_includedir}

ac_add_options --allow-addon-sideload
ac_add_options --disable-debug
ac_add_options --disable-debug-symbols
ac_add_options --disable-updater
ac_add_options --disable-tests
ac_add_options --enable-alsa
ac_add_options --enable-crashreporter
ac_add_options --enable-default-toolkit=cairo-gtk3-wayland
ac_add_options --enable-install-strip
ac_add_options --enable-libproxy
ac_add_options --enable-lto
ac_add_options --enable-optimize
ac_add_options --enable-release
ac_add_options --enable-rust-simd
ac_add_options --enable-update-channel=aurora
ac_add_options --with-branding=browser/branding/aurora
ac_add_options --with-ccache=sccache
ac_add_options --with-google-location-service-api-keyfile=%{SOURCE20}
ac_add_options --with-google-safebrowsing-api-keyfile=%{SOURCE30}
ac_add_options --with-system-zlib
ac_add_options --with-unsigned-addon-scopes=app
ac_add_options --without-wasm-sandboxed-libraries
EOF

sccache -s
./mach build
sccache -s

%install
source ./.obsenv.sh

install -Dm 0644 %{SOURCE10} %{buildroot}%{_datadir}/applications/ff-dev-edition.desktop

DESTDIR="%{buildroot}" ./mach install

mv %{buildroot}%{_prefix}/%_lib/firefox %{buildroot}%{progdir}

find %{buildroot}%{progdir} \
  -name "*.js" -o \
  -name "*.jsm" -o \
  -name "*.rdf" -o \
  -name "*.properties" -o \
  -name "*.dtd" -o \
  -name "*.txt" -o \
  -name "*.xml" -o \
  -name "*.css" \
  -exec chmod a-x {} +
find %{buildroot}%{progdir} -type f -name ".mkdir.done" -delete

rm %{buildroot}%{_bindir}/firefox
ln -sf ../%{_lib}/ff-dev-edition/firefox-bin %{buildroot}%{_bindir}/firefox-aurora

for size in 16 32 48 64 128; do
  mkdir -p %{buildroot}%{_prefix}/share/icons/hicolor/${size}x${size}/apps
  cp %{buildroot}%{progdir}/browser/chrome/icons/default/default$size.png \
      %{buildroot}%{_prefix}/share/icons/hicolor/${size}x${size}/apps/ff-dev-edition.png
done

rm -f %{buildroot}%{progdir}/updater.ini
rm -f %{buildroot}%{progdir}/removed-files
rm -f %{buildroot}%{progdir}/README.txt
rm -f %{buildroot}%{progdir}/old-homepage-default.properties
rm -f %{buildroot}%{progdir}/run-mozilla.sh
rm -f %{buildroot}%{progdir}/LICENSE
rm -f %{buildroot}%{progdir}/precomplete
rm -f %{buildroot}%{progdir}/update-settings.ini

%fdupes %{buildroot}%{progdir}
%fdupes %{buildroot}%{_datadir}

%post
%desktop_database_post
%icon_theme_cache_post
exit 0

%postun
%icon_theme_cache_postun
%desktop_database_postun
exit 0

%files
%defattr(-,root,root)
%dir %{progdir}
%dir %{progdir}/browser/
%dir %{progdir}/browser/chrome/
%{progdir}/browser/chrome/icons
%{progdir}/browser/omni.ja
%{progdir}/defaults/
%{progdir}/gmp-clearkey/
%{progdir}/firefox
%{progdir}/firefox-bin
%{progdir}/application.ini
%{progdir}/dependentlibs.list
%{progdir}/*.so
%{progdir}/glxtest
%{progdir}/vaapitest
%{progdir}/omni.ja
%{progdir}/fonts/
%{progdir}/pingsender
%{progdir}/platform.ini
%{progdir}/crashhelper
%{progdir}/crashreporter
%{_datadir}/applications/ff-dev-edition.desktop
%{_prefix}/share/icons/hicolor/
%{_bindir}/firefox-aurora

%changelog
