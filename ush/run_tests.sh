#!/bin/bash

uw execute \
  --module coastal.py \
  --classname Coastal \
  --task provisioned_rundir \
  --config-file ../tests/coastal_ike_shinnecock_atm2sch.yaml \
  --cycle 2008-08-23T00 \
  --batch
