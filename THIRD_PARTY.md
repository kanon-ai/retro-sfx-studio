# Third-party licenses and notices

Original Retro SFX Studio code and documentation are licensed under the [MIT License](LICENSE).
The MIT License does not replace the licenses of third-party components listed below.

ymfm by Aaron Giles and contributors — BSD 3-Clause License.

- Source: https://github.com/aaronsgiles/ymfm
- Pinned commit: `81aec25ccbb98f4873a255f7551ac4dadac59b4a`
- Source and full license: `vendor/ymfm/` (distribution license: `_internal/licenses/LICENSE`)
- No user BIOS or proprietary ROM files are required or included.

The standalone YM2149 wrapper in this revision reports clock/64 but advances one SSG tick per generated sample. Our adapter uses clock/8, matching `ssg_engine::clock()` and the measured 440 Hz test. The vendored source is unchanged.

Retro SFX Studio is an independent project. The hardware-style interface does not use KORG logos or artwork and does not imply an affiliation with KORG.

MCP implementation reference: https://modelcontextprotocol.io/specification/2025-11-25/basic/transports

The Windows distribution includes CPython 3.13.5, the PyInstaller 6.20.0 bootloader (bootloader exception), and OpenSSL libraries used by the Python runtime. Their license texts are included under `_internal/licenses/` and `licenses/` in the source package.

The bundled license files preserve the upstream copyright notices and applicable terms. Vendored ymfm sources are unmodified; application-specific clock handling is implemented in `native/render.cpp`.
