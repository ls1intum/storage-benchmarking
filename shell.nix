{ pkgs ? import <nixpkgs> {} }:

pkgs.mkShell {
  name = "python-dev";

  buildInputs = with pkgs; [
    python311
    zsh
    poetry
    fio
  ];

  shellHook = ''
    export SHELL=$(which zsh)
    echo "Welcome to the Python development environment"
    echo "Python version: $(python3 --version)"
    echo "Poetry version: $(poetry --version)"
    echo "FIO version: $(fio -v)"
    zsh
  '';
}
