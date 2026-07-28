#!/usr/bin/env python3
"""Patch EmulatorJS 4.2.3's false-fatal DOSBox Pure startup exception.

The threaded DOSBox Pure core can synchronously throw a WebAssembly
"memory access out of bounds" exception from callMain while its worker keeps
booting the game. EmulatorJS catches that exception around the entire startup
routine, displays "Failed to start game", and skips UI initialization.

Keep the workaround narrowly scoped to that exact core and exception. The
replacement count guards make an EmulatorJS upgrade fail the image build
instead of silently producing an unpatched image.
"""

from pathlib import Path


ASSET_ROOT = Path("/var/www/html/assets/emulatorjs/data")

PATCHES = {
    "emulator.min.js": (
        'this.Module.callMain(t),"number"==typeof this.config.softLoad',
        '(()=>{try{this.Module.callMain(t)}catch(e){if("dosbox_pure"!==this.getCore()||'
        '!(e instanceof WebAssembly.RuntimeError)||!String(e).includes("memory access out of bounds"))'
        'throw e;console.warn("Ignoring recoverable DOSBox Pure startup exception",e)}})(),'
        '"number"==typeof this.config.softLoad',
    ),
    "src/emulator.js": (
        "            this.Module.callMain(args);\n",
        "            try {\n"
        "                this.Module.callMain(args);\n"
        "            } catch (error) {\n"
        "                const recoverableDosboxPureError =\n"
        '                    this.getCore() === "dosbox_pure" &&\n'
        "                    error instanceof WebAssembly.RuntimeError &&\n"
        '                    String(error).includes("memory access out of bounds");\n'
        "                if (!recoverableDosboxPureError) throw error;\n"
        '                console.warn("Ignoring recoverable DOSBox Pure startup exception", error);\n'
        "            }\n",
    ),
}

for relative_path, (old, new) in PATCHES.items():
    path = ASSET_ROOT / relative_path
    source = path.read_text()
    count = source.count(old)
    if count != 1:
        raise RuntimeError(f"Expected one patch target in {path}, found {count}")
    path.write_text(source.replace(old, new))
    print(f"Patched {path}")
