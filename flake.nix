{
  inputs = {
    nixpkgs.url = "github:nixos/nixpkgs/nixpkgs-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, flake-utils, ... }:
    flake-utils.lib.eachDefaultSystem (system:
      let pkgs = import nixpkgs { system = system; }; in
      {
        devShells.default = pkgs.mkShellNoCC {
          NIX_LD_LIBRARY_PATH = pkgs.lib.makeLibraryPath [
            pkgs.glibc pkgs.libz
          ];
          shellHook = ''
            export SSL_CERT_FILE="/etc/static/ssl/certs/ca-bundle.crt"
          '';
          packages = with pkgs; [ git just uv railway sqlite mdbook mdbook-mermaid ];
        };
      }
    );
}
