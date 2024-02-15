#!/bin/bash

for img in *.png; do
  convert -size 800x960 xc:none $img -geometry +0+0 -composite -depth 8 bgra:- | xz -c > "./fb/$(basename $img .png).img.xz"
done
