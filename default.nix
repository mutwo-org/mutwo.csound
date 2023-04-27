let
  sourcesTarball = fetchTarball "https://github.com/mutwo-org/mutwo-nix/archive/refs/heads/main.tar.gz";
  mutwo-csound = import (sourcesTarball + "/mutwo.csound/default.nix") {};
  mutwo-csound-local = mutwo-csound.overrideAttrs (
    finalAttrs: previousAttrs: {
       src = ./.;
    }
  );
in
  mutwo-csound-local

