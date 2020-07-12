Bluetooth A2DP/AVRCP Apple Accessory Protocol Bridge for BMW 6FL option (no idrive/nav/etc). 

Hardware:
* RN52 Breakout board from Sparkfun. 
* 30 pin iPod connector Breakout board from Elabguy. 
* Adafruit itsybitsy M4 express from Aadafruit. 

Itsybitsy communicates to both the RN52 and Car iPod interface via UART/Serial. 
GPIO2 on RN52 monitored by Itsybitsy for changes. 
GPIO9 on RN52 used to put RN52 into cmd mode by IstyBitsy. Could just ground it as well. 
Audio passed directly from RN52 to ipod board. 

Hookup:
* ItsyBitsy A4 <-> RN52 UART RX
* ItsyBitsy A5 <-> RN52 UART TX
* ItsyBitsy 7  <-> RN52 GPIO 2
* ItsyBitsy 13 <-> RN52 GPIO 9
* ItsyBitsy G  <-> RN52 Ground. 
* ItsyBitsy 3v <-> RN52 3v. + RN52 Pwr_En
* ItsyBitsy 3v <-> iPodBreakout 18. 3.3v
* ItsyBitsy TX <-> iPodBreakout 12. TX
* ItsyBitsy RX <-> iPodBreakout 13. RX
* ItsyBitsy G  <-> iPodBreakout 1. GND 11. SGND, 15. GND, 16. UGND
* ItsyBitsy USB<-> iPodBreakout 23. +5v
* RN52 SPK_L- <-> ipodBreakout 2. VGND
* RN52 SPK_L+ <-> iPodBreakout 4. LOL+   
* RN62 SPK_R+ <-> ipodBreakout 3. LOR+ 

Known issues:
Some charaters not displayed correctly on the display in the car. Encoding issue? Unlikely to spend much or anytime trying to fix. 
