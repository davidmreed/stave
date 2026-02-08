{
  inputs = {
    nixpkgs.url = "github:nixos/nixpkgs/nixpkgs-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, flake-utils, ... }:
    flake-utils.lib.eachDefaultSystem (system:
      let pkgs = import nixpkgs { system = system; }; in
      {
        devShells.default = pkgs.mkShell {
          NIX_LD_LIBRARY_PATH = pkgs.lib.makeLibraryPath [
            pkgs.glibc
          ];
            NIX_LD = builtins.readFile "${stdenv.cc}/nix-support/dynamic-linker";
          packages = with pkgs; [ git just uv railway sqlite mdbook mdbook-mermaid ];
        };
      }
    );
}
