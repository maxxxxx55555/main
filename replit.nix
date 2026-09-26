{ pkgs }: {
  deps = with pkgs; [
    python311
    python311Packages.pip
    python311Packages.venv
    gcc
    libpq
  ];
}