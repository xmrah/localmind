{
  description = "xPalace - Multi-IDE MCP Hafıza Sunucusu";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, flake-utils }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = nixpkgs.legacyPackages.${system};
      in
      {
        devShells.default = pkgs.mkShell {
          buildInputs = [
            pkgs.python311
            pkgs.python311Packages.pip
            pkgs.python311Packages.virtualenv
            # ChromaDB ve Python C uzantıları için gerekli C kütüphaneleri:
            pkgs.stdenv.cc.cc.lib
            pkgs.zlib
          ];

          # C/C++ bağlamaları (bindings) içeren Python paketleri (ChromaDB vb.)
          # NixOS üzerinde hata vermesin diye dinamik kütüphane yolunu ayarlıyoruz:
          shellHook = ''
            export LC_ALL=en_US.UTF-8
            export LD_LIBRARY_PATH="${pkgs.lib.makeLibraryPath [ pkgs.stdenv.cc.cc.lib pkgs.zlib ]}"
            
            if [ ! -d .venv ]; then
              echo "🔧 Python sanal ortamı (.venv) oluşturuluyor..."
              python3 -m venv .venv
            fi
            
            # Sanal ortamı otomatik aktif et
            source .venv/bin/activate
            
            echo "🏰 xPalace (NixOS Forensic Edition) Geliştirme Ortamına Hoş Geldin!"
            echo "👉 Gerekli paketleri kurmak için: pip install fastmcp chromadb"
          '';
        };
      }
    );
}
