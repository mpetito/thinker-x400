#!/bin/bash
echo ${2}
echo "date0: $(date +"%Y-%m-%d %H:%M:%S")"
SD_PATH=~/printer_data/gcodes
rm ${SD_PATH}/plr.gcode
#SD_PATH=~octoprint/.octoprint/uploads
#cat "${2}" > ~/plrtmpA.$$
echo "date1: $(date +"%Y-%m-%d %H:%M:%S")"

cat "${2}" | sed -n '/HEADER_BLOCK_START/,/THUMBNAIL_BLOCK_END/{p}' > ${SD_PATH}/plr.gcode
echo '' >> ${SD_PATH}/plr.gcode


#sed -i 's/z./z0./g' /tmp/plrtmpA.$$
#cat /tmp/plrtmpA.$$ | sed -e '1,/Z'${1}'/ d' | sed -ne '/ Z/,$ p' | grep -m 1 ' Z' | sed -ne 's/.* Z\([^ ]*\)/SET_KINEMATIC_POSITION Z=\1/p' > ${SD_PATH}/plr.gcode
echo "date20: $(date +"%Y-%m-%d %H:%M:%S")"
#echo 'START_TEMPS' >> ${SD_PATH}/plr.gcode
cat "${2}" | sed '/G1 Z'${1}'/q' | sed -ne '/\(M104\|M140\|M109\|M190\)/p' >> ${SD_PATH}/plr.gcode
echo "date21: $(date +"%Y-%m-%d %H:%M:%S")"
#cat ${2} | sed -ne '/;End of Gcode/,$ p' | tr '\n' ' ' | sed -ne 's/ ;[^ ]* //gp' | sed -ne 's/\\\\n/;/gp' | tr ';' '\n' | grep material_bed_temperature | sed -ne 's/.* = /M140 S/p' | head -1 >> ${SD_PATH}/plr.gcode
#echo "date22: $(date +"%Y-%m-%d %H:%M:%S")"
#cat ${2} | sed -ne '/;End of Gcode/,$ p' | tr '\n' ' ' | sed -ne 's/ ;[^ ]* //gp' | sed -ne 's/\\\\n/;/gp' | tr ';' '\n' | grep material_print_temperature | sed -ne 's/.* = /M104 S/p' | head -1 >> ${SD_PATH}/plr.gcode
#echo "date23: $(date +"%Y-%m-%d %H:%M:%S")"
#cat ${2} | sed -ne '/;End of Gcode/,$ p' | tr '\n' ' ' | sed -ne 's/ ;[^ ]* //gp' | sed -ne 's/\\\\n/;/gp' | tr ';' '\n' | grep material_bed_temperature | sed -ne 's/.* = /M190 S/p' | head -1 >> ${SD_PATH}/plr.gcode
#cat ${2} | sed -ne '/;End of Gcode/,$ p' | tr '\n' ' ' | sed -ne 's/ ;[^ ]* //gp' | sed -ne 's/\\\\n/;/gp' | tr ';' '\n' | grep material_print_temperature | sed -ne 's/.* = /M109 S/p' | head -1 >> ${SD_PATH}/plr.gcode
echo "date3: $(date +"%Y-%m-%d %H:%M:%S")"
# cat /tmp/plrtmpA.$$ | sed -e '1,/ Z'${1}'[^0-9]*$/ d' | sed -e '/ Z/q' | tac | grep -m 1 ' E' | sed -ne 's/.* E\([^ ]*\)/G92 E\1/p' >> ${SD_PATH}/plr.gcode
#tac /tmp/plrtmpA.$$ | sed -e '/ Z'${1}'[^0-9]*$/q' | tac | tail -n+2 | sed -e '/ Z[0-9]/ q' | tac | sed -e '/ E[0-9]/ q' | sed -ne 's/.* E\([^ ]*\)/G92 E\1/p' >> ${SD_PATH}/plr.gcode
BG_EX=`tac "${2}" | sed -e '/G1 Z'${1}'[^0-9]*$/q' | tac | tail -n+2 | sed -e '/ Z[0-9]/ q' | tac | sed -e '/ E[0-9]/ q' | sed -ne 's/.* E\([^ ]*\)/G92 E\1/p'`
# If we failed to match an extrusion command (allowing us to correctly set the E axis) prior to the matched layer height, then simply set the E axis to the first E value present in the resemued gcode.  This avoids extruding a huge blod on resume, and/or max extrusion errors.
if [ "${BG_EX}" = "" ]; then
 BG_EX=`tac "${2}" | sed -e '/G1 Z'${1}'[^0-9]*$/q' | tac | tail -n+2 | sed -ne '/ Z/,$ p' | sed -e '/ E[0-9]/ q' | sed -ne 's/.* E\([^ ]*\)/G92 E\1/p'`
fi
echo "date4: $(date +"%Y-%m-%d %H:%M:%S")"
echo 'G92 E0' >> ${SD_PATH}/plr.gcode
echo 'M83' >> ${SD_PATH}/plr.gcode
echo 'G90' >> ${SD_PATH}/plr.gcode

echo ${BG_EX} >> ${SD_PATH}/plr.gcode

echo 'SET_KINEMATIC_POSITION Z='$1 >> ${SD_PATH}/plr.gcode
echo 'G91' >> ${SD_PATH}/plr.gcode
echo 'G1 Z4' >> ${SD_PATH}/plr.gcode
echo 'G90' >> ${SD_PATH}/plr.gcode
echo 'G28 X Y' >> ${SD_PATH}/plr.gcode
echo 'G91' >> ${SD_PATH}/plr.gcode
echo 'G1 Z-4.08' >> ${SD_PATH}/plr.gcode
echo 'G90' >> ${SD_PATH}/plr.gcode
echo 'M83' >> ${SD_PATH}/plr.gcode
echo 'G92 E0' >> ${SD_PATH}/plr.gcode
echo 'G1 E2' >> ${SD_PATH}/plr.gcode
echo 'G1 X350 Y350 F6000' >> ${SD_PATH}/plr.gcode
echo 'G92 E0' >> ${SD_PATH}/plr.gcode
echo 'M106 S250' >> ${SD_PATH}/plr.gcode
echo 'SET_KINEMATIC_POSITION Z='$1 >> ${SD_PATH}/plr.gcode
echo "date5: $(date +"%Y-%m-%d %H:%M:%S")"
cat "${2}" | sed -e '1,/G1 Z'${1}'/d' | sed -ne '/ Z/,$ p' >> ${SD_PATH}/plr.gcode
#tac /tmp/plrtmpA.$$ | sed -e '/ Z'${1}'[^0-9]*$/q' | tac | tail -n+2 | sed -ne '/ Z/,$ p' >> ${SD_PATH}/plr.gcode

# show the plr.gcode file size
echo $(stat -c %s ${SD_PATH}/plr.gcode)

echo "date6: $(date +"%Y-%m-%d %H:%M:%S")"
#rm ~/plrtmpA.$$
#echo "date7: $(date +"%Y-%m-%d %H:%M:%S")"
sync
sleep 10
#echo "date8: $(date +"%Y-%m-%d %H:%M:%S")"
#curl -X POST http://127.0.0.1/printer/gcode/script?script=SDCARD_PRINT_FILE%20FILENAME=plr.gcode
echo "date9: $(date +"%Y-%m-%d %H:%M:%S")"