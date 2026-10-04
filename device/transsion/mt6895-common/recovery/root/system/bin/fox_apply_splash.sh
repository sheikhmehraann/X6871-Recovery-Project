#!/bin/sh
# OrangeFox Splash Applier for Infinix GT 20 Pro (X6871)
set -e

spl_bg_user=$(twrp xget spl_bg_user 2>/dev/null || echo "0")
spl_bg_on=$(twrp xget spl_bg_on 2>/dev/null || echo "0")
spl_bg_color=$(twrp xget spl_bg_color 2>/dev/null || echo "#000000")
spl_logo_type=$(twrp xget spl_logo_type 2>/dev/null || echo "o")
spl_ofr=$(twrp xget spl_ofr 2>/dev/null || echo "1")

logo_color="F86314"
case "$spl_logo_type" in
    w) logo_color="ffffff" ;;
    d) logo_color="353535" ;;
    c) logo_color="00BCD4" ;;
    r) logo_color="E91E63" ;;
    b) logo_color="2196F3" ;;
    g) logo_color="4CAF50" ;;
    y) logo_color="FFEB3B" ;;
    p) logo_color="9C27B0" ;;
    o) logo_color="F86314" ;;
esac

logo_on=""
[ "$spl_logo_type" = "0" ] && logo_on="!--"

logo_ofr="!--"
[ "$spl_ofr" = "1" ] && logo_ofr=""
[ "$spl_logo_type" = "0" ] && logo_ofr="!--"

bg_on="!--"
mkdir -p /tmp/orangefox/ramdisk/twres/images/Splash /tmp/orangefox/ramdisk/twres/themes/sed /twres/images/Splash

if [ "$spl_bg_on" = "1" ] && [ -f /twres/images/Splash/user.png ]; then
    bg_on=""
    cp -f /twres/images/Splash/user.png /tmp/orangefox/ramdisk/twres/images/Splash/user.png
fi

if [ "$spl_bg_user" = "1" ]; then
    sed -e "s/#SHOWOFR#/${logo_ofr}/g" \
        -e "s/#TCOLOR#/${logo_color}/g" \
        -e "s/#BG_COLOR#/${spl_bg_color}/g" \
        -e "s/#LOGO_TYPE#/${spl_logo_type}/g" \
        -e "s/#LOGO_ON#/${logo_on}/g" \
        -e "s/#BG_IMG#/${bg_on}/g" \
        /twres/themes/sed/splash.xml > /tmp/orangefox/ramdisk/twres/splash.xml
else
    cp -f /twres/themes/sed/splash_orig.xml /tmp/orangefox/ramdisk/twres/splash.xml
fi

cp -f /tmp/orangefox/ramdisk/twres/splash.xml /twres/splash.xml
twrp xset spl_parsed=0
exit 0
