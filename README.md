# muendat-generation
Simple scripts that, together with the g application, create new muendat data. Also compares new data to old data.

## Installation

Ensure you have the `$EGS_HOME` environment variable properly defined in your .bashrc/.zshrc/.cshrc bootup profile.
If you are already using egs_brachy this should already be properly configured.

Ensure the `g` application is compiled. I.e. go to \$EGS_HOME/g and type `make`.
But first, since we want to use radiative corrections to the Compton cross section, we need to ensure that 
our `g` application is compiled with radiative corrections enabled. See PIRS701 page 46. 
Where you place `$(EGS SOURCEDIR)rad compton1.mortran` in g.make is important, so follow the instructions closely.
You will also need to manually modify \$HEN_HOUSE/src/egsnrc.mortran if you're using a modern fortran compiler
(Modern compilers don't like the `a$` part of the mortan code, so you should replace all instances of that pattern 
with `a` using e.g. the shell command `sed -i.bak 's/a\$$/a/g' egsnrc.mortran`).

You should place this `muendat-generation` repository directly inside the `g` repository (so that this README has the 
path \$EGS_HOME/g/muendat-generation/README.md). In order to run the main python3 script there
(muendat_generation.py) you will need to setup a virtual environment and download the required 3rd-party packages.
To do so, use the following terminal commands while in the \$EGS_HOME/g/muendat-generation directory

> python -m venv .venv

> source .venv/bin/activate

> pip install -r requirements.txt

You should now have all the prerequisites to run this application

## Usage

While inside the $EGS_HOME/g/muendat-generation directory, type

> python3 muendat_generation.py

This will find all materials in all .muendat files in egs_brachy/lib/muen and attempt to reproduce their results.
If the material is not defined in egs_brachy/media/material.dat then the material will not be calculated, unless
your previous .muendat file is accurate about which .pegs4dat file to try to use from \$HEN_HOUSE/pegs4/data
